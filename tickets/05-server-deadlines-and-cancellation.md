# 05: Server request deadlines and cancellation

- **Status:** open
- **Priority:** high
- **Area:** server (`rpckit/runtime.py`, `rpckit/server.py`,
  `rpckit/connection.py`, `rpckit/channel.py`, `rpckit/protocol.py`, schema)
- **Depends on:** 01, 15 (late-response tolerance and per-item admission)

## Problem

1. **No handler deadline.** A hanging handler keeps its slot in the
   per-connection semaphore (`max_concurrency`, default 32) forever. After 32
   hung calls, the connection stops processing requests. Nothing tells the
   client.
2. **No cancellation.** When a client gives up on a request (timeout, user
   abort), the handler keeps running on the server and wastes resources.
   JSON-RPC has no built-in cancel, so rpckit needs a convention.

## Design

### Deadlines

- `RpcLimits.request_timeout: float | None`, with a sensible default. Choose
  between `None` (backwards compatible) and a value such as 60 s, and justify
  the choice in the PR.
- Per-method override: `@channel.method(timeout=...)`. Store it on
  `RpcMethodDefinition`.
- Define whether queue/semaphore wait and dependency resolution count toward
  the deadline, and how an explicit `None` differs from an omitted method
  override. Use a monotonic clock. Keep `RpcServer.handle` / `handle_json`
  deadlines consistent with endpoint serving; document any transport-specific
  cancellation limitation.
- When the deadline expires, the handler is cancelled and the client
  receives a built-in error `request_timeout` (`SERVER_ERROR` rpc code, like
  `pending_limit`). It counts as a builtin for `strict_errors` purposes.
  Check how `RpcPendingLimitError` behaves under `strict_errors` and make
  both consistent.
- Middleware and observer outcomes record the timeout distinctly (not as an
  internal error).

### Cancellation

- The server keeps a registry `request id → task` for in-flight requests in
  `_serve_endpoint` (batches: per item).
- Reserved notification `$/cancelRequest` with params `{"id": <request id>}`
  (LSP convention). Make sure user methods cannot be named with the `$/`
  prefix, or document the reservation.
- When the server receives it, it cancels the matching task. The cancelled
  request is answered with error `request_cancelled` (code -32800, as in LSP)
  so the protocol stays well-formed; clients drop it per ticket 01.
- Unknown or finished ids are ignored silently.
- Control notifications bypass the handler semaphore and pending admission,
  while retaining message/parameter validation and bounded processing. A full
  queue must not stop a cancel from cancelling queued or executing work.
- Preserve request-id types (string and integer ids must not collide).
  Duplicate in-flight ids must not overwrite the original registry entry;
  choose a documented rejection policy. Notifications have no cancellable id.
- Distinguish request cancellation from connection/server shutdown. Do not
  emit `request_cancelled` responses on a disconnected socket or swallow
  outer serving-task cancellation. Cleanup releases ticket 15's accounting.
- Export the convention in the OpenRPC document (an `x-rpc-` extension, matching `schema/openrpc.py`, or
  info in the docs) so that non-rpckit clients can use it.
- Optional, but nice: `RpcConnectedClient.call` sends `$/cancelRequest` to the
  client when its own `client_method_timeout` expires.

### Subscriptions

Decide and document whether `subscribe` requests fall under the deadline.
They should not: only the subscribe handshake does, not the stream.

## Acceptance criteria

- A handler exceeding its deadline is cancelled and its semaphore slot is
  freed. The client receives `request_timeout`.
- `$/cancelRequest` cancels the handler. Dependency scopes and middleware
  exit cleanly, and the client gets `request_cancelled`.
- Docs: `docs/services.md` (timeouts) and a section on cancellation in the
  protocol docs.

## Tests

- `tests/test_runtime.py`: hung handler + `request_timeout` → error and slot
  freed (run `max_concurrency + 1` hung calls).
- Per-method timeout overrides the limit.
- Cancel an in-flight request and assert that the handler saw
  `CancelledError`, that the response is `request_cancelled`, and that the
  next request on the connection works.
- Cancelling unknown ids does nothing.
- Saturate all handler slots, then cancel a queued and an executing call;
  both cancellations are processed without waiting for a free slot.
- Mixed batch, string/integer ids, duplicate ids, and shutdown cancellation.
