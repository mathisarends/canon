import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from .conftest import document as document
from .test_connect import client_module as client_module
from .test_reconnect import Clock, Transport
from .test_reconnect import pool_runtime as pool_runtime


def recorder(events, calls, name, *, cleanup=None):
    class Middleware:
        @asynccontextmanager
        async def request(self, call):
            local = object()
            events.append((name, "enter"))
            calls.append(call)
            try:
                yield
            finally:
                assert local is not None
                assert call.outcome is not None
                events.append((name, "exit"))
                if cleanup is not None:
                    raise cleanup

    return Middleware()


def route(runtime, **options):
    return runtime.RpcRouteInfo(
        method="work", server="primary", result_adapter=TypeAdapter(str), **options
    )


@pytest.mark.parametrize(
    "failure", ["success", "remote", "transport", "validation", "acquisition"]
)
async def test_onion_outcomes_and_original_error(pool_runtime, failure):
    events, calls = [], []
    remote = pool_runtime.RpcRemoteError(-32000, "domain", "Domain failure")
    lost = pool_runtime.RpcConnectionLostError(sent=True)
    denied = pool_runtime.RpcConnectError("Denied", permanent=True)

    class Adapter(Transport):
        async def request(self, method, params=None):
            if failure == "remote":
                raise remote
            if failure == "transport":
                raise lost
            return 42 if failure == "validation" else "ok"

    transport = Adapter()

    async def acquire(server):
        if failure == "acquisition":
            raise denied
        return transport

    source = SimpleNamespace(get=acquire, close=transport.close)
    middleware = [recorder(events, calls, name) for name in ("outer", "inner")]
    core = pool_runtime.RpcClientCore(source, middleware=middleware)
    if failure == "success":
        assert await core.request(route(pool_runtime)) == "ok"
        assert calls[0].outcome.result == "ok"
        assert calls[0].outcome.error is None
    else:
        with pytest.raises(Exception) as raised:
            await core.request(route(pool_runtime))
        assert calls[0].outcome.error is raised.value
        if failure == "validation":
            assert isinstance(raised.value, pool_runtime.RpcResponseValidationError)
        else:
            assert (
                raised.value
                is {"remote": remote, "transport": lost, "acquisition": denied}[failure]
            )
    assert events == [
        ("outer", "enter"),
        ("inner", "enter"),
        ("inner", "exit"),
        ("outer", "exit"),
    ]
    assert calls[0] is calls[1]
    assert calls[0].attempt == 1 and calls[0].call_id
    assert calls[0].server == "primary"
    assert calls[0].transport is (None if failure == "acquisition" else transport)
    assert calls[0].duration >= 0
    await core.close()


async def test_retry_attempt_ids_and_legacy_hooks_remain_once_per_call(pool_runtime):
    events, calls, hooks = [], [], []
    sent = 0

    class Adapter(Transport):
        async def request(self, method, params=None):
            nonlocal sent
            sent += 1
            if sent == 1:
                raise pool_runtime.RpcConnectionLostError(sent=False)
            return "ok"

    class Hook:
        async def before_request(self, route, params):
            hooks.append("before")

        async def after_response(self, route, result):
            assert result == "ok"
            hooks.append("after")

    transport = Adapter()

    async def acquire(server):
        return transport

    source = SimpleNamespace(
        get=acquire, close=transport.close, retry_delay=lambda _: 0
    )
    core = pool_runtime.RpcClientCore(
        source,
        middleware=[recorder(events, calls, "metrics")],
        hooks=[Hook()],
        retry_attempts=1,
    )
    assert await core.request(route(pool_runtime)) == "ok"
    assert hooks == ["before", "after"]
    assert [call.attempt for call in calls] == [1, 2]
    assert calls[0].call_id == calls[1].call_id
    assert isinstance(calls[0].outcome.error, pool_runtime.RpcConnectionLostError)
    assert calls[1].outcome.result == "ok"
    await core.close()


@pytest.mark.parametrize("failure", [True, False])
async def test_cleanup_preserves_existing_error_and_cleanup_only_fault_never_retries(
    pool_runtime, failure, caplog
):
    events, calls = [], []
    original = pool_runtime.RpcConnectionLostError(sent=True)
    cleanup = pool_runtime.RpcConnectionLostError(sent=False)
    sent = 0

    class Adapter(Transport):
        async def request(self, method, params=None):
            nonlocal sent
            sent += 1
            if failure:
                raise original
            return "ok"

    core = pool_runtime.RpcClientCore(
        Adapter(),
        middleware=[
            recorder(events, calls, "outer"),
            recorder(events, calls, "inner", cleanup=cleanup),
        ],
        retry_attempts=2,
    )
    with pytest.raises(pool_runtime.RpcConnectionLostError) as raised:
        await core.request(route(pool_runtime))
    assert raised.value is (original if failure else cleanup)
    assert calls[0].outcome.error is raised.value
    assert calls[0].outcome.result is None
    assert sent == 1
    assert ("middleware cleanup failed" in caplog.text) == failure
    await core.close()


@pytest.mark.parametrize("timeout", [False, True])
async def test_cancel_and_overall_timeout_finalize_pending_acquisition(
    pool_runtime, monkeypatch, timeout
):
    before = asyncio.all_tasks()
    clock = Clock(monkeypatch, pool_runtime)
    entered = asyncio.Event()
    events, calls = [], []

    async def acquire(server):
        entered.set()
        await asyncio.Future()

    async def close():
        pass

    source = SimpleNamespace(get=acquire, close=close, request_timeout=5)
    core = pool_runtime.RpcClientCore(
        source, middleware=[recorder(events, calls, "metrics")]
    )
    task = asyncio.create_task(core.request(route(pool_runtime)))
    await entered.wait()
    if timeout:
        _, waiting = await clock.timers.get()
        waiting.reschedule(asyncio.get_running_loop().time())
        with pytest.raises(pool_runtime.RpcRequestTimeoutError) as raised:
            await task
    else:
        task.cancel("caller abort")
        with pytest.raises(asyncio.CancelledError, match="caller abort") as raised:
            await task
    assert calls[0].outcome.error is raised.value
    assert calls[0].transport is None
    await core.close()
    assert not asyncio.all_tasks() - before


async def test_mutated_params_revalidated_before_send(pool_runtime):
    class Params(BaseModel):
        value: int

    observed, sent = [], []

    class Middleware:
        @asynccontextmanager
        async def request(self, call):
            call.params = {"value": "invalid"}
            try:
                yield
            finally:
                observed.append(call.outcome)

    class Adapter(Transport):
        async def request(self, method, params=None):
            sent.append(params)
            return "ok"

    core = pool_runtime.RpcClientCore(Adapter(), middleware=[Middleware()])
    method = route(pool_runtime, params_adapter=TypeAdapter(Params))
    with pytest.raises(ValidationError) as raised:
        await core.request(method, params=Params(value=1))
    assert observed[0].error is raised.value
    assert not sent
    await core.close()


async def test_subscription_control_calls_have_scopes(pool_runtime):
    events, calls = [], []
    queue = asyncio.Queue()

    class Adapter(Transport):
        async def request(self, method, params=None):
            if method.endswith(".subscribe"):
                queue.put_nowait(
                    {
                        "jsonrpc": "2.0",
                        "method": "updates",
                        "params": {"subscriptionId": "s", "payload": {"value": 1}},
                    }
                )
                return {"subscriptionId": "s"}
            return None

        async def notifications(self):
            while True:
                yield await queue.get()

    core = pool_runtime.RpcClientCore(
        Adapter(), middleware=[recorder(events, calls, "metrics")]
    )
    notification = pool_runtime.RpcNotificationInfo(
        method="updates",
        message_adapter=TypeAdapter(dict[str, Any]),
        payload_adapter=TypeAdapter(dict[str, Any]),
    )
    stream = core.subscribe_remote(notification)
    assert await anext(stream) == {"value": 1}
    await stream.aclose()
    assert [call.route.method for call in calls] == [
        "updates.subscribe",
        "updates.unsubscribe",
    ]
    assert all(call.outcome.error is None for call in calls)
    assert all(call.transport is not None for call in calls)
    await core.close()


async def test_middleware_entry_failure_is_application_error_without_retry(
    pool_runtime, client_module
):
    events, calls = [], []
    error = pool_runtime.RpcConnectionLostError(sent=False)
    sent = []

    class Broken:
        @asynccontextmanager
        async def request(self, call):
            raise error
            yield

    class Adapter(Transport):
        async def request(self, method, params=None):
            sent.append(method)

    core = pool_runtime.RpcClientCore(
        Adapter(),
        middleware=[recorder(events, calls, "outer"), Broken()],
        retry_attempts=2,
    )
    with pytest.raises(pool_runtime.RpcConnectionLostError) as raised:
        await core.request(route(pool_runtime))
    assert raised.value is error
    assert calls[0].outcome.error is error
    assert not sent
    assert client_module.RpcClientCall is pool_runtime.RpcClientCall
    assert client_module.RpcClientCallOutcome is pool_runtime.RpcClientCallOutcome
    assert client_module.RpcClientMiddleware is pool_runtime.RpcClientMiddleware
    await core.close()
