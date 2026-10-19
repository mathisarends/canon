# Changelog

## 0.1.0 - Unreleased

Initial release.

- `WebRtcRouter.session()` declares WebRTC sessions as WebSocket signaling
  endpoints. FastAPI dependencies admit sessions before any peer is created.
- `Session` handlers: `on_start`, `run`, `on_track`, typed `on_message`,
  `on_close` and outgoing tracks. `Peer` sends messages and tracks with
  renegotiation, and exposes stats and close codes.
- Typed data channels from Pydantic models, `str` or `bytes`. Channels support
  negotiated IDs, reliability options, size limits, bounded inbound queues and
  send backpressure.
- Signaling protocol `fastapi-webrtc.v1`. It uses perfect negotiation,
  candidate buffering, ICE username checks, categorized close codes and
  negotiation, media and transport deadlines.
- ICE server providers, `TurnRestCredentials` with separate engine URLs and
  session event hooks.
- A pluggable `Engine` protocol, with an `aiortc` reference engine behind the
  `aiortc` extra.
- `fastapi-webrtc contract` and `fastapi-webrtc generate` export a session
  contract and generate a dependency-free TypeScript browser client with typed
  parameters, channels and errors. Both commands support `--check` drift
  detection.

### Breaking changes

These corrections apply to the unreleased initial SDK. Regenerate clients before
adopting the reviewed 0.1.0 source; no published WebRTC release is superseded.

- Outgoing JSON messages use Pydantic serialization aliases, including nested
  models. Consumers of provisional payloads must read the alias keys advertised
  by the contract instead of Python field names.
- Query models export flat FastAPI query fields. Replace provisional object
  parameters such as `filters` with the generated named fields; aliases, defaults,
  required metadata and repeated list values are retained.
- Ambiguous generated names now fail before writing files. Rename sessions such
  as `config`, distinguish names such as `foo_bar`/`fooBar`, or choose a client
  class that does not collide with a generated session type.
- Named connect query parameters override per-call query maps, shared credentials
  and base-URL query values, in that order. Required query values are checked
  after merging. Generated query fields are optional to allow shared credentials;
  required path fields remain mandatory. Omit a named value to retain shared
  credentials; use `null` to remove it explicitly.
- Data-channel reliability options are mutually exclusive even when zero, and
  accept only integers from 0 through 65535. Supply at most one option and fix
  invalid values at declaration time instead of relying on engine errors.
- Browser renegotiation and channel sends now have operation deadlines after
  connect. Handle `negotiation_timeout`/`slow_consumer` rejections and reconnect
  after termination. Set `sendTimeoutMs` when the 10-second send default is too
  short; rename any provisional route parameter with that reserved option name.

### Fixes

- Finish session cleanup before dependency teardown even when ASGI cancels the
  endpoint during cleanup; `on_close` retains access to its session services.
- Bound browser renegotiation by the server's negotiation deadline, including
  stalled SDP/track operations. Bound sends independently of connect, and reject
  all pending operations on permanent peer-connection failure.
- Report unavailable aiortc jitter as `None`: its RTP timestamp units cannot
  be converted to seconds without a reliable per-stream codec clock rate.
- Count only active incoming tracks against media limits, releasing capacity
  exactly once when a track ends so replacements can use the same session.
- Release tracks returned by session factories on router/endpoint capacity,
  shutdown and invalid-handler rejection, before dependency teardown.
- Protect borrowed aiortc sources with sender-local forwarding tracks. Closing
  the RTP sender releases its wrapper while session ownership controls the source.
- Cancel blocked ICE and engine startup on negotiation timeout or shutdown,
  release session slots and dependencies, and close peers returned during
  cancellation without starting signaling.
- Own initial session tracks before attachment and release all owned tracks on
  early disconnects, timeouts and partial attachment failures.
- Apply browser connect timeout and abort handling to asynchronous credential
  resolution as well as negotiation. Late credentials cannot create a socket
  after termination; the deadline is not restarted after preparation.
- Use `timeoutMs: 10_000` in the browser quickstart. `signal` also closes a running
  session, so a timed signal limits the entire session lifetime.
