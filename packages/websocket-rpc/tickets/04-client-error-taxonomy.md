# 04: Client error taxonomy

- **Status:** done
- **PR:** https://github.com/mathisarends/pyrpckit/pull/27
- **Priority:** high
- **Area:** generated clients (Python + TypeScript)
- **Depends on:** 01

## Problem

1. **Raw exceptions leak (Python, verified).** When the socket fails,
   `transport.py.j2::_receive` calls `_fail_pending(error)` with the raw
   exception. In-flight requests raise `ConnectionResetError`,
   `websockets.exceptions.ConnectionClosedError`, and so on. Code that
   catches `RpcClientError` misses the most common production failure.
   `transport.closed` resolves with the raw exception too.
2. **TS errors are untyped.** Pending requests reject with plain
   `Error("The WebSocket connection closed")`, `Error("... failed")`, and
   `Error("RPC request x timed out")`. `instanceof` checks are impossible,
   and close codes and reasons are lost.
3. **Retry-relevant situations are indistinguishable.** Timeout, "connection
   lost before the request was sent", and "connection lost after it was sent"
   are all `RpcTransportError` (or a plain `Error`). Callers and ticket 10's
   automatic retry need to tell them apart, because only "not sent" is always
   safe to retry.

## Design

One hierarchy, mirrored in Python (`runtime/errors.py.j2`) and TS
(`typescript/core.ts.j2`). Keep the existing names as base classes so
current `except` clauses keep working:

```
RpcClientError
├── RpcRemoteError …                          (unchanged)
├── RpcTransportError                         (existing base)
│   ├── RpcRequestTimeoutError                (method, timeout)
│   ├── RpcConnectionLostError                (sent: bool, code, reason)
│   └── RpcConnectError                       (could not open; permanent: bool)
└── RpcConnectionClosed                       (existing: code, reason)
```

- `sent=False` must mean provably not sent. Once `send` has begun, including
  when it raises or is cancelled before completing, delivery may be unknown;
  classify that conservatively as `sent=True`, or add an explicit unknown
  state treated identically by retry policy. A failed `send` is not proof
  that the server did not execute the call. Track this per pending request.
- `RpcConnectError.permanent` is set for handshake rejections that will not
  succeed on retry: HTTP 401/403/404 or a close with policy violation.
  Ticket 07 uses it. Extract status and code duck-typed (for example via
  `response.status_code`, `rcvd.code`) so the runtime keeps no hard
  `websockets` import.
- The exact names are open for discussion in the PR, but whatever is chosen
  must exist in both languages.
- Chain an original transport error (`from error` / `cause`) when available.
- Preserve caller cancellation and user hook exceptions; the hierarchy
  applies to library, validation, remote, and transport failures, not every
  possible exception from application code. TS aborts are specified in 06.
- Browsers generally hide HTTP handshake status and expose an opaque error
  event. Preserve classification only when status/code is actually available;
  unknown failures remain bounded by ticket 07's policy, without inventing
  an HTTP status. Document this Python/browser difference.
- `transport.closed` resolves with the wrapped error.

## Acceptance criteria

- Library-originated failures from `request()`, notification iterators,
  subscriptions, or `closed` use the client hierarchy in Python and TS;
  caller cancellation and application exceptions retain their semantics.
- Close code and reason of a server-initiated close are available on the
  error.
- A request that never left the client raises `RpcConnectionLostError` with
  `sent=False`, and one that did raises it with `sent=True`.
- `docs/clients.md` gets a short "Errors on the client" section with the
  hierarchy and when each error occurs.

## Tests

- Fake socket raising `ConnectionResetError` → `RpcConnectionLostError`
  with a cause.
- Server closes with 1011 mid-request → error carries `code == 1011`.
- Timeout → `RpcRequestTimeoutError`, still a subclass of
  `RpcTransportError`.
- Python and TS equivalents.
- A socket that delivers the frame and then raises is never reported as
  provably unsent. Two simultaneous calls retain their individual send state.
