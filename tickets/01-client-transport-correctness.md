# 01: Client transport correctness

- **Status:** open
- **Priority:** critical
- **Area:** generated clients (Python + TypeScript)
- **Depends on:** –

Four bugs in the generated client transports. They are all local fixes in the
same template files, so they ship together.

## 1. Late or unknown responses kill the transport (critical)

When a request times out or the caller cancels it, its id is removed from the
pending map. If the server answers afterwards, the transport treats the
response as a protocol violation, the reader dies, **every other in-flight
request fails**, and the transport closes. One slow handler takes down the
connection. `asyncio.wait_for(...)`, `TaskGroup` cancellation, and any
caller-side abort take the same path.

Reproduction (Python, verified):

```python
sock = FakeSocket()  # recv() reads from an asyncio.Queue
t = WebSocketTransport(sock, request_timeout=0.1)
await t.request("slow")  # RpcTransportError: timed out
await sock.inbox.put('{"jsonrpc":"2.0","id":1,"result":1}')
# t.closed -> RpcTransportError('Unknown JSON-RPC response ID: 1')
await t.request("fast")  # RpcTransportError: transport is closed
```

Where:

- `rpckit/codegen/templates/python/transport.py.j2` → `_resolve_response`
- `rpckit/codegen/templates/typescript/transport.ts.j2` → `#resolveResponse`
- Reference behaviour: the server already does this right in
  `rpckit/connected_client.py::_resolve` (log and drop).

Fix: validate the response envelope first, then drop a valid response whose
id is not pending, or whose future is already done. Keep failing the
transport for malformed messages (non-integer id, neither `result` nor
`error`, or both). Diagnostics must be bounded: no warning per dropped
message, and no new logger dependency for browser clients.

## 2. TypeScript client crashes on server-to-client requests (high)

Endpoints can declare client methods (`channel.client.method`), which the
server calls with string ids (`server:<n>`). The Python client answers them
with its handlers or with `method_not_found`. The TS generator ignores client
methods (`rpckit/codegen/typescript.py` never reads `client_methods`). In
`transport.ts.j2::#receive`, every message with an `id` goes to
`#resolveResponse`, which throws "JSON-RPC response IDs must be integers" for
the string id and closes the socket.

Fix: in `#receive`, treat a message with an `id` and a string `method` as a
server request and answer it with error `-32601`,
`data: {code: "method_not_found", details: {method}}`. That is exactly what
the Python client sends without a handler (see `_answer` in
`transport.py.j2`). Typed TS handlers for client methods are out of scope;
mention them as a follow-up in the PR.

## 3. Python `request()` sends outside the timeout (medium)

In `transport.py.j2::request`, `await self._socket.send(...)` runs before
`asyncio.timeout(self._request_timeout)`. Under backpressure, or on a
half-open connection, `send` can block far longer than the request timeout.

Fix: run send and wait under the same timeout. On timeout, remove the request
from `_pending` and settle or cancel its future; a racing transport failure
must not produce an unhandled-future warning. Check the socket contract for
whether cancelling a blocked send leaves it usable; if delivery or framing
is uncertain, retire the transport and document that outcome.

## 4. `_StaticTransports.close()` aborts on the first failure (low)

`runtime/core.py.j2::_StaticTransports.close` uses `asyncio.gather` without
`return_exceptions=True`. One failure makes `close()` return before all
other close operations have finished. `gather` does not automatically cancel
those operations, but callers cannot rely on cleanup being complete.

Fix: await all close operations with `return_exceptions=True`, and finalize
client state even on failure. Match `RpcTransportPool.close`'s existing
best-effort behaviour, or explicitly document and test an intentional
change to error propagation. Do not accidentally swallow caller cancellation.

## Acceptance criteria

- A response that arrives after the client timeout, or after the caller
  cancelled the request, is dropped. The transport stays open and later
  requests succeed (Python + TS).
- Malformed responses still fail the transport.
- When the server calls a client method on a TS client, the server gets
  `method_not_found`, and the TS client stays connected.
- A blocked `send` is bounded by `request_timeout`.
- Closing a multi-transport client closes every transport, even if one of
  them fails.

## Tests

- Python: transport tests with a fake socket in
  `tests/codegen/test_python_runtime.py` (late response, cancelled caller,
  blocking send, failing close).
- TS: late-response test and a client-method test (endpoint with a client
  method, server calls it after accept) in the TS test harness
  (`tests/codegen/test_typescript*.py`).
- End to end: a handler sleeps longer than the client `request_timeout`, and
  a second call on the same client still succeeds.
