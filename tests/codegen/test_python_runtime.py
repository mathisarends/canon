import asyncio
import importlib
import json
import sys
from collections.abc import AsyncIterator, Iterator
from copy import deepcopy
from types import ModuleType
from typing import Any

import pytest
from pydantic import TypeAdapter

from rpckit.codegen import generate_python_client
from rpckit.codegen.python import PythonClientOptions


class StubTransport:
    def __init__(self, result: Any = None) -> None:
        self.result = result
        self.closed = 0

    async def request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return self.result

    async def notifications(self) -> AsyncIterator[dict[str, Any]]:
        if False:
            yield {}

    async def close(self) -> None:
        self.closed += 1


@pytest.fixture
def runtime(generated_client: ModuleType) -> ModuleType:
    return importlib.import_module(f"{generated_client.__name__}.internal")


async def test_client_core_wraps_response_validation_with_the_route(
    runtime: ModuleType,
) -> None:
    core = runtime.RpcClientCore(StubTransport("wrong"))
    route = runtime.RpcRouteInfo(
        method="math.count",
        result_adapter=TypeAdapter(int),
    )

    with pytest.raises(runtime.RpcResponseValidationError) as raised:
        await core.request(route)

    assert raised.value.method == "math.count"


async def test_client_core_closes_an_owned_transport_once(
    runtime: ModuleType,
) -> None:
    transport = StubTransport()
    core = runtime.RpcClientCore(transport)

    await core.close()
    await core.close()

    assert transport.closed == 1


def test_server_info_resolves_declared_variables(runtime: ModuleType) -> None:
    server = runtime.RpcServerInfo(
        name="control",
        url="wss://{host}/{sessionId}",
        variables={
            "host": runtime.RpcServerVariable("api.example.com"),
            "sessionId": runtime.RpcServerVariable("demo"),
        },
    )

    assert server.resolve({"sessionId": "s-123"}) == "wss://api.example.com/s-123"


def test_server_info_rejects_unknown_variables(runtime: ModuleType) -> None:
    server = runtime.RpcServerInfo(name="control", url="wss://example.com")

    with pytest.raises(ValueError, match="Unknown variables"):
        server.resolve({"token": "secret"})


async def test_binary_websocket_stream_sends_and_receives_raw_frames(
    document: dict[str, Any], tmp_path
) -> None:
    deployed = deepcopy(document)
    deployed["servers"] = [
        {
            "name": "control",
            "url": "wss://api/rpc",
            "x-rpckit-transport": {
                "type": "websocket",
                "messageEncoding": "json",
            },
        }
    ]
    deployed["x-rpckit-binary-streams"] = [
        {
            "name": "voice",
            "url": "wss://media/{sessionId}",
            "direction": "server-to-client",
            "contentType": "audio/pcm;rate=24000",
            "frameType": "binary",
            "variables": {"sessionId": {"default": "demo"}},
        }
    ]
    package = "voice_client"
    generate_python_client(
        deployed,
        tmp_path / package,
        PythonClientOptions(package=package, with_transport="websocket"),
    )
    sys.path.insert(0, str(tmp_path))

    class Socket:
        def __init__(self) -> None:
            self.sent: list[bytes] = []
            self.closed = False

        async def send(self, message: bytes) -> None:
            self.sent.append(message)

        async def recv(self) -> bytes:
            return b"assistant-pcm"

        async def close(self) -> None:
            self.closed = True

    socket = Socket()

    async def factory(
        url: str,
        *,
        subprotocols: list[str] | None,
        additional_headers: dict[str, str] | None,
    ):
        assert url == "wss://media/turn-1"
        assert subprotocols is None
        assert additional_headers is None
        return socket

    try:
        media = importlib.import_module(f"{package}.streams")
        endpoint = media.BinaryStreamEndpoint(
            name=media.BinaryStreamName.VOICE,
            url="wss://media/turn-1",
            content_type="audio/pcm;rate=24000",
        )
        stream = await media.BinaryWebSocketStream.open(
            endpoint, socket_factory=factory
        )

        assert await stream.receive() == b"assistant-pcm"
        await stream.close()

        assert socket.sent == []
        assert socket.closed is True
    finally:
        sys.path.remove(str(tmp_path))
        for name in [
            name
            for name in sys.modules
            if name == package or name.startswith(f"{package}.")
        ]:
            del sys.modules[name]


class ClosingTransport:
    """A transport whose notification stream ends right away."""

    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.closed = 0

    async def request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return None

    async def notifications(self) -> AsyncIterator[dict[str, Any]]:
        if self.error is not None:
            raise self.error
        if False:
            yield {}

    async def close(self) -> None:
        self.closed += 1


async def _drain(stream: AsyncIterator[dict[str, Any]]) -> list[dict[str, Any]]:
    return [message async for message in stream]


async def test_subscribing_after_the_pump_ended_stops_instead_of_hanging(
    runtime: ModuleType,
) -> None:
    core = runtime.RpcClientCore(ClosingTransport())

    assert await _drain(core.notifications("tasks.updated")) == []
    assert await _drain(core.notifications("tasks.updated")) == []


async def test_subscribing_after_the_pump_failed_reports_the_failure(
    runtime: ModuleType,
) -> None:
    core = runtime.RpcClientCore(ClosingTransport(RuntimeError("socket died")))

    with pytest.raises(runtime.RpcTransportError):
        await _drain(core.notifications("tasks.updated"))
    with pytest.raises(runtime.RpcTransportError):
        await _drain(core.notifications("tasks.updated"))


@pytest.fixture(scope="module")
def websocket_runtime(document, tmp_path_factory) -> Iterator[ModuleType]:
    root = tmp_path_factory.mktemp("websocket_runtime")
    package = "transport_runtime_client"
    deployed = deepcopy(document)
    deployed["servers"] = [
        {
            "name": "rpc",
            "url": "ws://test",
            "x-rpckit-transport": {"type": "websocket", "messageEncoding": "json"},
        }
    ]
    generate_python_client(
        deployed,
        root / package,
        PythonClientOptions(package=package, with_transport="websocket"),
    )
    sys.path.insert(0, str(root))
    try:
        yield importlib.import_module(package)
    finally:
        sys.path.remove(str(root))
        for name in list(sys.modules):
            if name == package or name.startswith(f"{package}."):
                del sys.modules[name]


class ControlledSocket:
    def __init__(self) -> None:
        self.inbox: asyncio.Queue[str] = asyncio.Queue()
        self.sent: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.send_gate = asyncio.Event()
        self.send_gate.set()
        self.closed = False

    async def send(self, message: str) -> None:
        self.sent.put_nowait(json.loads(message))
        await self.send_gate.wait()

    async def recv(self) -> str:
        return await self.inbox.get()

    async def close(self) -> None:
        self.closed = True

    def reply(self, request_id: int, **payload: Any) -> None:
        self.inbox.put_nowait(
            json.dumps({"jsonrpc": "2.0", "id": request_id, **payload})
        )


@pytest.mark.parametrize("abandon", ["timeout", "cancel"])
async def test_late_duplicate_and_unknown_responses_leave_other_calls_alive(
    websocket_runtime: ModuleType, abandon: str
) -> None:
    socket = ControlledSocket()
    transport = websocket_runtime.WebSocketTransport(socket, request_timeout=None)
    try:
        if abandon == "timeout":
            transport._request_timeout = 0
        abandoned = asyncio.create_task(transport.request("slow"))
        first = await socket.sent.get()
        if abandon == "timeout":
            with pytest.raises(websocket_runtime.RpcTransportError, match="timed out"):
                await abandoned
            transport._request_timeout = None
        else:
            abandoned.cancel()
            with pytest.raises(asyncio.CancelledError):
                await abandoned
        assert not transport._pending

        other = asyncio.create_task(transport.request("fast"))
        second = await socket.sent.get()
        socket.reply(first["id"], result="late")
        socket.reply(123456, error={"code": -32601, "message": "unknown"})
        socket.reply(second["id"], result="ok")
        socket.reply(second["id"], result="duplicate")
        assert await other == "ok"
        last = asyncio.create_task(transport.request("later"))
        third = await socket.sent.get()
        socket.reply(third["id"], result="still connected")
        assert await last == "still connected"
        assert not transport.closed.done()
    finally:
        await transport.close()
    assert not transport._pending
    assert transport._reader.done()


async def test_late_response_from_a_served_endpoint_keeps_the_client_usable(
    websocket_runtime: ModuleType,
) -> None:
    from rpckit import RpcChannel, RpcService
    from rpckit.testing import InMemorySocketFactory

    channel = RpcChannel("resilience")
    entered, release = asyncio.Event(), asyncio.Event()

    @channel.method
    async def slow() -> str:
        entered.set()
        await release.wait()
        return "late"

    @channel.method
    async def fast() -> str:
        return "ok"

    service = RpcService()
    service.socket("/rpc", channels=[channel])

    def configure(socket, attempt):
        socket.server_to_client.hold()

    async with InMemorySocketFactory(service, configure=configure) as factory:
        transport = await websocket_runtime.WebSocketTransport.open(
            "ws://test/rpc", socket_factory=factory, request_timeout=0
        )
        try:
            with pytest.raises(websocket_runtime.RpcTransportError, match="timed out"):
                await transport.request("resilience.slow")
            await entered.wait()
            release.set()
            faults = factory.sockets[0].server_to_client
            await faults.held.wait()
            assert faults.held_count == 1
            faults.release()
            transport._request_timeout = None
            assert await transport.request("resilience.fast") == "ok"
            assert await transport.request("resilience.fast") == "ok"
            assert not transport.closed.done()
        finally:
            release.set()
            await transport.close()
    assert all(task.done() for task in factory._tasks)


@pytest.mark.parametrize(
    "payload",
    [
        {"id": "unknown", "result": 1},
        {"id": True, "result": 1},
        {"id": 999},
        {"id": 999, "result": 1, "error": {"code": -1, "message": "bad"}},
        {"id": 999, "error": "bad"},
        {"id": 999, "error": {"code": "bad", "message": "bad"}},
    ],
)
async def test_malformed_unknown_responses_still_fail_pending_calls(
    websocket_runtime: ModuleType, payload: dict[str, Any]
) -> None:
    socket = ControlledSocket()
    transport = websocket_runtime.WebSocketTransport(socket, request_timeout=None)
    pending = asyncio.create_task(transport.request("pending"))
    await socket.sent.get()
    socket.inbox.put_nowait(json.dumps({"jsonrpc": "2.0", **payload}))
    with pytest.raises(websocket_runtime.RpcTransportError):
        await pending
    assert isinstance(await transport.closed, websocket_runtime.RpcTransportError)
    assert not transport._pending


async def test_blocked_send_is_inside_request_timeout_and_retires_transport(
    websocket_runtime: ModuleType,
) -> None:
    socket = ControlledSocket()
    socket.send_gate.clear()
    transport = websocket_runtime.WebSocketTransport(socket, request_timeout=0)
    with pytest.raises(websocket_runtime.RpcTransportError, match="timed out"):
        async with asyncio.timeout(1):
            await transport.request("blocked")
    assert socket.closed
    assert not transport._pending
    assert transport._reader.done()
    assert isinstance(await transport.closed, websocket_runtime.RpcTransportError)


async def test_cancel_during_send_preserves_cancellation_and_retires_transport(
    websocket_runtime: ModuleType,
) -> None:
    socket = ControlledSocket()
    socket.send_gate.clear()
    transport = websocket_runtime.WebSocketTransport(socket, request_timeout=None)
    request = asyncio.create_task(transport.request("blocked"))
    await socket.sent.get()
    request.cancel()
    with pytest.raises(asyncio.CancelledError):
        await request
    assert socket.closed
    assert not transport._pending
    assert transport._reader.done()


async def test_deep_json_fails_all_client_calls_without_leaked_futures(
    websocket_runtime: ModuleType,
) -> None:
    socket = ControlledSocket()
    transport = websocket_runtime.WebSocketTransport(socket, request_timeout=None)
    calls = [asyncio.create_task(transport.request("pending")) for _ in range(2)]
    for _ in calls:
        await socket.sent.get()
    socket.inbox.put_nowait("[" * 100_000)
    outcomes = await asyncio.gather(*calls, return_exceptions=True)
    assert all(isinstance(e, websocket_runtime.RpcTransportError) for e in outcomes)
    assert isinstance(await transport.closed, websocket_runtime.RpcTransportError)
    assert not transport._pending
    assert transport._reader.done()
    assert socket.closed


async def test_static_transport_close_waits_for_all_and_finalizes_client(
    runtime: ModuleType,
) -> None:
    started, release = asyncio.Event(), asyncio.Event()

    class Failing(StubTransport):
        async def close(self) -> None:
            await started.wait()
            raise OSError("close failed")

    class Blocking(StubTransport):
        async def close(self) -> None:
            started.set()
            await release.wait()
            await super().close()

    blocking = Blocking()
    core = runtime.RpcClientCore({"first": Failing(), "second": blocking})
    closing = asyncio.create_task(core.close())
    await started.wait()
    release.set()
    await closing
    assert blocking.closed == 1
    assert core.closed.done()
    await core.close()
    assert blocking.closed == 1


async def test_static_transport_close_preserves_caller_cancellation(
    runtime: ModuleType,
) -> None:
    started, cancelled = asyncio.Event(), asyncio.Event()

    class Blocking(StubTransport):
        async def close(self) -> None:
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

    core = runtime.RpcClientCore({"first": Blocking(), "second": Blocking()})
    closing = asyncio.create_task(core.close())
    await started.wait()
    closing.cancel()
    with pytest.raises(asyncio.CancelledError):
        await closing
    assert cancelled.is_set()
    assert core.closed.done()
