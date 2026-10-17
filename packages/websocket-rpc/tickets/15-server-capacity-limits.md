# 15: Pending accounting and capacity limits

- **Status:** done
- **PR:** https://github.com/mathisarends/pyrpckit/pull/25
- **Priority:** high
- **Area:** server (`rpckit/runtime.py`, `rpckit/connection.py`), docs
- **Depends on:** –

## Problem

A batch is one task in `reader()`, so `max_pending_requests` (1024)
effectively permits up to 1024 × `max_batch_size` (32) request coroutines
per connection. Limits on concurrency and pending work are per connection;
there is no documented way to bound total work across connections.

`max_message_bytes` is checked only after `socket.receive()` returns the
complete message. It cannot prevent buffering by the underlying transport.

## Design

- Account for admitted request and notification items, including each batch
  member, rather than receive-loop tasks. Define whether executing calls
  count toward the limit; keep the definition consistent with single calls.
- Reserve capacity atomically before scheduling. Release it exactly once on
  success, rejection, cancellation, disconnect, or handler failure.
- Reject excess calls with `pending_limit`. Preserve batch response shape,
  never respond to notifications, and test mixed batches and empty/invalid
  input. Document whether admission is atomic per batch or per item.
- Responses to server-to-client calls must still bypass request admission.
  Leave a bounded control path for cancellation and heartbeat (tickets 05
  and 09) so saturation cannot prevent recovery.
- Document a worked pattern for process-wide connection and concurrency
  limits in `docs/services.md`. Use lifecycle middleware for connection
  accounting and request middleware for a shared limiter; `before_accept`
  alone has no disconnect cleanup. Include permit release on errors,
  disconnect, and cancellation, and state that multiple worker processes
  require deployment limits or coordinated accounting. A new public shared
  limiter API is out of scope for this PR.
- In `docs/transports.md`, explain how to align an ASGI/WebSocket message
  limit (for Uvicorn, `--ws-max-size` / `ws_max_size`) with
  `RpcLimits.max_message_bytes`. Verify options against the supported backend;
  do not assume every WebSocket backend supports identical limits. Cover
  assembled fragmented messages and the memory implications of queuing.

## Acceptance criteria

- A batch cannot bypass `max_pending_requests`, and counters never become
  negative or retain capacity after connection cleanup.
- Single-call overload behaviour and JSON-RPC notification semantics remain
  correct; observers and middleware retain their rejection signals.
- Docs include a usable shared-capacity example and frame-size configuration.

## Tests

- `tests/test_runtime.py`: concurrent mixed batches plus single calls with a
  small limit, using barriers to keep admitted work pending.
- Complete, fail, cancel, and disconnect admitted work; assert capacity is
  released and later calls can run.
- Verify server-to-client responses resolve even when request capacity is
  full. Exercise the documented limiter pattern with several connections.
