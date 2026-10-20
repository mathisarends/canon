import asyncio
import importlib
import importlib.util
import runpy
import shutil
import subprocess
import sys
import tempfile
from collections.abc import AsyncIterator
from importlib.metadata import version
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict
from starlette.websockets import WebSocketDisconnect

MODULES = {
    "fastapi-canon": "fastapi_canon",
    "fastapi-streams": "fastapi_streams",
    "fastapi-rpckit": "fastapi_rpckit",
    "fastapi-webrtc": "fastapi_webrtc",
}
STACK = {"fastapi-canon", "fastapi-streams", "fastapi-rpckit"}


class Event(BaseModel):
    type: Literal["ready"] = "ready"
    value: int = 1


class SocketInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: int


class SocketOutput(BaseModel):
    value: int


def main() -> None:
    selected = set(sys.argv[1:])
    assert importlib.util.find_spec("rpckit") is None
    assert importlib.util.find_spec("fastapi_wsrpc") is None
    for name, module in MODULES.items():
        if name in selected:
            installed = importlib.import_module(module)
            assert Path(installed.__file__).resolve().is_relative_to(Path(sys.prefix))
            if hasattr(installed, "__version__"):
                assert installed.__version__ == version(name)
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
    if "fastapi-rpckit" in selected:
        from fastapi_rpckit import (
            Inject,
            RpcChannel,
            RpcService,
            RpcSocket,
            create_router,
        )

        channel = RpcChannel("health")

        @channel.method("ping")
        async def ping() -> str:
            return "pong"

        rpc = RpcService()
        rpc.socket("/rpc", channels=(channel,))

        @channel.socket("messages")
        async def messages(message: SocketInput) -> SocketOutput:
            return SocketOutput(value=message.value + 1)

        rpc.socket("/messages", messages)

        @channel.socket("session")
        async def session(socket: Inject[RpcSocket[SocketInput, SocketOutput]]) -> None:
            await socket.send(SocketOutput(value=0))
            async for message in socket:
                await socket.send(SocketOutput(value=message.value + 1))

        rpc.socket("/session", session)
        routers.append(create_router(rpc))
        _cli("fastapi-rpckit")
    if "fastapi-webrtc" in selected:
        engine = _RecordingEngine()
        routers.append(_webrtc_router(engine, canon="fastapi-canon" in selected))
        _cli("fastapi-webrtc")
    if "fastapi-canon" in selected:
        from fastapi_canon import Composition, ErrorOptions, Feature

        app = Composition(
            Feature(name="installed", routers=routers),
            errors=ErrorOptions(type_base="https://example.test/problems"),
        ).apply(app)
    else:
        for router in routers:
            app.include_router(router)
    with TestClient(app) as client:
        if "fastapi-canon" in selected:
            assert client.get("/health").json() == {"status": "ok"}
        if "fastapi-streams" in selected:
            assert '"type":"ready"' in client.get("/events").text
        if "fastapi-rpckit" in selected:
            with client.websocket_connect("/rpc") as websocket:
                websocket.send_json(
                    {"jsonrpc": "2.0", "id": 1, "method": "health.ping"}
                )
                assert websocket.receive_json()["result"] == "pong"
            with client.websocket_connect("/messages") as websocket:
                websocket.send_json({"value": 41})
                assert websocket.receive_json() == {"value": 42}
                websocket.send_json({"value": "secret"})
                try:
                    websocket.receive_json()
                except WebSocketDisconnect as error:
                    assert error.code == 1002
                    assert "secret" not in error.reason
                else:
                    raise AssertionError("Typed socket accepted an invalid message")
            with client.websocket_connect("/session") as websocket:
                assert websocket.receive_json() == {"value": 0}
                websocket.send_json({"value": 41})
                assert websocket.receive_json() == {"value": 42}
        if "fastapi-webrtc" in selected:
            _webrtc_sessions(client, engine, canon="fastapi-canon" in selected)
    assert app.openapi()["openapi"]
    if "fastapi-webrtc" in selected:
        _webrtc_codegen(app)
    if "fastapi-rpckit" in selected and importlib.util.find_spec("jinja2"):
        _rpc_codegen(rpc)
    if selected == STACK:
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


class _RecordingEngine:
    """Counts peers; admission must reject sessions before reaching it."""

    def __init__(self) -> None:
        from fastapi_webrtc import EngineCapabilities

        self.capabilities = EngineCapabilities(
            trickle_ice=True, ice_restart=False, renegotiation=False
        )
        self.created = 0

    def track_kind(self, track):
        raise TypeError("No local tracks in the installed-artifact check")

    async def create_peer(self, config, observer):
        self.created += 1
        raise RuntimeError("The smoke engine allocates no peers")


def _webrtc_router(engine, *, canon=False):
    from fastapi import HTTPException, Query
    from fastapi_webrtc import DataChannelSpec, Session, WebRtcRouter

    class AdmissionDenied(Exception):
        pass

    declarations = {}
    if canon:
        from fastapi_canon import Error, ErrorRegistry
        from fastapi_canon.integrations.webrtc import CanonWebRtcRouter

        denied = Error(
            AdmissionDenied,
            status=403,
            code="admission_denied",
            title="Denied",
            type="https://example.test/problems/admission_denied",
        )
        rtc = CanonWebRtcRouter(
            engine=engine, prefix="/rtc", error_registry=ErrorRegistry(errors=[denied])
        )
        declarations["raises"] = [denied]
    else:
        rtc = WebRtcRouter(engine=engine, prefix="/rtc")

    @rtc.session(
        "/rooms/{room}",
        data_channels=(DataChannelSpec(name="events", send_model=SocketOutput),),
        **declarations,
    )
    def room(room: str, token: str = Query()) -> Session:
        if token != "ok":
            if canon:
                raise AdmissionDenied()
            raise HTTPException(status_code=403)
        return Session()

    return rtc


def _webrtc_sessions(client, engine, *, canon=False) -> None:
    from fastapi_webrtc import SUBPROTOCOL
    from starlette.testclient import WebSocketDenialResponse

    try:
        with client.websocket_connect("/rtc/rooms/a?token=no", [SUBPROTOCOL]):
            raise AssertionError("A denied session was accepted")
    except WebSocketDenialResponse as error:
        assert error.status_code == 403
        if canon:
            assert error.json()["code"] == "admission_denied"
    assert engine.created == 0
    with client.websocket_connect("/rtc/rooms/a?token=ok", [SUBPROTOCOL]) as socket:
        try:
            socket.receive_text()
        except WebSocketDisconnect as error:
            assert (error.code, error.reason) == (1011, "engine_failure")
        else:
            raise AssertionError("Expected an engine_failure close")
    assert engine.created == 1
    if importlib.util.find_spec("aiortc") is None:
        try:
            importlib.import_module("fastapi_webrtc.engines.aiortc")
        except ImportError as error:
            assert "fastapi-webrtc[aiortc]" in str(error)
        else:
            raise AssertionError("The aiortc engine imported without aiortc")
    else:
        from fastapi_webrtc.engines.aiortc import AiortcEngine

        assert AiortcEngine().capabilities.renegotiation


def _webrtc_codegen(app) -> None:
    from fastapi_webrtc.codegen.typescript import generate_typescript
    from fastapi_webrtc.codegen.writer import write_files
    from fastapi_webrtc.contract import build_contract

    contract = build_contract(app)
    (session,) = contract["sessions"]
    assert session["path"] == "/rtc/rooms/{room}"
    files = generate_typescript(contract)
    assert "export class RtcClient {" in files["client.ts"]
    assert "readonly room: SessionApi<" in files["client.ts"]
    with tempfile.TemporaryDirectory(prefix="canon-webrtc-client-") as temporary:
        output = Path(temporary) / "client"
        assert write_files(output, files)
        assert not write_files(output, files, check=True)


def _rpc_codegen(rpc) -> None:
    from fastapi_rpckit.codegen import (
        PythonClientOptions,
        TypeScriptClientOptions,
        generate_python_client,
        generate_typescript_client,
    )
    from fastapi_rpckit.testing import InMemorySocketFactory

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
                    generated.HealthClient.connect(
                        socket_factory=factory, socket_connection_factory=factory
                    ) as client,
                ):
                    assert await client.health.ping() == "pong"
                    async with client.health.messages() as socket:
                        await socket.send(generated.SocketInput(value=41))
                        result = await socket.receive()
                        assert isinstance(result, generated.SocketOutput)
                        assert result.value == 42
                    async with client.health.session() as socket:
                        assert (await socket.receive()).value == 0
                        await socket.send(generated.SocketInput(value=41))
                        assert (await socket.receive()).value == 42

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
