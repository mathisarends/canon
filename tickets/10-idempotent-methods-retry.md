# 10: Idempotent methods and automatic retry

- **Status:** open
- **Priority:** medium
- **Area:** contract (`rpckit/channel.py`, `rpckit/protocol.py`,
  `rpckit/schema/openrpc.py`), codegen IR, generated clients
- **Depends on:** 04, 07

## Problem

With `reconnect=True`, the client reconnects, but every request that was in
flight during the drop fails, and callers must write their own retry logic.
Retrying blindly is unsafe, because the server may already have executed a
non-idempotent call. The contract has no way to say which methods are safe
to retry.

## Design

- `@channel.method(idempotent=True)`. Store it on `RpcMethodDefinition` and
  export it in OpenRPC as an extension (`x-rpc-idempotent: true`, following the `x-rpc-` naming
  in `schema/openrpc.py`). Generators read it from
  the OpenRPC document, never from `RpcProtocol` (`AGENTS.md`).
- `codegen/ir.py`: carry the flag on `RouteDecl`. Include it in the route
  metadata of both generated clients (`metadata.py.j2`, TS route info).
- Client retry policy, configured on `connect(...)`:
  - `RpcConnectionLostError(sent=False)`: always safe, so retry for every
    method once the transport is back if retry is enabled (bounded by the
    overall call deadline). Unknown delivery is treated as sent, per 04.
  - `RpcConnectionLostError(sent=True)` and `RpcRequestTimeoutError`: retry
    only for idempotent methods.
  - Remote errors are never retried automatically.
  - Parameters: `retry_attempts` and backoff reused from the reconnect policy.
    Default to retry disabled to preserve existing execution behaviour;
    document an explicit opt-in. Distinguish total attempts from retries.
- Use one monotonic deadline for the logical call, including connection
  acquisition, queueing, send, response, and retry backoff. A per-attempt
  timeout may allow another attempt only while budget remains; an exhausted
  overall deadline never starts a retry. Do not reset the deadline each time.
- Never retry caller cancellation, explicit client close, permanent connect
  errors, response validation errors, or subscriptions/client methods as
  ordinary method calls. Retrying after ambiguous delivery can execute an
  idempotent handler concurrently with the first attempt; document that
  idempotency is a service guarantee, not server-side deduplication.
- Retries reuse the same params but a fresh request id. Once ticket 13 is
  merged, middleware must see each attempt and its error (ticket 13). Expose
  attempt metadata through the existing call path without requiring 13's API.
- Optional extension (note it in the PR, don't build it): idempotency keys
  for non-idempotent methods.

## Acceptance criteria

- The idempotent flag round-trips: decorator, OpenRPC, IR, generated route
  metadata (Python + TS).
- An idempotent call in flight during a drop succeeds transparently after
  reconnect.
- A non-idempotent call that was sent fails with
  `RpcConnectionLostError(sent=True)` and is not retried.
- A call that was never sent is retried for any method.
- Total time stays bounded by the request timeout or deadline.
- Docs: `docs/services.md` (flag) and `docs/clients.md` (retry semantics).

## Tests

- Schema export test for the extension, plus an IR test.
- End to end with fault injection: drop the connection after the request
  frame was delivered, then the idempotent call succeeds and the
  non-idempotent call raises.
- Drop the connection before sending, then the non-idempotent call
  succeeds.
- A send delivers then raises: non-idempotent work is not retried. Exhaust
  the overall deadline during backoff, and cancel during a retry; neither
  starts another attempt.
