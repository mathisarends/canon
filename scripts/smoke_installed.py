import asyncio
import importlib
import importlib.util
import runpy
import shutil
import subprocess
import sys
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

MODULES = {
    "fastapi-canon": "fastapi_canon",
    "fastapi-streams": "fastapi_streams",
    "fastapi-wsrpc": "fastapi_wsrpc",
}


class Event(BaseModel):
    type: Literal["ready"] = "ready"
    value: int = 1


def main() -> None:
    selected = set(sys.argv[1:])
    assert importlib.util.find_spec("rpckit") is None
    for name, module in MODULES.items():
        if name in selected:
            installed = importlib.import_module(module)
            assert Path(installed.__file__).resolve().is_relative_to(Path(sys.prefix))
        else:
            assert importlib.util.find_spec(module) is None, module
    app = FastAPI()
    routers = []
    if "fastapi-canon" in selected:
        from fastapi_canon import CanonRouter

        http = CanonRouter()

        @http.get("/health")
        async def health() -> dict[str, str]:
            return {"status": "ok"}

        routers.append(http)
    if "fastapi-streams" in selected:
        from fastapi_streams import StreamRouter

        if "fastapi-canon" in selected:
            from fastapi_canon.integrations.streams import CanonStreamRouter

            streams = CanonStreamRouter()
        else:
            streams = StreamRouter()

        @streams.stream("/events", operation_id="events")
        async def events() -> AsyncIterator[Event]:
            yield Event()

        routers.append(streams)
        _cli("fastapi-streams")
    if "fastapi-wsrpc" in selected:
        from fastapi_wsrpc import RpcChannel, RpcService, create_router

        channel = RpcChannel("health")

        @channel.method("ping")
        async def ping() -> str:
            return "pong"

        rpc = RpcService()
        rpc.socket("/rpc", channels=(channel,))
        routers.append(create_router(rpc))
        _cli("fastapi-wsrpc")
    if "fastapi-canon" in selected:
        from fastapi_canon import Composition, Feature

        app = Composition(Feature(name="installed", routers=routers)).apply(app)
    else:
        for router in routers:
            app.include_router(router)
    with TestClient(app) as client:
        if "fastapi-canon" in selected:
            assert client.get("/health").json() == {"status": "ok"}
        if "fastapi-streams" in selected:
            assert '"type":"ready"' in client.get("/events").text
        if "fastapi-wsrpc" in selected:
            with client.websocket_connect("/rpc") as websocket:
                websocket.send_json(
                    {"jsonrpc": "2.0", "id": 1, "method": "health.ping"}
                )
                assert websocket.receive_json()["result"] == "pong"
    assert app.openapi()["openapi"]
    if "fastapi-wsrpc" in selected and importlib.util.find_spec("jinja2"):
        _rpc_codegen(rpc)
    if selected == set(MODULES):
        # Run the same composition/lifecycle regression against installed wheels.

        example = runpy.run_path(
            str(Path(__file__).resolve().parents[1] / "examples/stack_service.py")
        )
        stack = example["create_app"]()
        with TestClient(stack) as client:
            assert client.post("/counter").json() == {"value": 1}
            assert '"value":1' in client.get("/counter/events").text
            with client.websocket_connect("/rpc") as websocket:
                websocket.send_json(
                    {"jsonrpc": "2.0", "id": 1, "method": "counter.increment"}
                )
                assert websocket.receive_json()["result"] == {"value": 2}
            counter = client.portal.call(
                stack.state.dishka_container.get, example["Counter"]
            )
        assert counter.closed
    print(f"Installed artifact checks passed: {', '.join(sorted(selected))}")


def _cli(name: str) -> None:
    executable = Path(sys.executable).with_name(
        f"{name}.exe" if sys.platform == "win32" else name
    )
    subprocess.run(
        [str(executable), "--help"], check=True, capture_output=True, timeout=30
    )


def _rpc_codegen(rpc) -> None:
    from fastapi_wsrpc.codegen import (
        PythonClientOptions,
        TypeScriptClientOptions,
        generate_python_client,
        generate_typescript_client,
    )
    from fastapi_wsrpc.testing import InMemorySocketFactory

    document = rpc.contract(title="Health", base_url="ws://test").to_openrpc()
    with tempfile.TemporaryDirectory(prefix="canon-rpc-client-") as temporary:
        working = Path(temporary)
        python_options = PythonClientOptions(
            package="health_client",
            client_name="HealthClient",
            with_transport="websocket",
        )
        typescript_options = TypeScriptClientOptions(with_transport="websocket")
        generate_python_client(document, working / "health_client", python_options)
        generate_typescript_client(document, working / "typescript", typescript_options)
        assert not generate_python_client(
            document, working / "health_client", python_options, check=True
        )
        assert not generate_typescript_client(
            document, working / "typescript", typescript_options, check=True
        )
        sys.path.insert(0, temporary)
        try:
            generated = importlib.import_module("health_client")

            async def consume() -> None:
                async with (
                    InMemorySocketFactory(rpc) as factory,
                    generated.HealthClient.connect(socket_factory=factory) as client,
                ):
                    assert await client.health.ping() == "pong"

            asyncio.run(consume())
        finally:
            sys.path.remove(temporary)
        node = shutil.which("node")
        compiler = (
            Path(__file__).resolve().parents[1]
            / "packages/fastapi-streams/node_modules/typescript/bin/tsc"
        )
        assert node and compiler.is_file(), "Run npm ci for the Streams member first"
        subprocess.run(
            [
                node,
                str(compiler),
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
                "typescript/index.ts",
            ],
            cwd=working,
            check=True,
            timeout=30,
        )


if __name__ == "__main__":
    main()
