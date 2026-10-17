# 07: Reconnect policy and connection state

- **Status:** done — [PR #30](https://github.com/mathisarends/pyrpckit/pull/30)
- **Priority:** high
- **Area:** generated clients (Python `runtime/connection.py.j2`,
  `client.py.j2`; TS `core.ts.j2`, `client.ts.j2`)
- **Depends on:** 04

## Problems

1. **Permanent rejections are retried forever.** `RpcTransportPool.get`
   (Python, `except Exception:` in the connect loop) and `#connect` (TS)
   retry every connect failure, including 401/403/404 handshake rejections.
   With an expired token, the user only ever sees "Could not connect within
   the request timeout". The real cause never surfaces.
2. **No jitter.** The backoff is `delay * 2` capped at `reconnect_max_delay`
   with no randomness. After a deploy, every client reconnects in lockstep (a
   thundering herd).
3. **No attempt limit.** Reconnect loops until the client is closed. No
   give-up, no terminal state.
4. **No state visibility.** Applications cannot observe "disconnected /
   reconnecting / connected again". UIs need it for a "Reconnecting…"
   indicator, and apps need it to resync state after a gap.
5. **`client.closed` semantics.** `RpcTransportPool._transport_closed`
   resolves the pool's `closed` future on the **first** transport drop, even
   when `reconnect=True` will recover. Code awaiting `client.closed` to
   detect "client is dead" fires on a transient blip. Verify the intended
   semantics in tests and docs, then make them consistent.

## Design

- Classify connect failures with `RpcConnectError.permanent` from ticket 04.
  Permanent failures are not retried: they fail pending `get()` calls
  immediately with the real error, and move the client to the terminal state.
  Make the classification overridable, for example
  `reconnect_should_retry: Callable[[Exception], bool]`.
- Full-jitter backoff: `sleep = random.uniform(0, min(max_delay, initial * 2**n))`
  (same in TS), with the seed or random source injectable for tests.
  Cap the running delay before doubling so long outages do not overflow.
- `reconnect_max_attempts: int | None = None`. When it is exhausted, the
  client enters the terminal state with the last error.
- Connection state:
  - Python: `client.state` (enum: `connecting`, `connected`, `reconnecting`,
    `closed`) and callbacks `on_disconnect(error)`, `on_reconnect()` (or a
    single `on_state_change(state, error)`) passed to `connect(...)`. Keep it
    small and consistent with existing parameter naming.
  - TS: the same, as options plus an `onStateChange` listener.
- `client.closed` resolves only when the client is terminally closed:
  explicit `close()`, a permanent failure, or attempts exhausted. With
  `reconnect=False` the behaviour is unchanged (the first drop is terminal).
  Document this in `docs/clients.md`.
- The headers callable is already re-invoked per connect (good for token
  refresh). Keep that and add a test for it.
- Define state and callbacks per server in multi-endpoint clients, plus how
  aggregate `client.closed` behaves if one server becomes terminal. A
  server's reconnect must not replace another server's live transport.
- Specify whether initial connect failures are retried and whether reconnect
  is lazy (on next use) or proactive. Notification-only subscribers must be
  able to trigger recovery without issuing a separate request.
- Use one connect attempt per server shared by concurrent waiters. Bound
  connect, lock wait, and backoff by the caller's remaining deadline;
  cancelling one waiter must not corrupt other callers. Explicit close
  interrupts connect/backoff and prevents subsequent state changes.
- Define close-code classification together with 11 and 12: 1001/1012/1013
  are transient; general policy rejection remains terminal by default, with
  a narrowly identifiable credential-expiry exception. A caller's explicit
  close never triggers reconnect. Callback failures must not break cleanup.

## Acceptance criteria

- Reconnect after a 401/403 handshake rejection stops immediately and
  surfaces `RpcConnectError(permanent=True)` to waiting callers.
- Backoff delays are jittered within bounds (test with an injected random
  source).
- `reconnect_max_attempts` is respected.
- State callbacks fire in order: disconnect, then reconnect (or then closed).
- `client.closed` does not resolve on a transient drop when `reconnect=True`.
- Python and TS behave the same.

## Tests

Use the fault-injecting sockets from ticket 03 if available:

- server drops the connection, client reconnects, state callbacks fire,
  `closed` stays pending;
- next handshake rejected with 401, no retry, error surfaced;
- the headers callable is invoked again on reconnect;
- attempts exhausted, terminal state, `closed` resolved with the last
  error.
- Concurrent waiters, cancellation during connect, close during backoff,
  and independent state transitions for two configured servers.
