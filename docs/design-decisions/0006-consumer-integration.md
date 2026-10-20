# 0006: Close consumer integration gaps without coupling the extensions

Status: implemented, unreleased. Prepared versions: Canon 0.6.0, WebRTC 0.2.0
and RPCkit 0.4.0. Streams remains at published 0.4.0.

## Evidence

The [Maximus integration report](../feedback/2026-10-20-maximus.md) describes
adoption of the released stack, including native Linux Chromium/GStreamer tests.
Those are consumer-reported results, separate from this workspace's independent
tests. It demonstrates successful remote engine adoption without library patches
and identifies repeated integration work rather than a signaling defect.

## Decisions

1. Canon owns the optional `CanonWebRtcRouter`, reusing the exact existing `Error`
   definitions, registry membership rules and shared/local `raises` semantics.
   A neutral admission contract-provider hook belongs to WebRTC; neither package
   gains a required dependency on the other. Export resolves types against the
   composed registry and embeds self-contained Problem Details schemas.
2. Admission metadata describes HTTP rejection before WebSocket acceptance.
   Dependencies' errors are declared explicitly. `raises` is documentation, not
   a runtime allowlist. Accepted-session errors retain WebRTC framing and teardown.
   Contract metadata cannot expose failed handshakes through browser WebSocket APIs.
3. `Session.engine` binds a remote peer's resource identity without disguising it
   as a native media track. A router engine remains the default; factories can
   supply all bindings when no default exists. The runtime owns created peers;
   a factory dependency owns remote leases and closes them even before acceptance.
4. The executable send-only example uses an independent async context manager for
   every viewer, idempotent cleanup, actual native connection events, explicit
   unsupported operations and partial stats. It does not stop shared capture
   sources. Expected engine creation failures preserve existing `WebRtcError`
   categories; new wire categories require a separate protocol decision.
5. Browser media observation is optional and separate from transport readiness.
   It has distinct opt-in first-frame/stall deadlines, decoding and compositor
   measurements, recovery, per-track selection and bounded non-overlapping polling.
   The application retains control of UI and fallback policy.
6. Generated RPC factory protocols accept positional URLs. Lazy default connectors
   also adapt `websockets`' nominal subprotocol type, preserving neutral factory
   protocols and custom factory support. Typechecking covers the actual generated
   backends and a custom factory whose first parameter has a different name.

## Verification and remaining scope

Tests cover admission from factories/dependencies before peer allocation, declared
and undeclared registry members, nested problem schema references, effective
mounted paths, generated metadata and post-accept errors. Remote tests cover
concurrent bindings, second-viewer rejection, cancellation before an offer,
shutdown and partial setup failure. Chromium exercises generated clients and
real peers, video output, an intentional presentation stall and recovery.

The optional HTTP ticket recipe is an application pattern, not a ticket store or
authentication framework. Partial stats must remain explicit. A generic engine
capability split, maintained CDP/cdpify binding, native GStreamer adapter, new
busy/unavailable wire codes and RPCKit signaling adapter remain deferred until
their concrete reuse and ownership are established.

Current and minimum wheel checks include ten independent combinations, including
all four packages and Canon's WebRTC extra. Release validation checks the optional
WebRTC pin and requires it to be published before Canon. Source preparation and
dry runs do not authorize or constitute publication.
