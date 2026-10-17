# 03: Fault-injecting sockets for resilience tests

- **Status:** done
- **PR:** https://github.com/mathisarends/pyrpckit/pull/26
- **Priority:** high
- **Area:** `rpckit/testing.py` (public, documented), tests
- **Depends on:** –

## Problem

Most open hardening work (reconnect, cancellation, timeouts, drain) is about
failures that the current in-memory test tooling cannot simulate in a
deterministic way. Each ticket would otherwise build its own ad-hoc fake
socket.

## Goal

Add fault injection to `rpckit.testing`, so that server tests and
generated-client tests can script failures deterministically. Users get the
same tooling for testing their own services.

Capabilities, scriptable per direction (client → server, server → client):

- **Drop the connection** after N frames, or on a predicate, with a given
  close code and reason, or abruptly with no close frame (like 1006).
- **Delay** frames by a fixed or per-frame duration.
- **Hold** frames until the test releases them. This is needed to produce
  "response arrives after timeout" without real sleeps.
- **Half-open**: frames sent by one side are silently discarded while the
  connection looks open.
- **Slow consumer**: `send` blocks until released.
- **Handshake rejection** on the next connect attempt (status or close code),
  for reconnect tests.

Read `rpckit/testing.py` first and extend the existing in-memory socket
rather than writing a parallel implementation. The generated Python client
must be able to use it through its `socket_factory` hook, which is how
reconnect tests will drive repeated connects.
The existing `InMemorySocket` is the server side of the adapter: provide a
client-side view with `send` / `recv` / `close` for `socket_factory`, without
duplicating its queues or server-specific close signature. Preserve close
codes and reasons through both views. Never emit reserved code 1006 as a
wire close frame; represent it as an abnormal disconnect.

## Acceptance criteria

- The new API is documented in `docs/transports.md` (in-memory testing
  section) and exported from `rpckit.testing`.
- Tests use `asyncio` primitives or a controllable clock, not timing-sensitive
  wall-clock sleeps. Test teardown releases held operations and leaves no
  background tasks. The clock must be injectable into code that uses it.

## Tests

- Cover each capability in `tests/test_testing.py`, including blocked-send
  cancellation, close-code propagation, and cleanup of held frames.
- Rewrite at least one existing resilience test to use the new tooling as a
  usage example, including the generated-client socket adapter.

## Out of scope

A TypeScript equivalent. TS tests can keep their own fakes.
