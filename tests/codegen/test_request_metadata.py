import asyncio
import importlib
import subprocess
import sys
from contextlib import asynccontextmanager
from copy import deepcopy

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from pydantic import TypeAdapter

from rpckit import Inject, RpcChannel, RpcConnectedClient, RpcService
from rpckit.codegen import generate_python_client
from rpckit.codegen.python import PythonClientOptions
from rpckit.integrations.opentelemetry import (
    OpenTelemetry,
    _remote_context,
    trace_metadata,
)
from rpckit.testing import InMemorySocketFactory

from . import test_client_methods
from .conftest import document as document
from .test_connect import client_module as client_module
from .test_reconnect import Transport
from .test_reconnect import pool_runtime as pool_runtime

reverse_module = test_client_methods.client_module


class InjectMetadata:
    @asynccontextmanager
    async def request(self, call):
        call.metadata.update(trace_metadata())
        yield


@pytest.mark.parametrize("cancelled", [False, True])
async def test_reverse_metadata_is_reset_on_failure_and_cancellation(
    reverse_module, cancelled
):
    class Handler(reverse_module.RoomHandler):
        async def ping(self):
            assert (
                reverse_module.current_client_method_metadata()["traceparent"]
                == "context"
            )
            if cancelled:
                raise asyncio.CancelledError("stop")
            raise RuntimeError("application failure")

    dispatcher = reverse_module.handler_dispatcher(Handler())
    message = {
        "jsonrpc": "2.0",
        "id": "r",
        "method": "room.ping",
        "meta": {"traceparent": "context"},
    }
    if cancelled:
        with pytest.raises(asyncio.CancelledError, match="stop"):
            await dispatcher.respond(message)
    else:
        assert (await dispatcher.respond(message))["error"]["code"] == -32603
    assert reverse_module.current_client_method_metadata() is None


async def test_python_middleware_injects_active_trace_into_real_no_params_call(
    client_module,
):
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    channel = RpcChannel("trace")

    @channel.method()
    async def ping() -> str:
        return "pong"

    service = RpcService(
        middleware=[OpenTelemetry(tracer_provider=provider, metrics=False)]
    )
    service.socket("/rpc", channels=[channel])
    runtime = importlib.import_module(f"{client_module.__name__}.internal")
    async with (
        InMemorySocketFactory(service) as factory,
        client_module.GreetingClient.connect(
            socket_factory=factory, lazy=True, middleware=[InjectMetadata()]
        ) as client,
    ):
        with provider.get_tracer("test").start_as_current_span("caller") as caller:
            route = runtime.RpcRouteInfo(
                method="trace.ping",
                server="primary",
                result_adapter=TypeAdapter(str),
            )
            assert await client._rpc.request(route) == "pong"
            assert trace.get_current_span() is caller
    span = next(
        item for item in exporter.get_finished_spans() if item.name == "trace.ping"
    )
    assert span.parent.is_remote
    assert span.parent.span_id == caller.get_span_context().span_id
    assert all(task.done() for task in factory._tasks)
    provider.shutdown()


@pytest.mark.parametrize(
    "metadata", [{"other": "x"}, {"baggage": "x" * 4096}, {"traceparent": 42}]
)
async def test_bad_client_metadata_is_observed_and_never_sent_or_retried(
    pool_runtime, metadata
):
    seen, sent = [], []

    class Middleware:
        @asynccontextmanager
        async def request(self, call):
            call.metadata.update(metadata)
            try:
                yield
            finally:
                seen.append(call.outcome.error)

    class Adapter(Transport):
        async def request(self, method, params=None, **options):
            sent.append(method)

    core = pool_runtime.RpcClientCore(
        Adapter(), middleware=[Middleware()], supports_metadata=True, retry_attempts=2
    )
    with pytest.raises(ValueError) as raised:
        await core.request(pool_runtime.RpcRouteInfo("ping", TypeAdapter(str)))
    assert seen == [raised.value] and not sent
    await core.close()


async def test_contract_capability_and_current_transport_typing(
    document, tmp_path, pool_runtime
):
    old = deepcopy(document)
    old.pop("x-rpc-request-metadata")
    generate_python_client(old, tmp_path / "old", PythonClientOptions(package="old"))
    assert "supports_metadata=False" in (tmp_path / "old/client.py").read_text()
    consumer = tmp_path / "adapter_types.py"
    consumer.write_text(
        """
from collections.abc import AsyncIterator, Mapping
from typing import Any
from old import RpcTransport
from old.internal import RpcClientCore

class Adapter:
    async def request(self, method: str, params: dict[str, Any] | None = None,
                      *, metadata: Mapping[str, str] | None = None) -> Any:
        return None
    async def notifications(self) -> AsyncIterator[dict[str, Any]]:
        yield {}
    async def close(self) -> None:
        pass

transport: RpcTransport = Adapter()
client = RpcClientCore(transport)
""",
        encoding="utf-8",
    )
    checked = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyright",
            "--pythonpath",
            sys.executable,
            "--pythonversion",
            "3.12",
            str(consumer),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert checked.returncode == 0, checked.stdout + checked.stderr

    class Inject:
        @asynccontextmanager
        async def request(self, call):
            call.metadata["traceparent"] = "invalid"
            yield

    adapter = Transport()
    core = pool_runtime.RpcClientCore(adapter, middleware=[Inject()])
    with pytest.raises(ValueError, match="contract does not support"):
        await core.request(pool_runtime.RpcRouteInfo("ping", TypeAdapter(str)))
    await core.close()
    core = pool_runtime.RpcClientCore(Transport())
    assert (
        await core.request(pool_runtime.RpcRouteInfo("ping", TypeAdapter(str))) == "ok"
    )
    await core.close()


async def test_subscription_controls_each_carry_middleware_metadata(pool_runtime):
    sent = []

    class Inject:
        @asynccontextmanager
        async def request(self, call):
            call.metadata["traceparent"] = "context"
            yield

    class Adapter(Transport):
        async def request(self, method, params=None, *, metadata=None):
            sent.append((method, metadata))
            if method.endswith(".subscribe"):
                return {"subscriptionId": "one"}
            return None

        async def notifications(self):
            yield {
                "jsonrpc": "2.0",
                "method": "updates",
                "params": {"subscriptionId": "one", "payload": "ready"},
            }
            await asyncio.Event().wait()

    core = pool_runtime.RpcClientCore(
        Adapter(), middleware=[Inject()], supports_metadata=True
    )
    notification = pool_runtime.RpcNotificationInfo(
        "updates", TypeAdapter(dict), TypeAdapter(str)
    )
    stream = core.subscribe_remote(notification)
    assert await anext(stream) == "ready"
    await stream.aclose()
    assert sent == [
        ("updates.subscribe", {"traceparent": "context"}),
        ("updates.unsubscribe", {"traceparent": "context"}),
    ]
    await core.close()


async def test_reverse_calls_propagate_server_context_and_detach_handler_metadata(
    tmp_path,
):
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("test")
    channel = RpcChannel("demo")

    ping = channel.client.method("ping", result=str)

    @channel.server.method()
    async def trigger(client: Inject[RpcConnectedClient]) -> str:
        return await client.call(ping, metadata=trace_metadata())

    service = RpcService(
        middleware=[OpenTelemetry(tracer_provider=provider, metrics=False)]
    )
    service.socket("/rpc", channels=[channel], name="rpc")
    package = "traced_reverse_client"
    generate_python_client(
        service.contract(title="Trace", base_url="ws://test").to_openrpc(),
        tmp_path / package,
        PythonClientOptions(
            package=package, client_name="Client", with_transport="websocket"
        ),
    )
    sys.path.insert(0, str(tmp_path))
    try:
        module = importlib.import_module(package)
        from opentelemetry import context

        class Handler(module.DemoHandler):
            async def ping(self):
                metadata = module.current_client_method_metadata()
                assert metadata is not None
                token = context.attach(_remote_context(metadata, False))
                try:
                    with tracer.start_as_current_span("reverse handler"):
                        return "pong"
                finally:
                    context.detach(token)

        handler = Handler()
        async with (
            InMemorySocketFactory(service) as factory,
            module.Client.connect(socket_factory=factory, handlers=handler) as client,
        ):
            assert await client.demo.trigger() == "pong"
            assert module.current_client_method_metadata() is None
        dispatcher = module.handler_dispatcher(handler)
        bad = await dispatcher.respond(
            {"jsonrpc": "2.0", "id": "bad", "method": "demo.ping", "meta": None}
        )
        assert bad["error"]["code"] == -32600
        assert module.current_client_method_metadata() is None
        spans = {span.name: span for span in exporter.get_finished_spans()}
        assert (
            spans["reverse handler"].parent.span_id
            == spans["demo.trigger"].context.span_id
        )
        assert spans["reverse handler"].parent.is_remote
    finally:
        sys.path.remove(str(tmp_path))
        for name in list(sys.modules):
            if name == package or name.startswith(package + "."):
                del sys.modules[name]
        provider.shutdown()
