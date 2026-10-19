import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from fastapi_rpckit import (
    Inject,
    ProtocolDefinitionError,
    RpcChannel,
    RpcConnectionClose,
    RpcService,
    RpcSocket,
)

from .test_socket_codecs import Byte, ByteCodec
from .test_typed_sockets import Ping, Pong
from .testing import RpcTestClient


class PublicReply(BaseModel):
    value: int


class InternalReply(PublicReply):
    internal_value: str


@pytest.mark.parametrize("as_model", [False, True])
async def test_outgoing_overrides_return_annotation_and_filters_output(
    as_model,
) -> None:
    channel = RpcChannel("models")

    @channel.socket(outgoing=PublicReply)
    async def reply(message: Ping) -> dict[str, Any] | InternalReply:
        values = {"value": message.value + 1, "internal_value": "private"}
        return InternalReply(**values) if as_model else values

    app = RpcService()
    app.socket("/reply", reply)
    document = app.contract(title="Models", base_url="ws://h").to_openrpc()
    schemas = document["components"]["schemas"]
    assert "PublicReply" in schemas and "InternalReply" not in schemas
    assert schemas["ModelsReplyServerMessage"] == {
        "$ref": "#/components/schemas/PublicReply"
    }
    async with RpcTestClient(app, "/reply") as client:
        await client.send_message('{"value":41}')
        assert await client.next_message() == '{"value":42}'


async def test_decorator_models_allow_unannotated_message_and_normal_return() -> None:
    channel = RpcChannel("models")
    received = []

    @channel.socket(incoming=Ping, outgoing=PublicReply)
    async def reply(message, multiplier: int):
        received.append(message)
        return {"value": message.value * multiplier}

    app = RpcService()
    app.socket("/reply/{multiplier}", reply)
    async with RpcTestClient(app, "/reply/2") as client:
        await client.send_message('{"value":21}')
        assert await client.next_message() == '{"value":42}'
        await client.send_message('{"value":"secret"}')
        assert await client.closed() == (
            RpcConnectionClose.PROTOCOL_ERROR,
            "Invalid incoming socket message",
        )
    assert len(received) == 1 and isinstance(received[0], Ping)


async def test_decorator_models_apply_to_dynamic_connection_handler() -> None:
    channel = RpcChannel("models")

    @channel.socket(incoming=Ping, outgoing=PublicReply)
    async def session(socket: Inject[RpcSocket[Any, Any]]) -> None:
        await socket.send({"value": 0})
        message = await socket.receive()
        assert isinstance(message, Ping)
        await socket.send({"value": message.value + 1})

    app = RpcService()
    app.socket("/session", session)
    async with RpcTestClient(app, "/session") as client:
        assert await client.next_message() == '{"value":0}'
        await client.send_message('{"value":41}')
        assert await client.next_message() == '{"value":42}'


async def test_connection_override_can_infer_the_other_direction() -> None:
    channel = RpcChannel("models")

    @channel.socket(outgoing=PublicReply)
    async def session(socket: Inject[RpcSocket[Ping, Any]]) -> None:
        message = await socket.receive()
        await socket.send({"value": message.value + 1})

    app = RpcService()
    app.socket("/session", session)
    async with RpcTestClient(app, "/session") as client:
        await client.send_message('{"value":41}')
        assert await client.next_message() == '{"value":42}'


async def test_explicit_incoming_can_infer_the_output_annotation() -> None:
    channel = RpcChannel("models")

    @channel.socket(incoming=Ping)
    async def reply(message: Any) -> PublicReply:
        assert isinstance(message, Ping)
        return PublicReply(value=message.value + 1)

    app = RpcService()
    app.socket("/reply", reply)
    async with RpcTestClient(app, "/reply") as client:
        await client.send_message('{"value":41}')
        assert await client.next_message() == '{"value":42}'


async def test_custom_codec_receives_resolved_decorator_models() -> None:
    channel = RpcChannel("models")

    @channel.socket(incoming=Byte, outgoing=Byte, codec=ByteCodec)
    async def increment(message: Any) -> int:
        return message + 1

    codec = channel.sockets[0].codec
    assert isinstance(codec, ByteCodec)
    assert codec.incoming_type is Byte and codec.outgoing_type is Byte
    app = RpcService()
    app.socket("/increment", increment)
    async with RpcTestClient(app, "/increment") as client:
        await client.send_message(b"\x29")
        assert await client.next_message() == b"\x2a"
        await client.send_message(b"\xff")
        assert await client.closed() == (
            RpcConnectionClose.INTERNAL_ERROR,
            "Invalid outgoing socket message",
        )


async def test_invalid_normal_return_uses_outgoing_validation() -> None:
    channel = RpcChannel("models")

    @channel.socket(outgoing=PublicReply)
    async def reply(message: Ping) -> dict[str, str]:
        return {"value": "secret"}

    app = RpcService()
    app.socket("/reply", reply)
    async with RpcTestClient(app, "/reply") as client:
        await client.send_message('{"value":41}')
        assert await client.closed() == (
            RpcConnectionClose.INTERNAL_ERROR,
            "Invalid outgoing socket message",
        )


async def test_explicit_none_is_a_null_schema_instead_of_inference() -> None:
    channel = RpcChannel("null")

    @channel.socket(incoming=None, outgoing=None)
    async def reply(message: None):
        assert message is None
        return None

    app = RpcService()
    app.socket("/null", reply)
    document = app.contract(title="Null", base_url="ws://h").to_openrpc()
    schemas = document["components"]["schemas"]
    assert schemas["NullReplyClientMessage"] == {"type": "null"}
    assert schemas["NullReplyServerMessage"] == {"type": "null"}
    async with RpcTestClient(app, "/null") as client:
        await client.send_message("null")
        assert await client.next_message() == "null"


def test_received_types_cannot_disagree_with_the_runtime_model() -> None:
    with pytest.raises(ProtocolDefinitionError, match="received annotation"):

        @RpcChannel("input").socket(incoming=Ping, outgoing=PublicReply)
        async def wrong(message: Pong): ...

    with pytest.raises(ProtocolDefinitionError, match="received annotation"):

        @RpcChannel("input").socket(incoming=Ping)
        async def wrong_socket(
            socket: Inject[RpcSocket[Pong, PublicReply]],
        ) -> None: ...

    with pytest.raises(ProtocolDefinitionError, match="sent annotation"):

        @RpcChannel("output").socket(outgoing=PublicReply)
        async def wrong_output(socket: Inject[RpcSocket[Ping, Pong]]) -> None: ...

    with pytest.raises(ProtocolDefinitionError, match=r"RpcSocket\[Received, Sent\]"):

        @RpcChannel("bare").socket(incoming=Ping, outgoing=PublicReply)
        async def bare(socket: Inject[RpcSocket]) -> None: ...


def test_explicit_message_schema_does_not_hide_missing_path_annotations() -> None:
    with pytest.raises(ProtocolDefinitionError, match="multiplier.*annotation"):

        @RpcChannel("paths").socket(incoming=Ping, outgoing=PublicReply)
        async def wrong(message, multiplier): ...


def test_decorator_override_types_preserve_implementation_type_checks(
    tmp_path: Path,
) -> None:
    source = tmp_path / "consumer.py"
    source.write_text(
        """
from typing import Any, assert_type
from pydantic import BaseModel
from fastapi_rpckit import Inject, RpcChannel, RpcSocket

class Ping(BaseModel):
    value: int
class Pong(BaseModel):
    value: int

channel = RpcChannel("overrides")

@channel.socket(outgoing=Pong)
async def reply(message: Ping) -> dict[str, int]:
    return {"value": message.value + 1}

@channel.socket(incoming=Ping, outgoing=Pong)
async def dynamic(socket: Inject[RpcSocket[Any, Any]]) -> None:
    assert_type(await socket.receive(), Any)
    await socket.send({"value": 1})

@channel.socket(outgoing=Pong)
async def typed_input(socket: Inject[RpcSocket[Ping, Any]]) -> None:
    assert_type(await socket.receive(), Ping)
    await socket.send({"value": 1})
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
    assert json.loads(result.stdout)["summary"]["errorCount"] == 0, result.stdout
