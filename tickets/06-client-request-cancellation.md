# 06: Client request cancellation

- **Status:** done — [PR #29](https://github.com/mathisarends/pyrpckit/pull/29)
- **Priority:** high
- **Area:** generated clients (Python + TypeScript)
- **Depends on:** 04, 05

## Problem

When the client's request times out, or the caller cancels the request, the
server is never told. Server-side work continues uselessly. TypeScript
callers also have no way to cancel at all: there is no `AbortSignal`
support.

## Design

- Python: when `request()` exits because of `TimeoutError` or
  `CancelledError` after the frame was sent, send `$/cancelRequest` with the
  request id. Do this fire-and-forget: never block or raise because of it,
  and skip it when the transport is already closed.
  Any background send must have a bounded timeout, have its failure consumed,
  and be awaited or cancelled during close. Caller cancellation stays
  `CancelledError`; a cancel frame is best effort, not proof of server abort.
- TS: `request(method, params, { signal?: AbortSignal })`. Thread the option
  through the generated API methods as a trailing options object, for
  example `client.tasks.run(params, { signal })`. On abort, reject with
  `AbortError` semantics (`signal.reason`), remove the request from pending,
  and send `$/cancelRequest`. Timeouts send it too.
- Only send cancellation on the transport that carried the original request;
  never replay it onto a reconnected transport with reused request ids.
  Remove abort listeners and timers on every terminal path. Handle abort,
  response, timeout, and disconnect races with exactly one local settlement.
- Optional per-call timeout override on both sides (Python
  `client.x(params, timeout=...)` only if it fits the generated API style,
  TS `{ timeoutMs }`). If this does not fit cleanly, leave it out and note
  that in the PR.
- The server's `request_cancelled` answer is dropped by the client, which is
  already guaranteed by ticket 01.

## Acceptance criteria

- A Python request that times out or is cancelled after sending emits
  exactly one `$/cancelRequest`, and the server handler is cancelled (end to
  end against the ticket 05 server).
- TS: aborting via `AbortSignal` rejects immediately and cancels on the
  server. An already-aborted signal rejects without sending anything.
- No cancel is sent for requests that never left the client.
- Generated code passes `ruff` and the TS type check.
- `docs/clients.md` documents cancellation for both languages.

## Tests

- Python and TS end-to-end tests with a handler that waits on an event:
  cancel or time out from the client, then assert the handler observed
  cancellation.
- A test that no cancel frame is sent when the transport closed first.
- Race abort with response and timeout; close during a blocked cancel send.
  Assert no stale listeners, timers, or unobserved task failures remain.
