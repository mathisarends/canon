# 12: Credential expiry on long-lived connections

- **Status:** open
- **Priority:** medium
- **Area:** server (`rpckit/connection.py`, `rpckit/runtime.py`), docs,
  generated clients (verification only)
- **Depends on:** 07

## Problem

Authentication happens once in `before_accept`, at the handshake. A WebSocket
can stay open for hours after the token expired or was revoked, and remains
fully authorized. rpckit offers no API or documented pattern for that.

Browser clients cannot set headers on a WebSocket at all. The TS client only
supports `subprotocols`, so auth has to go through query parameters,
subprotocols, or cookies. None of this is documented.

## Design

- Server API: let `before_accept` (or the handler code) set an expiry on the
  connection, for example by returning or setting
  `connection.expires_at: float | None`, or by calling
  `connection.expire_at(ts)`. When the expiry passes, the runtime closes the
  connection with a dedicated close. Use either the policy violation code
  with reason `credentials_expired`, or an application close code in the
  4000 range; pick one and document it. Revocation is already possible via
  `connection.close(...)`. Document that too.
- Expiry must be unambiguously distinguishable from other policy violations,
  using a documented application close code or a narrowly matched reason.
  Do not make all 1008 closes retryable. Invalid refreshed credentials must
  terminate or exhaust the configured refresh/reconnect budget, rather than
  loop forever. The refresh provider may need async I/O; document how that
  works without blocking the event loop.
- Define timestamp units and clock conversion, cancel the expiry timer on
  disconnect, and close RPC, stream, and raw endpoints consistently. Do not
  expose tokens in close reasons, logs, or state callbacks.
- Client side: the Python `headers` argument already accepts a callable that
  is re-evaluated per connect. Make sure the reconnect policy (ticket 07)
  treats the expiry close as **transient**, so the client reconnects with
  fresh credentials. Do the equivalent for TS (a callable for URL, query,
  or subprotocol credentials if needed).
- Docs: a new "Authentication" section in `docs/connections-and-events.md`
  (or a new guide) that covers:
  - header auth (Python/server-to-server);
  - browser auth via short-lived ticket in the query, cookie, or subprotocol,
    with the security trade-offs (query strings end up in logs);
  - cookie auth with Origin validation, cookie policy, and cross-site
    connection controls; subprotocol token syntax and negotiation; TLS and
    redaction of credentials in URLs and telemetry;
  - expiry and revocation;
  - the reconnect-with-refresh flow.

## Acceptance criteria

- A connection with `expires_at` in the past (or reaching it) is closed with
  the documented code and reason. Observers see it.
- The generated clients reconnect after that close and call the
  headers/credentials provider again.
- Docs cover both header-based and browser auth.

## Tests

- Runtime test: expiry set in `before_accept`, then the connection is closed
  after the expiry (controllable clock).
- Client test: an expiry close leads to a reconnect with refreshed headers
  (provider called twice).
- Generic policy rejection is terminal; expiry refresh succeeds once or
  fails with a bounded terminal outcome. Disconnect before expiry leaves no
  timer; browser credential providers are re-evaluated on reconnect.
