# 0005: Add `fastapi-webrtc` as an independent extension

Status: implemented and published as 0.1.0 on 2026-10-20. Tracks
[issue #2](https://github.com/mathisarends/canon/issues/2).

The consumer-driven 0.2.0 preparation is recorded in
[decision 0006](0006-consumer-integration.md).

The Maximus trading application signals WebRTC through hand-written FastAPI
WebSocket routes, an aiortc peer and hand-written browser code. Those parts
repeat for every session. Admission, negotiation, data-channel encoding,
cleanup and error reporting are not typed across the HTTP boundary. This
package makes that the declarative path, with the same contract and codegen
approach as Streams and RPCKit.

## Decisions

1. **A session is a FastAPI dependency.** `WebRtcRouter.session()` registers a
   WebSocket route whose factory returns a `Session`. FastAPI resolves path,
   query and security dependencies before the handshake is accepted. No engine
   peer exists for refused sessions. Generator dependencies stay open for the
   lifetime of the session.
2. **One signaling protocol, `fastapi-webrtc.v1`.** JSON over the session's
   WebSocket, with a `session` hello, numbered descriptions, trickled candidates,
   `ready` and non-terminal `error` messages. Terminal failures are WebSocket
   close codes whose reason is a stable error category. Renegotiation uses
   perfect negotiation, with a polite browser. See the
   [protocol](../../packages/fastapi-webrtc/docs/protocol.md).
3. **Engines are adapters.** The runtime depends on a small `Engine` protocol.
   aiortc is the reference engine behind an extra. GStreamer, remote-peer or
   SFU adapters can implement the protocol without changing sessions or clients.
   Tests use a deterministic in-process engine for protocol behavior. They also
   use aiortc and Chromium for interoperability.
4. **The contract is derived, not written.** `build_contract()` reads session
   declarations, effective route paths (including nested prefixes), path and
   query parameters with their constraints, and channel models. It reads models
   in validation mode for the direction the server receives and serialization
   mode for the direction it sends. Headers are omitted because browsers cannot
   set WebSocket headers. Cookies are sent automatically, so the client offers
   `query` for tokens instead of a `credentials` option.
5. **The browser client is generated and dependency-free.** `fastapi-webrtc
   generate` emits `runtime.ts`, `models.ts`, `client.ts` and `index.ts`, plus a
   manifest that records owned files. The API follows the issue's sketch:
   `new Client(config).<session>.connect({...params, tracks, signal, onTrack,
   onMessage})`. It returns typed `session.channels.<name>.send()` and an
   idempotent `session.close()`. Borrowed tracks are never stopped.
6. **Limits are explicit and categorized.** `SessionLimits` bounds every queue,
   buffer, size and deadline. Exceeding one closes or reports with a specific
   error code, never with a generic failure.
7. **No required dependency on Canon, RPCKit or GStreamer.** Canon composition
   works with `WebRtcRouter` as an ordinary router. Wheel checks cover WebRTC
   alone, with aiortc, and together with Canon.
8. **Dishka injection is explicit at the async session factory.** Use `@inject`
   with `Scope.SESSION` services and child `Scope.REQUEST` containers for
   per-message resources. Callbacks capture services from the factory. The
   [integration guide](../../packages/fastapi-webrtc/docs/canon-dishka.md) and
   lifecycle tests cover admission, disconnect and shutdown without an adapter.

## Deferred

- An RPCKit signaling adapter.
- Native GStreamer and production remote-peer engines beyond the tested lease
  adapter example added in 0.2.0.
- ICE restart on transport loss. The protocol reserves the capability, and the
  aiortc engine does not support it.
- Forced-TURN CI. Optional client media-stall observation is implemented in 0.2.0.
