import importlib
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Annotated
from urllib.parse import urlsplit

import pytest
from pydantic import Field

from fastapi_rpckit import RpcChannel, RpcService, RpcSocketProtocol
from fastapi_rpckit.codegen import (
    PythonClientOptions,
    TypeScriptClientOptions,
    generate_python_client,
    generate_typescript_client,
)
from fastapi_rpckit.codegen.bindings import bind_sockets
from fastapi_rpckit.codegen.ir import UnsupportedSchemaError, build_ir

from ..test_typed_sockets import Ping, Pong
from .test_bindings import EchoBinding
from .test_socket_roundtrip import LoopbackSocket, UnusedTransport

channel = RpcChannel("messages")


@channel.socket(protocol=RpcSocketProtocol("example"))
async def union(
    message: Annotated[Ping | Pong, Field(discriminator="type")],
) -> Annotated[Ping | Pong, Field(discriminator="type")]:
    return message


app = RpcService()
app.socket("/union", union)


@pytest.mark.parametrize("api_root", [None, "messages"])
async def test_python_union_messages_round_trip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    api_root: str | None,
) -> None:
    document = app.contract(title="Union", base_url="ws://h").to_openrpc()
    package_name = "union_client"
    generate_python_client(
        document,
        tmp_path / package_name,
        PythonClientOptions(package=package_name, api_root=api_root),
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    try:
        package = importlib.import_module(package_name)

        async def opener(endpoint):
            return LoopbackSocket(package, urlsplit(endpoint.url).path, app)

        client = package.UnionClient.with_transports(
            UnusedTransport(), socket_opener=opener
        )
        namespace = client.messages if api_root is None else client
        async with namespace.union() as socket:
            await socket.send(package.Ping(value=3))
            result = await socket.receive()
            assert isinstance(result, package.Ping)
            assert result.value == 3
    finally:
        for name in list(sys.modules):
            if name == package_name or name.startswith(f"{package_name}."):
                del sys.modules[name]


def test_protocol_bindings_can_replace_the_builtin_json_client() -> None:
    document = app.contract(title="Union", base_url="ws://h").to_openrpc()
    result = bind_sockets(
        iter(build_ir(document).sockets), [EchoBinding(protocol="example")], "python"
    )
    assert result["example"].session == "EchoSession"


@pytest.mark.parametrize("messages", [{}, {"client": {}}, {"client": {}, "server": 1}])
def test_malformed_directional_contracts_are_rejected(messages) -> None:
    document = app.contract(title="Union", base_url="ws://h").to_openrpc()
    document["x-rpckit-sockets"][0]["messages"] = messages
    with pytest.raises(UnsupportedSchemaError, match="client/server"):
        build_ir(document)


@pytest.mark.parametrize("api_root", [None, "messages"])
def test_union_clients_pass_target_formatting_and_types(
    tmp_path: Path,
    api_root: str | None,
) -> None:
    document = app.contract(title="Union", base_url="ws://h").to_openrpc()
    python_root = tmp_path / "python_client"
    generate_python_client(
        document,
        python_root,
        PythonClientOptions(package="python_client", api_root=api_root),
    )
    for command in ("check", "format"):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ruff",
                command,
                *(["--check"] if command == "format" else []),
                str(python_root),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
    npx = shutil.which("npx.cmd") or shutil.which("npx")
    if npx is None:
        pytest.skip("npx is required")
    target = tmp_path / "typescript"
    document["servers"] = [
        {
            "name": "rpc",
            "url": "ws://h/rpc",
            "x-rpckit-transport": {"type": "websocket", "messageEncoding": "json"},
        }
    ]
    generate_typescript_client(
        document,
        target,
        TypeScriptClientOptions(api_root=api_root, with_transport="websocket"),
    )
    result = subprocess.run(
        [npx, "prettier", "--check", str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
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
