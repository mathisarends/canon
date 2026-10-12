# 11: Graceful drain on shutdown

- **Status:** open
- **Priority:** high
- **Area:** server (`rpckit/runtime.py`, `rpckit/connection.py`,
  `rpckit/websocket.py`, `rpckit/integrations/fastapi.py`)
- **Depends on:** 05, 07 (in-flight registry and transient-close handling)

## Problem

On shutdown, the serving task is cancelled. `_serve_endpoint` catches
`CancelledError`, cancels every in-flight request immediately, and closes
with `SHUTDOWN` (1001). On every rolling deploy, all in-flight requests fail
and clients cannot tell "server restarting, reconnect soon" from other
closes. The close-code table (`rpckit/websocket.py::CLOSE_CODES`) has no
1012 (Service Restart).

## Design

- A drain API that applications call from their lifespan or shutdown hook
  before the server cancels tasks. For example, an `RpcDrain` or
  `RpcShutdown` object passed to endpoints or `RpcRoutes`, with
  `await drain.drain(timeout=...)`. It should not need a reference to every
  connection.
- During drain:
  - new connections are rejected with `UNAVAILABLE` (1013, try again later);
  - on open connections, new requests get a built-in `server_shutting_down`
    error (or are still accepted until a grace point, so pick and document);
  - in-flight requests, subscriptions, and streams may finish until the
    timeout;
  - afterwards, each connection closes with a new
    `RpcConnectionClose.SERVICE_RESTART` (1012), and remaining work is
    cancelled.
- Clients (ticket 07) treat 1012 and 1013 as transient and reconnect. Also
  check that 1001 is handled the same way.
- Streams and raw sockets: closed with 1012 after the timeout. They do not
  need request-level draining.
- FastAPI integration: a documented lifespan example. Read up on how
  Starlette/uvicorn cancel WebSocket tasks on shutdown and on
  `--timeout-graceful-shutdown`, and make sure the drain runs before the
  cancellation.
  Do not assume the teardown after lifespan `yield` runs before WebSocket
  tasks are cancelled. Verify shutdown ordering for the supported server and
  provide a real pre-shutdown trigger (for example an application-controlled
  drain before stopping the process). State when lifespan teardown is only
  final cleanup; a lifespan-only unit test cannot prove deployment ordering.
- Make drain idempotent and handle simultaneous drain/close/disconnect.
  Stop unbounded event producers, track long-lived subscriptions separately
  from finite requests, and flush already-enqueued responses within the grace
  period before closing. The deadline bounds flush and final cleanup too.

## Acceptance criteria

- During drain, in-flight requests complete and their responses are
  delivered.
- New connections are rejected with 1013, and connections close with 1012
  when the drain finishes or times out.
- Observers and middleware see the shutdown close code.
- `docs/transports.md` (FastAPI lifespan example) and
  `docs/connections-and-events.md` (close codes).

## Tests

- In-memory test: start a slow request, start the drain, assert the request
  completes and the close code is 1012.
- Drain timeout: a stuck request is cancelled when the timeout expires.
- New connection during drain is rejected.
- FastAPI test with the lifespan.
- Integration test or reproducible smoke check against the supported ASGI
  server: start a request, trigger pre-shutdown drain, then stop the server;
  the response arrives before the restart close. Queued responses and an
  endless event source cannot hang drain past its deadline.
