# 02: Server input hardening

- **Status:** done
- **PR:** https://github.com/mathisarends/pyrpckit/pull/24
- **Priority:** high
- **Area:** server (`rpckit/codec.py`, `rpckit/runtime.py`,
  `rpckit/connected_client.py`, `rpckit/server.py`), Python client decoder
- **Depends on:** –

Things a misbehaving or hostile client can do to a server today. They all
belong to the same theme: untrusted input must not cause internal errors,
or log floods. Capacity accounting and deployment limits are ticket 15.

## 1. Deeply nested JSON escapes parse-error handling (high)

`RpcCodec.decode` only catches `UnicodeDecodeError` and `JSONDecodeError`.
`"[" * 100_000` is 100 KB, well under the default 1 MiB
`max_message_bytes`, and makes `json.loads` raise `RecursionError`
(verified).

- `_serve_endpoint`'s reader falls into its generic `except Exception`. It
  closes the connection with `INTERNAL_ERROR` and records an error, so any
  client can trigger internal-error alerts at will.
- `RpcServer.handle_json`, used by custom transports, lets the
  `RecursionError` escape to the adapter.
- The Python client template `_decode` has the same gap.

Fix:

- Map `RecursionError` to `RpcParseError` in `RpcCodec.decode`, and to
  `RpcTransportError` in the client `_decode` (`transport.py.j2`).
- Check that pydantic validation of very deep params (`dict[str, Any]`,
  recursive models) raises nothing other than `ValidationError`. If it does,
  map that to `invalid_params`.

## 2. Client-triggerable log flooding (low)

The server logs one warning per offending message:

- `runtime.py::reject_pending`: "RPC client exceeded max_pending_requests"
- `connected_client.py::_resolve`: "Dropped a response to unknown
  client_method id"

A client can produce unbounded log volume.

Fix: log at most once per connection at `warning`, plus an aggregate count
at `debug`, or rate-limit per connection. Moving every message to `debug`
alone does not bound volume when debug logging is enabled. Do not drop the
observer/middleware signals. Keep counters scoped to a live connection.

## Acceptance criteria

- A deeply nested frame yields a `parse_error` (-32700) response. The
  connection stays open, and nothing is logged at `error` or `exception`
  level.
- `handle_json` returns an encoded parse-error response for such input.
- Flooding with over-limit requests or bogus client-method responses
  produces a bounded number of log lines per connection.
- The Python generated client turns deeply nested JSON into a controlled
  transport failure and settles all pending calls cleanly.

## Tests

- `tests/test_codec.py`: `decode("[" * 100_000)` raises `RpcParseError`.
- `tests/test_runtime.py`: send the nested frame and assert a parse-error
  response and that the next valid request succeeds. Log-flood test with
  `caplog`, including when debug logging is enabled.
- `tests/test_server.py`: `handle_json` with the nested frame.
- `tests/codegen/test_python_runtime.py`: nested response closes cleanly
  with a client error, with no raw `RecursionError` or leaked futures.
