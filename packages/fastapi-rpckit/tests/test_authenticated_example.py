import time

import pytest
from fastapi.testclient import TestClient
from starlette.testclient import WebSocketDenialResponse
from starlette.websockets import WebSocketDisconnect

from examples.authenticated import Login, Sessions, create_app
from fastapi_rpckit import RpcService
from fastapi_rpckit.integrations.dishka import dishka_router


@pytest.mark.parametrize(
    ("headers", "status"),
    [({}, 403), ({"origin": "https://app.example.test"}, 401)],
)
def test_authentication_rejects_before_accept(headers, status):
    with TestClient(create_app()) as client:
        with (
            pytest.raises(WebSocketDenialResponse) as denied,
            client.websocket_connect("/rpc", headers=headers),
        ):
            pass
        assert denied.value.status_code == status


def test_authenticated_calls_and_expiry():
    app = create_app()
    with TestClient(app) as client:
        sessions = client.portal.call(app.state.dishka_container.get, Sessions)
        sessions.values["short"] = Login("grace", time.time() + 0.5)
        with client.websocket_connect(
            "/rpc",
            headers={"origin": "https://app.example.test", "cookie": "session=short"},
        ) as socket:
            socket.send_json({"jsonrpc": "2.0", "id": 1, "method": "account.whoami"})
            assert socket.receive_json()["result"] == "grace"
            with pytest.raises(WebSocketDisconnect) as closed:
                socket.receive_json()
            assert closed.value.code == 1008
            assert closed.value.reason == "credentials_expired"


def test_dishka_router_reports_context_factory_misuse():
    async def context():
        return object()

    with pytest.raises(TypeError, match="RpcRoutes"):
        dishka_router(RpcService(), context=context)
