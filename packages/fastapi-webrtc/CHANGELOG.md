# Changelog

## 0.1.0 - Unreleased

Initial release.

- `WebRtcRouter.session()` declares WebRTC sessions as WebSocket signaling
  endpoints. FastAPI dependencies admit sessions before any peer is created and
  stay open until cleanup finished, also when the server cancels the endpoint.
- `Session` handlers: `on_start`, `run`, `on_track`, typed `on_message`,
  `on_close` and outgoing tracks. `Peer` sends messages and tracks with
  renegotiation, and exposes stats and close codes. Stats report jitter as
  `None` when the engine cannot convert it to seconds (aiortc).
- Track ownership: session tracks and `send_track(track)` are stopped on removal
  or cleanup, including rejected and partially started sessions;
  `send_track(track, owned=False)` keeps shared sources running behind a
  sender-local forwarding track. Only active
  incoming tracks count against `MediaPolicy.max_incoming_tracks`.
- Typed data channels from Pydantic models, `str` or `bytes`. JSON messages use
  the contract's serialization aliases. Channels support negotiated IDs,
  validated reliability options, size limits, bounded inbound queues and send
  backpressure.
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
