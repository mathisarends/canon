import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from fastapi_rpckit import RpcService
from fastapi_rpckit.codegen import (
    PythonClientOptions,
    TypeScriptClientOptions,
    generate_python_client,
    generate_typescript_client,
)
from fastapi_rpckit.codegen.bindings import SocketBinding
from fastapi_rpckit.codegen.ir import UnsupportedSchemaError, build_ir

from ..test_socket_codecs import increment, reply, session
from .test_bindings import EchoBinding
from .test_socket_roundtrip import LoopbackSocket, UnusedTransport

PYTHON_SESSION = """
from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from ..sockets import Socket


class Counter:
    def __init__(self, socket: Socket) -> None:
        self.socket = socket

    async def call(self, value: int) -> int:
        await self.socket.send(bytes([value]))
        result = await self.socket.receive()
        assert isinstance(result, bytes)
        return result[0]


@asynccontextmanager
async def open_counter(
    socket: AbstractAsyncContextManager[Socket],
) -> AsyncIterator[Counter]:
    async with socket as opened:
        yield Counter(opened)
"""

TYPESCRIPT_SESSION = """
import type { Socket } from "../sockets";

export class Counter {
  constructor(readonly socket: Socket) {}

  async call(value: number): Promise<number> {
    await this.socket.send(new Uint8Array([value]));
    const result = await this.socket.receive();
    if (!(result instanceof ArrayBuffer)) throw new TypeError("Expected bytes");
    return new Uint8Array(result)[0];
  }

  [Symbol.asyncDispose](): Promise<void> {
    return this.socket.close();
  }
}

export async function openCounter(socket: Socket): Promise<Counter> {
  return new Counter(socket);
}
"""


class CounterBinding:
    protocol = "counter"

    def bind(self, context):
        if context.language == "python":
            return SocketBinding("counter", PYTHON_SESSION, "open_counter", "Counter")
        return SocketBinding("counter", TYPESCRIPT_SESSION, "openCounter", "Counter")


def service() -> RpcService:
    app = RpcService()
    app.socket("/byte", increment)
    app.socket("/session", session)
    app.socket("/reply", reply)
    return app


@pytest.mark.parametrize("language", ["python", "typescript"])
@pytest.mark.parametrize(
    "codec_name,encoding", [("uint8", "uint8"), ("wrapped-json", "json")]
)
def test_unknown_codec_requires_a_binding_instead_of_assuming_json(
    language: str, codec_name: str, encoding: str, tmp_path: Path
) -> None:
    document = service().contract(title="Codec", base_url="ws://h").to_openrpc()
    document["x-rpckit-sockets"][0]["codec"] = {
        "name": codec_name,
        "encoding": encoding,
    }
    if encoding == "json":
        document["x-rpckit-sockets"][0]["messageTypes"] = ["text"]
        document["x-rpckit-sockets"][0]["x-rpckit-protocol"]["encoding"] = "json"
    generate = (
        generate_python_client if language == "python" else generate_typescript_client
    )
    with pytest.raises(UnsupportedSchemaError, match=codec_name + ".*protocol binding"):
        options = (
            PythonClientOptions(package="counter_client")
            if language == "python"
            else TypeScriptClientOptions()
        )
        generate(document, tmp_path / language, options)


@pytest.mark.parametrize(
    "metadata", [{}, {"name": "json"}, {"name": "json", "encoding": 1}]
)
def test_malformed_codec_metadata_is_rejected(metadata) -> None:
    document = service().contract(title="Codec", base_url="ws://h").to_openrpc()
    document["x-rpckit-sockets"][0]["codec"] = metadata
    with pytest.raises(UnsupportedSchemaError, match="codec metadata"):
        build_ir(document)


async def test_custom_binding_and_builtin_json_coexist_in_the_python_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = service()
    document = app.contract(title="Codec", base_url="ws://h").to_openrpc()
    package_name = "codec_client"
    generate_python_client(
        document,
        tmp_path / package_name,
        PythonClientOptions(
            package=package_name,
            bindings=(
                CounterBinding(),
                EchoBinding(protocol="json-session"),
            ),
        ),
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    try:
        package = importlib.import_module(package_name)

        async def opener(endpoint):
            return LoopbackSocket(package, urlsplit(endpoint.url).path, app)

        client = package.CodecClient.with_transports(
            UnusedTransport(), socket_opener=opener
        )
        async with client.binary.increment() as counter:
            assert await counter.call(41) == 42
        async with client.sessions.session() as wrapped:
            assert json.loads(await wrapped.socket.receive())["type"] == "ready"
            await wrapped.socket.send('{"value":41}')
            assert json.loads(await wrapped.socket.receive())["value"] == 41
            assert json.loads(await wrapped.socket.receive())["value"] == 42
        async with client.sessions.reply() as socket:
            await socket.send(package.Ping(value=41))
            assert (await socket.receive()).value == 42
    finally:
        for name in list(sys.modules):
            if name == package_name or name.startswith(package_name + "."):
                del sys.modules[name]


def test_custom_binding_and_json_clients_compile_together_in_typescript(
    tmp_path: Path,
) -> None:
    document = service().contract(title="Codec", base_url="ws://h").to_openrpc()
    document["servers"] = [
        {
            "name": "rpc",
            "url": "ws://h/rpc",
            "x-rpckit-transport": {"type": "websocket", "messageEncoding": "json"},
        }
    ]
    target = tmp_path / "typescript"
    generate_typescript_client(
        document,
        target,
        TypeScriptClientOptions(
            with_transport="websocket",
            bindings=(CounterBinding(), EchoBinding(protocol="json-session")),
        ),
    )
    npx = shutil.which("npx.cmd") or shutil.which("npx")
    if npx is None:
        pytest.skip("npx is required")
    result = subprocess.run(
        [
            npx,
            "--yes",
            "--package",
            "typescript",
            "tsc",
            "--strict",
            "--target",
            "ES2022",
            "--module",
            "ESNext",
            "--moduleResolution",
            "Bundler",
            "--lib",
            "ES2022,DOM,ESNext.Disposable",
            "--skipLibCheck",
            "--noEmit",
            str(target / "index.ts"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
