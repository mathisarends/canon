# 08: Notifications across reconnects

- **Status:** done — [PR #31](https://github.com/mathisarends/pyrpckit/pull/31)
- **Priority:** high
- **Area:** generated clients (Python `runtime/core.py.j2`, TS `core.ts.j2`)
- **Depends on:** 07

Everything about server-pushed messages when the connection is unreliable.

## Problems

1. **Event streams end on reconnect.** `client.subscribe(event)` and
   `client.notifications()` (connection-level events) go through
   `_notifications`, which binds to one transport. When it drops, the
   iterator raises and ends, even with `reconnect=True`. Only
   `subscribe_remote` resubscribes (the `while True` loop in
   `_subscribe_remote`).
2. **Silent gaps.** Both resubscription and any future resume path lose
   messages emitted while disconnected. Consumers are never told that a gap
   occurred, so they cannot resync.
3. **Overflow is invisible.** With `notification_overflow="drop_oldest"`
   (the default), both the transport queue and per-subscriber queues drop
   messages and warn **once**. There is no counter and no hook, so data loss
   in production goes unnoticed.
4. **Hub leak (Python).** `_hubs` is keyed by `id(transport)`. The
   `_notifications` path never removes hubs whose pump has terminated, so a
   long-lived client with many reconnects accumulates dead hubs, each holding
   its transport. `_subscribe_remote` only removes them when a subscriber
   exits. Check the TS hub map for the same problem.

## Design

- With `reconnect=True`, `subscribe()` and `notifications()` iterators
  survive reconnects: on transport failure they wait for the next transport
  and continue, as `subscribe_remote` does. Without reconnect, behaviour is
  unchanged.
- Gap signalling, opt-in so that existing iterators stay typed as payload
  streams. Pick one design and document it:
  - (a) a callback `on_gap(notification, reason)`;
  - (b) iterate an envelope type with a `gap` marker variant via a separate
    API, for example `subscribe(..., report_gaps=True)`;
  - (c) rely on the state events of ticket 07 plus documentation that every
    reconnect implies a possible gap.

  Recommended: (c) as the baseline, plus (a) for per-stream precision.
- Overflow: count dropped messages per subscriber and per transport, and
  expose the count. Python could use an `on_overflow(method, dropped)` hook
  or a `dropped` counter on the client; TS the equivalent. Keep the
  one-time warning.
- Remove hubs whose pump has terminated once their last subscriber leaves,
  or immediately when a new transport replaces them.
- Wake subscribers on replacement and terminal close before retiring a hub;
  avoid ending active iterators or creating duplicate pumps. Iterator exit
  must remove its subscriber even if transport acquisition was cancelled.
- Remote resubscriptions acquire fresh subscription ids. Do not replay an
  unsubscribe from an old connection onto the new one. No durable replay or
  exactly-once guarantee is introduced in this ticket.

## Acceptance criteria

- A `subscribe()` iterator keeps yielding after a server-side drop and
  reconnect (Python + TS).
- `subscribe_remote` keeps resubscribing as before (no regression).
- Consumers can detect that a reconnect happened during their stream.
- Dropped notifications are observable through the chosen hook or counter.
- After N reconnects, the hub map holds at most one hub per live transport.
- `docs/connections-and-events.md` documents delivery guarantees: at most
  once, gaps on reconnect, overflow behaviour.

## Tests

- Event emitted before the drop is received, then drop and reconnect, then an
  event after reconnect is received on the same iterator.
- Overflow test asserts the counter or hook.
- Reconnect 10 times and assert the hub count stays bounded.
- Several consumers reconnect together; one exits during reconnect while
  others continue. Explicit close terminates waiting iterators cleanly.
