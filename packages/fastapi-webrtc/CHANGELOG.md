# Changelog

## 0.2.0 - Unreleased

### Breaking changes

- Generated runtimes export `observeVideoHealth` and its types. Regenerate clients
  and rename any colliding session/client declarations reported by code generation.
  Existing `connect()` readiness semantics are unchanged.
- Add `Session.engine` and allow a router without a default engine when factories
  bind one per session. Custom constructor overrides should accept an optional
  engine. Supply either a router engine or a session engine; missing bindings are
  refused with `handler_failure` and returned tracks are cleaned up.
- Extend `WebRtcRouter.session()` and `SessionDeclaration` with the optional
  `admission_errors` contract-provider hook. Custom router overrides must accept
  and forward this keyword. Regenerate clients to include declared admission
  metadata in session descriptors. The signaling protocol remains v1.

### Added

- Optional browser video health observation with separate opt-in first-frame and
  ongoing-stall deadlines, recovery events, per-track decoded stats and optional
  compositor frame callbacks. Abort, session close and `stop()` release observers;
  observation never closes sessions, stops tracks or chooses a fallback UI.
- A tested remote send-only adapter example with per-viewer async-context-manager
  leases, explicit unsupported operations and partial statistics. Categorized
  `WebRtcError` failures during peer creation retain their stable protocol code.
- Canon-independent admission contract export, including optional generated
  descriptor metadata. HTTP denials remain distinct from accepted-session errors;
  this metadata does not expose failed WebSocket handshake bodies in browsers.

## 0.1.0 - 2026-10-20

Initial release.

- `WebRtcRouter.session()` declares WebRTC sessions as WebSocket signaling
  endpoints. FastAPI dependencies admit sessions before any peer is created and
  stay open until cleanup finished, also when the server cancels the endpoint.
- `Session` handlers: `on_start`, `run`, `on_track`, typed `on_message`,
  `on_close` and outgoing tracks. `Peer` sends messages and tracks with
  renegotiation, and exposes stats and close codes. Stats report jitter as
  `None` when the engine cannot convert it to seconds (aiortc). `on_close` runs
  once per accepted session and keeps at least one second even when cancelled
  handlers used up `shutdown_timeout_seconds`.
- Track ownership: session tracks and `send_track(track)` are stopped on removal
  or cleanup, including rejected and partially started sessions;
  `send_track(track, owned=False)` keeps shared sources running behind a
  sender-local forwarding track. Only active
  incoming tracks count against `MediaPolicy.max_incoming_tracks`.
- Typed data channels from Pydantic models, `str` or `bytes`. JSON messages use
  the contract's serialization aliases. Channels support negotiated IDs,
  validated keyword-only reliability options, size limits, bounded inbound
  queues and send backpressure. A `DataChannelSpec` is generic over its message
  types: `on_message` accepts specs as keys, and `peer.channel(spec)` and
  `peer.send_message(spec, ...)` are type-checked against its models.
  `Never` as `receive_model` or `send_model` declares a one-way channel
  (format `none`); the generated client omits `send` or `subscribe` for it.
- Signaling protocol `fastapi-webrtc.v1`. It uses perfect negotiation,
  candidate buffering, ICE username checks, categorized close codes and
  negotiation, media and transport deadlines. Negotiation timeouts and shutdown
  cancel blocked ICE and engine startup.
- ICE server providers, `TurnRestCredentials` with separate engine URLs and
  session event hooks.
- `WebRtcRouter(allowed_origins=...)` refuses cross-site browser handshakes with
  HTTP 403 before the session factory runs.
- A pluggable `Engine` protocol, with an `aiortc` reference engine behind the
  `aiortc` extra.
- Tested Canon/Dishka composition with explicit async-factory injection,
  session services, per-message request scopes and ordered cleanup.
- `fastapi-webrtc contract` and `fastapi-webrtc generate` export a session
  contract and generate a dependency-free TypeScript browser client with typed
  parameters, channels and errors. Query models become flat named parameters.
  Ambiguous generated names fail before files are written. Both commands support
  `--check` drift detection.
- The browser client merges query values from the base URL, shared credential
  providers, per-call maps and named parameters, in that order; `null` removes
  a value. `timeoutMs` bounds credential resolution and connection setup;
  `signal` cancels the whole session. Renegotiation
  and channel sends (`sendTimeoutMs`) have deadlines after connect, and
  permanent transport failure rejects pending operations.
