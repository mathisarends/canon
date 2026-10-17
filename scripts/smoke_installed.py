import importlib
import importlib.util
import runpy
import subprocess
import sys
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

MODULES = {
    "fastapi-canon": "fastapi_canon",
    "fastapi-streams": "fastapi_streams",
    "pyrpckit": "rpckit",
}


class Event(BaseModel):
    type: Literal["ready"] = "ready"
    value: int = 1


def main() -> None:
    selected = set(sys.argv[1:])
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
    if "pyrpckit" in selected:
        from rpckit import RpcChannel, RpcService
        from rpckit.integrations.fastapi import create_router

        channel = RpcChannel("health")

        @channel.method("ping")
        async def ping() -> str:
            return "pong"

        rpc = RpcService()
        rpc.socket("/rpc", channels=(channel,))
        routers.append(create_router(rpc))
        _cli("rpckit")
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
        if "pyrpckit" in selected:
            with client.websocket_connect("/rpc") as websocket:
                websocket.send_json(
                    {"jsonrpc": "2.0", "id": 1, "method": "health.ping"}
                )
                assert websocket.receive_json()["result"] == "pong"
    assert app.openapi()["openapi"]
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


if __name__ == "__main__":
    main()
