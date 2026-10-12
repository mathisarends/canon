# 09: Dead-connection detection in the TypeScript client

- **Status:** open
- **Priority:** high
- **Area:** generated TypeScript client (`transport.ts.j2`, `core.ts.j2`);
  possibly the server (`rpckit/runtime.py`) for a ping method
- **Depends on:** 05, 07 (reserved control namespace and reconnect lifecycle)

## Problem

A browser `WebSocket` cannot send pings. A half-open connection is not
detected for minutes: the TCP peer is gone but no close event fires. This
happens after mobile network switches, NAT timeouts, or laptop sleep. In that
state:

- each request runs into its own timeout, one after another;
- the transport never counts as failed, so **reconnect never triggers**;
- notification streams just go silent.

The server pings browsers (uvicorn's default `ws_ping_interval`), so the
server notices. The client does not.

The Python client is covered by the `websockets` default keepalive
(`ping_interval` and `ping_timeout` of 20 s), but only with the default
`socket_factory`. Document that.

## Design

Two complementary mechanisms, both configurable and on by default only
where safe:

1. **Application heartbeat.** The client sends a reserved, cheap request (for
   example `$/ping`, answered by the server runtime without going through
   user handlers, middleware, or observers) every `heartbeatIntervalMs` when
   no other traffic arrived in that interval. If no answer arrives within
   `heartbeatTimeoutMs`, the transport is failed with
   `RpcConnectionLostError`, and reconnect takes over.
   - Server side: handle `$/ping` in `_serve_endpoint` before dispatch.
     Reserve the name together with `$/cancelRequest` (ticket 05). Export it
     in the OpenRPC document as an rpckit extension.
2. **Consecutive-timeout breaker** (cheap fallback): after N consecutive
   request timeouts with no other inbound traffic, treat the transport as
   dead.

Negotiate heartbeat support through an OpenRPC extension before enabling it
by default. A generated client using an older or third-party server must not
disconnect merely because `$/ping` is unsupported. Specify its params/result
wire shape, capability fallback, and whether Python custom factories can opt
in. Browser timers may pause in background tabs or during sleep; recheck
liveness on wake without a burst of queued heartbeats.

Use a single bounded outstanding heartbeat per transport. It bypasses the
server handler semaphore so overload does not look like a dead connection,
but still receives message validation and bounded control processing. Clean
up all timers/listeners on close and reset timeout-breaker state on valid
inbound traffic. Keep this ticket's changes to Python limited to any shared
capability metadata and documentation unless opt-in is implemented.

## Acceptance criteria

- On a half-open connection, the TS client detects it within
  `interval + timeout` and reconnects (with `reconnect: true`). State
  callbacks from ticket 07 fire.
- Heartbeats do not show up in user middleware, observer metrics, or OTel
  spans.
- Heartbeats are suppressed while other inbound traffic proves liveness.
- Docs: `docs/clients.md` (keepalive, Python vs. TS) and
  `docs/transports.md` (server ping settings).

## Tests

- TS test with a fake socket that silently stops delivering messages:
  transport fails after the heartbeat timeout and reconnect happens. Use fake
  timers.
- Server test: `$/ping` gets an answer and is invisible to middleware and the
  observer.
- Unsupported heartbeat, saturated handler slots, background timer pause,
  resumed traffic resetting the breaker, and no timers surviving close.
