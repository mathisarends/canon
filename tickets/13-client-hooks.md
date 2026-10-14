# 13: Client hooks for errors and per-call state

- **Status:** done ([PR #36](https://github.com/mathisarends/pyrpckit/pull/36))
- **Priority:** medium
- **Area:** generated clients (Python `runtime/core.py.j2`, TS `core.ts.j2`)
- **Depends on:** 04

## Problem

`RpcClientHook` has `before_request(route, params)` and
`after_response(route, result)` only.

- `after_response` is skipped when the request fails (see
  `RpcClientCore.request`), and there is no error hook. Client-side metrics,
  logging, tracing, and circuit breakers therefore cannot observe failures.
- Hooks cannot carry state from before to after (a span or a start time)
  except through context variables.
- Hooks cannot see duration, attempt number (ticket 10), or the transport or
  server used.

## Design

Prefer a middleware-style hook over adding more callbacks. It mirrors the
server's `RpcMiddleware` and solves state passing naturally:

```python
class RpcClientMiddleware(Protocol):
    def request(self, call: RpcClientCall) -> AsyncContextManager[None]: ...
```

`RpcClientCall` exposes `route`, `params` (JSON), `server`, `attempt`, and
after the block an `outcome`: `result` or `error`, plus `duration`.

- Keep `RpcClientHook` working: adapt it internally to the new mechanism, or
  deprecate it with a clear migration note. Decide in the PR. `after_response`
  semantics stay unchanged for success.
- Run middleware around retries (ticket 10) per attempt, or once around all
  attempts: use per-attempt execution when retry is available, with `attempt`
  starting at 1 and a shared logical-call identifier. Before 10 is implemented,
  every call has attempt 1. Keep 10 and 13 independently implementable.
- TS equivalent with the same shape (async function wrapping `next`, or
  `onRequest` / `onResponse` / `onError` callbacks; match TS idioms).
- Also apply middleware to `subscribe_remote` subscribe and unsubscribe
  calls, so they are observable.
- Finalize outcomes on remote, transport, validation, and cancellation paths,
  including failures before a transport was acquired. State whether duration
  includes acquisition and validation. Preserve the original call error if
  teardown or an observer callback also fails; define this policy explicitly.
- Define parameter mutation and metadata injection before validation/send
  for ticket 14. Middleware exceptions remain application exceptions, and
  cancellation is not converted to a retryable error. Legacy hooks keep their
  existing per-call semantics if retry adds per-attempt middleware.

## Acceptance criteria

- Errors (remote, transport, validation) are observable by client
  middleware in Python and TS.
- Middleware can keep per-call state without context variables.
- Existing hooks keep working, or have a documented migration path.
- `docs/clients.md` and `docs/observability.md` updated.

## Tests

- Middleware sees success with result and duration, a remote error, a
  transport error, and a response validation error.
- Ordering of several middlewares (onion order) is tested.
- Legacy `RpcClientHook` still receives `before_request` and
  `after_response`.
- Cancellation, acquisition failure, middleware failure during cleanup, and
  an optional retry attempt all produce the documented ordering and outcome.
