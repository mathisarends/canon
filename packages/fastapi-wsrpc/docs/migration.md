# Migrate from pyrpckit to fastapi-wsrpc

The successor is developed inside Canon; the original repository remains
available. This source migration has not published a new PyPI release.

| Before | After |
| --- | --- |
| distribution `pyrpckit` | `fastapi-wsrpc` (initial unreleased version 0.1.0) |
| Python import `rpckit` | `fastapi_wsrpc` |
| CLI `rpckit` | `fastapi-wsrpc` |
| optional `[fastapi]` extra | FastAPI is required; remove the extra |
| logger `rpckit` | logger `fastapi_wsrpc` |

Use the wheel built by `uv build --package fastapi-wsrpc` before publication.
After publication the install will be `uv add fastapi-wsrpc`; retain `[codegen]`,
`[dishka]`, and `[otel]` only where needed. Update imports throughout application
code, codegen source modules, monkeypatch targets, and configuration.

The FastAPI mounting APIs are directly available:

```python
from fastapi_wsrpc import FastApiSocket, RpcRoutes, create_router, serve_websocket
```

The existing `fastapi_wsrpc.integrations.fastapi` paths also remain valid.
`RpcChannel`, `RpcService`, endpoint registration, and `Inject` retain their
behavior. With Canon, put `dishka_router(service)` in a feature's routers; it
uses Canon's application container, SESSION per connection, and REQUEST per call.
See the [workspace example](../../../examples/stack_service.py).

The JSON-RPC envelopes, method names, control frames, OpenRPC `x-rpckit-*`
extensions, binary/raw framing, and `.rpcgen` manifest format are deliberately
preserved, as are the `rpckit.*` OpenTelemetry metric and attribute names so
existing dashboards continue to work. Generated clients do not require server-package imports.
Regenerating clients updates their generator attribution; use the same
`rpcgen.toml` and the renamed CLI, then run `--check` and consumer tests.

No `rpckit` Python compatibility shim is installed. The old and new distributions
can coexist during application migration because their import namespaces differ.
Existing generic adapter seams are retained for tests and migration, while the
supported product experience is FastAPI WebSockets.

The name is distinct from `fastapi-ws-rpc` under
[PyPA normalization](https://packaging.python.org/en/latest/specifications/name-normalization/).
The PyPI JSON endpoint returned 404 on 2026-10-17. This is not a name reservation;
PyPI acceptance/ownership must be confirmed before configuring publication.
