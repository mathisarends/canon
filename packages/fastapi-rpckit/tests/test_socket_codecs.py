import asyncio
import json
import subprocess
import sys
from functools import partial
from pathlib import Path
from typing import Annotated, Literal

import pytest
from pydantic import BaseModel, Field
from typing_extensions import TypeForm

from fastapi_rpckit import (
    Inject,
    ProtocolDefinitionError,
    RpcChannel,
    RpcConnectionClose,
    RpcJsonCodec,
    RpcMessageType,
    RpcService,
    RpcSocket,
    RpcSocketCodec,
    RpcSocketCodecError,
    RpcSocketMessage,
    RpcSocketProtocol,
)

from .test_typed_sockets import Ping, Pong
from .testing import RpcTestClient


class Ready(BaseModel):
    type: Literal["ready"] = "ready"


type Output = Pong | Ready
type SessionSocket = RpcSocket[Ping, Output]

channel = RpcChannel("sessions")


@channel.socket(protocol=RpcSocketProtocol("json-session"))
async def session(socket: Inject[SessionSocket]) -> None:
    await socket.send(Ready())
    async for message in socket:
        await socket.send(Pong(value=message.value))
        await socket.send(Pong(value=message.value + 1))


@channel.socket()
async def reply(message: Ping) -> Output:
    return Pong(value=message.value + 1)


def service() -> RpcService:
    app = RpcService()
    app.socket("/session", session)
    app.socket("/reply", reply)
    return app


async def test_connection_codec_supports_unsolicited_and_multiple_messages() -> None:
    async with RpcTestClient(service(), "/session") as client:
        assert await client.next_message() == '{"type":"ready"}'
        await client.send_message('{"value":4}')
        assert json.loads(await client.next_message())["value"] == 4
        assert json.loads(await client.next_message())["value"] == 5
        await client.send_message('{"value":"secret"}')
        assert await client.closed() == (
            RpcConnectionClose.PROTOCOL_ERROR,
            "Invalid incoming socket message",
        )


async def test_both_handler_styles_infer_codecs_from_their_annotations() -> None:
    for definition in channel.sockets:
        assert isinstance(definition.codec, RpcJsonCodec)
        assert definition.codec.incoming_type is Ping
        assert definition.codec.outgoing_type is Output
    async with RpcTestClient(service(), "/reply") as client:
        await client.send_message('{"value":4}')
        assert json.loads(await client.next_message())["value"] == 5


async def test_connection_codec_revalidates_output_and_cancels_on_disconnect() -> None:
    released = asyncio.Event()
    app = RpcService()
    local = RpcChannel("invalid")

    @local.socket()
    async def invalid(socket: Inject[RpcSocket[Ping, Pong]]) -> None:
        try:
            output = Pong(value=1)
            output.value = "secret"  # type: ignore[assignment]
            await socket.send(output)
        finally:
            released.set()

    app.socket("/invalid", invalid)
    async with RpcTestClient(app, "/invalid") as client:
        assert await client.closed() == (
            RpcConnectionClose.INTERNAL_ERROR,
            "Invalid outgoing socket message",
        )
        await asyncio.wait_for(released.wait(), 1)


type Byte = Annotated[int, Field(ge=0, le=255)]


class ByteCodec(RpcSocketCodec[int, int]):
    def __init__(self, *, incoming: TypeForm[int], outgoing: TypeForm[int]) -> None:
        super().__init__(
            incoming=incoming,
            outgoing=outgoing,
            name="uint8",
            encoding="uint8",
            messages=(RpcMessageType.BINARY,),
        )

    def decode(self, message: RpcSocketMessage) -> int:
        if not isinstance(message, bytes) or len(message) != 1:
            raise RpcSocketCodecError("secret wire details")
        return self.incoming.validate_python(message[0], strict=True)

    def encode(self, message: int) -> bytes:
        return bytes([self.validate_outgoing(message)])


binary = RpcChannel("binary")


@binary.socket(codec=ByteCodec, protocol=RpcSocketProtocol("counter", encoding="uint8"))
async def increment(message: Byte) -> Byte:
    return message + 1


def binary_service() -> RpcService:
    app = RpcService()
    app.socket("/byte", increment)
    return app


async def test_custom_binary_codec_works_with_the_message_handler() -> None:
    async with RpcTestClient(binary_service(), "/byte") as client:
        await client.send_message(b"\x29")
        assert await client.next_message() == b"\x2a"


@pytest.mark.parametrize("frame", [b"", b"secret", "41"])
async def test_custom_codec_rejections_do_not_expose_wire_details(frame) -> None:
    async with RpcTestClient(binary_service(), "/byte") as client:
        await client.send_message(frame)
        code, reason = await client.closed()
        assert code == RpcConnectionClose.PROTOCOL_ERROR
        assert "secret" not in reason


async def test_custom_codec_output_uses_the_shared_output_validator() -> None:
    async with RpcTestClient(binary_service(), "/byte") as client:
        await client.send_message(b"\xff")
        assert await client.closed() == (
            RpcConnectionClose.INTERNAL_ERROR,
            "Invalid outgoing socket message",
        )


@pytest.mark.parametrize("frame", ["secret", object()])
async def test_codec_output_must_match_its_declared_frame_type(frame) -> None:
    class Broken(ByteCodec):
        def encode(self, message: Byte):
            return frame

    local = RpcChannel("broken")

    @local.socket(codec=Broken)
    async def handle(message: Byte) -> Byte:
        return message

    app = RpcService()
    app.socket("/broken", handle)
    async with RpcTestClient(app, "/broken") as client:
        await client.send_message(b"\x01")
        assert await client.closed() == (
            RpcConnectionClose.INTERNAL_ERROR,
            "Invalid outgoing socket message",
        )


async def test_decoder_implementation_failure_is_an_internal_error() -> None:
    class Broken(ByteCodec):
        def decode(self, message: RpcSocketMessage) -> Byte:
            raise RuntimeError("secret implementation details")

    local = RpcChannel("broken")

    @local.socket(codec=Broken)
    async def handle(message: Byte) -> Byte:
        raise AssertionError("A decoder failure must not reach the handler")

    app = RpcService()
    app.socket("/broken", handle)
    async with RpcTestClient(app, "/broken") as client:
        await client.send_message(b"\x01")
        assert await client.closed() == (
            RpcConnectionClose.INTERNAL_ERROR,
            "Internal error",
        )


def test_custom_codec_contract_keeps_its_wire_encoding_and_schemas() -> None:
    document = binary_service().contract(title="Byte", base_url="ws://h").to_openrpc()
    endpoint = document["x-rpckit-sockets"][0]
    assert endpoint["codec"] == {"name": "uint8", "encoding": "uint8"}
    assert endpoint["messageTypes"] == ["binary"]
    schemas = document["components"]["schemas"]
    assert schemas["Byte"] == {"type": "integer", "minimum": 0, "maximum": 255}


def test_codec_factories_cannot_override_resolved_types() -> None:
    def swapped(*, incoming, outgoing):
        return RpcJsonCodec(incoming=outgoing, outgoing=incoming)

    with pytest.raises(ProtocolDefinitionError, match="preserve the resolved"):

        @RpcChannel("mismatch").socket(codec=swapped)
        async def wrong(message: Ping) -> Pong: ...

    with pytest.raises(ProtocolDefinitionError, match="preserve the resolved"):

        @RpcChannel("swapped").socket(codec=swapped)
        async def wrong_socket(socket: Inject[RpcSocket[Ping, Pong]]) -> None: ...

    with pytest.raises(ProtocolDefinitionError, match=r"RpcSocket\[Received, Sent\]"):

        @RpcChannel("untyped").socket(codec=RpcJsonCodec)
        async def untyped(socket: Inject[RpcSocket]) -> None: ...

    with pytest.raises(ProtocolDefinitionError, match="class or factory"):
        RpcChannel("instance").socket(codec=RpcJsonCodec(incoming=Ping, outgoing=Pong))

    class CallableCodec(RpcJsonCodec[Ping, Pong]):
        def __call__(self, **kwargs):
            return self

    with pytest.raises(ProtocolDefinitionError, match="class or factory"):
        RpcChannel("callable").socket(codec=CallableCodec(incoming=Ping, outgoing=Pong))

    with pytest.raises(ProtocolDefinitionError, match="must return RpcSocketCodec"):

        @RpcChannel("invalid").socket(codec=lambda **kwargs: object())
        async def invalid(message: Ping) -> Pong: ...


async def test_configured_codec_factory_runs_once_from_handler_types() -> None:
    calls = []

    def factory(*, label, incoming, outgoing):
        calls.append((label, incoming, outgoing))
        return RpcJsonCodec(incoming=incoming, outgoing=outgoing)

    local = RpcChannel("factory")

    @local.socket(codec=partial(factory, label="configured"))
    async def handle(message: Ping) -> Pong:
        return Pong(value=message.value + 1)

    assert calls == [("configured", Ping, Pong)]
    app = RpcService()
    app.socket("/factory", handle)
    async with RpcTestClient(app, "/factory") as client:
        for value in (1, 2):
            await client.send_message(json.dumps({"value": value}))
            assert json.loads(await client.next_message())["value"] == value + 1
    assert calls == [("configured", Ping, Pong)]


def test_codec_typing_preserves_constructor_inference_and_socket_directions(
    tmp_path: Path,
) -> None:
    source = tmp_path / "consumer.py"
    source.write_text(
        """
from typing import assert_type
from pydantic import BaseModel
from typing_extensions import TypeForm
from fastapi_rpckit import (
    Inject, RpcChannel, RpcJsonCodec, RpcMessageType, RpcSocket,
    RpcSocketCodec, RpcSocketMessage,
)

class Ping(BaseModel):
    value: int
class Pong(BaseModel):
    text: str

codec = RpcJsonCodec(incoming=Ping, outgoing=Pong)
assert_type(codec, RpcJsonCodec[Ping, Pong])
assert_type(codec.decode('{"value":1}'), Ping)

@RpcChannel("messages").socket(codec=RpcJsonCodec)
async def session(socket: Inject[RpcSocket[Ping, Pong]]) -> None:
    assert_type(await socket.receive(), Ping)
    await socket.send(Pong(text="ok"))
    await socket.send(Ping(value=1))

async def raw(socket: RpcSocket) -> None:
    assert_type(await socket.receive(), str | bytes)

class Binary(RpcSocketCodec[int, int]):
    def __init__(self, *, incoming: TypeForm[int], outgoing: TypeForm[int]) -> None:
        super().__init__(incoming=incoming, outgoing=outgoing, name="binary",
                         encoding="binary", messages=(RpcMessageType.BINARY,))

    def decode(self, message: RpcSocketMessage) -> int:
        assert isinstance(message, bytes)
        return self.incoming.validate_python(message[0], strict=True)

    def encode(self, message: int) -> bytes:
        return bytes([self.validate_outgoing(message)])

@RpcChannel("binary").socket(codec=Binary)
async def binary(socket: Inject[RpcSocket[int, int]]) -> None:
    assert_type(await socket.receive(), int)
    await socket.send(1)
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyright",
            "--pythonpath",
            sys.executable,
            "--pythonversion",
            "3.12",
            "--outputjson",
            str(source),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    errors = [
        item
        for item in json.loads(result.stdout)["generalDiagnostics"]
        if item["severity"] == "error"
    ]
    assert len(errors) == 1, result.stdout
    assert errors[0]["rule"] == "reportArgumentType"
    assert "Ping" in errors[0]["message"] and "Pong" in errors[0]["message"]
