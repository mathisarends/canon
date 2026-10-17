# 14: Per-request trace context propagation

- **Status:** done ([PR #37](https://github.com/mathisarends/pyrpckit/pull/37))
- **Priority:** medium
- **Area:** wire protocol convention, server (`rpckit/runtime.py`,
  `rpckit/integrations/opentelemetry.py`), generated clients
- **Depends on:** 13

## Problem

The OpenTelemetry integration extracts trace context only from the
**handshake headers** (`OpenTelemetry.connection` in `rpckit/integrations/opentelemetry.py`:
`propagate.extract(scope.handshake.headers)`). On a long-lived WebSocket,
every RPC span is parented to the trace that opened the connection, possibly
hours earlier. Distributed traces from a caller's request through the RPC
into the server are broken for everything after the handshake.

## Design

- Wire convention for per-request metadata. Decide in the PR; recommended:
  - `params._meta` (the MCP convention), with keys `traceparent`,
    `tracestate`, and optionally `baggage`. It needs named params and a
    reserved key that user params cannot use. Validation must strip it
    before params validation.
  - Alternative: a top-level envelope extension (for example `"meta"`),
    requiring explicit support in `RpcRequestEnvelope` and a documented
    interoperability policy. Avoid changing positional-param semantics just
    to insert metadata.
- Server: the dispatcher extracts and strips the metadata before params
  validation, and exposes it on the request scope (`RpcRequestScope` /
  `RpcRequestContext`). The OTel integration's request span uses the
  per-request context as its parent when it is present, and links to the
  connection span. Otherwise it keeps today's behaviour.
- Client: a built-in client middleware (from ticket 13), or a documented
  recipe, injects the current context. Python: an optional
  `rpckit`-generated helper that uses `opentelemetry.propagate.inject` only
  if OTel is installed. Generated code must not hard-depend on OTel. TS: a
  documented middleware.
- Document the convention in the OpenRPC output (an extension) so
  non-rpckit clients can participate.
- Same for subscriptions and client methods (server-to-client calls inject
  the server's context).
- Specify missing, invalid, and oversized metadata handling; bound its size
  and allowed value types. If `params._meta` is chosen, enforce the reserved
  field at definition/schema time and explain how no-param calls work. Older
  contracts with a conflicting field need a clear migration path.
- Keep each batch member's context independent, and detach context on every
  exit so concurrent calls cannot inherit each other's spans. Treat inbound
  tracing as remote context; do not turn baggage into authorization data or
  unrestricted log attributes. Define opt-in baggage propagation.

## Acceptance criteria

- A request carrying `traceparent` in its metadata produces a server span
  whose parent is that context.
- Params validation never sees metadata. If `_meta` is used, conflicting
  user params are rejected at definition/schema time, with migration guidance.
- No new hard dependencies in the runtime or generated code.
- `docs/observability.md` documents the convention and the client setup.

## Tests

- `tests/test_opentelemetry.py`: per-request parent wins over the handshake
  context, and the handshake context is still used without metadata.
- Dispatcher test: metadata stripped, params valid.
- Generated-client test: the middleware injects `traceparent`.
- Two concurrent calls and a mixed-context batch have distinct parents;
  invalid metadata and cancelled calls leave no context behind. Exercise
  no-param calls, subscriptions, and server-to-client propagation.
