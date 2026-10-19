# Sockets

A socket is a WebSocket endpoint that carries its messages unchanged.
fastapi_rpckit owns acceptance, dependencies, limits, cancellation, and closure, and
passes every text and binary message through without JSON parsing, JSON-RPC
envelopes, or framing. Use it to proxy a native protocol such as the Chrome
DevTools Protocol (CDP), whose existing clients must keep speaking their own
wire format.

Use a [binary stream](streams.md) when you control the protocol and only move
bytes. Use a socket when the messages belong to someone else's protocol,
or when text and binary messages must keep their type.

## Declare and mount a socket

```python
import asyncio

from fastapi_rpckit import (
    Inject,
    RpcChannel,
    RpcErrorBinding,
    RpcSocket,
    RpcRejection,
    RpcService,
)


class BrowserNotFound(Exception): ...


class CdpUnavailable(Exception): ...


UNKNOWN_BROWSER = RpcErrorBinding(
    BrowserNotFound, rejection=RpcRejection.NOT_FOUND, message="Unknown browser"
)
CDP_UNAVAILABLE = RpcErrorBinding(
    CdpUnavailable,
    rejection=RpcRejection.INTERNAL_ERROR,
    message="Browser CDP unavailable",
)

browser = RpcChannel("browser")


@browser.socket("cdp", closes=(UNKNOWN_BROWSER, CDP_UNAVAILABLE))
async def cdp(socket: Inject[RpcSocket], browsers: Inject[BrowserService]) -> None:
    async with browsers.connect_page_cdp() as upstream:

        async def to_upstream() -> None:
            async for message in socket:
                await upstream.send(message)

        async with asyncio.TaskGroup() as group:
            forwarding = group.create_task(to_upstream())
            async for message in upstream:
                await socket.send(message)
            forwarding.cancel()


app = RpcService()
app.socket("/browser/cdp", cdp)
```

The handler is an async function that returns `None` and injects
`RpcSocket` exactly once. Its operation name is `browser.cdp`, and the
mounted path becomes its own WebSocket endpoint. Handler parameters without
`Inject[...]` are path variables, validated before the handshake is accepted,
exactly as for [binary streams](streams.md#path-variables).

`RpcService.socket()` mounts both kinds of WebSocket endpoint. With
`channels=...` it serves rpckit's managed JSON-RPC protocol. With a handler
decorated by `@channel.socket()` it serves a socket whose messages belong to
the handler. JSON-RPC-only options such as `error_mapper=`, `path_model=`, and
`close_when_events_complete=` are rejected for socket handlers.

`messages=` declares the accepted message types and defaults to
`(RpcMessageType.TEXT, RpcMessageType.BINARY)`. fastapi_rpckit closes the socket with
a protocol error (1002) when the client sends an undeclared type, and
`send()` raises `TypeError` for one.

## Declare the protocol

A socket is the transport; the messages it carries follow an application
protocol. Declare that protocol with `protocol=` so the contract and generated
clients know what the endpoint speaks:

```python
from fastapi_rpckit import RpcMessageType, RpcSocketProtocol

CDP = RpcSocketProtocol(
    name="cdp",
    version="1.3",
    schemas=(
        "https://raw.githubusercontent.com/ChromeDevTools/devtools-protocol/master/json/browser_protocol.json",
        "https://raw.githubusercontent.com/ChromeDevTools/devtools-protocol/master/json/js_protocol.json",
    ),
)


@browser.socket("cdp", protocol=CDP, messages=(RpcMessageType.TEXT,))
async def cdp(socket: Inject[RpcSocket], browsers: Inject[BrowserService]) -> None: ...
```

The declaration is metadata only. fastapi_rpckit does not decode, validate,
correlate, or rewrite the messages: a CDP endpoint stays a CDP endpoint and
forwards `{"id": 1, "method": "Page.enable", "params": {}}` byte for byte.
Request correlation, events, and target sessions remain the job of the
protocol's client. The handler can read the declaration as `socket.protocol`.

`RpcSocketProtocol` describes any protocol:

```python
from fastapi_rpckit import RpcSocketProtocol

GRAPHQL_WS = RpcSocketProtocol(
    name="graphql-transport-ws",
    version="5",
    encoding="json",
    schemas=("schemas/graphql-ws.json",),
)
```

| Field | Meaning |
|---|---|
| `name` | Lowercase protocol identifier; generators select client bindings by it |
| `version` | The protocol's own version, independent of server or browser versions |
| `encoding` | Payload encoding, such as `json`; defaults to `json` |
| `schemas` | URI references to the specification, which may span several files |

Absolute schema URIs are used as written. Relative references resolve against
the location of the exported contract document, like OpenAPI `$ref` values, so
`schemas/graphql-ws.json` next to `contract.openrpc.json` stays valid when both
files move together.

fastapi_rpckit ships no protocol-specific declarations; the protocol belongs
to the application. The [CDP example](../examples/cdp/README.md) declares the
Chrome DevTools Protocol and binds it to typed Python and TypeScript clients.

## Send and receive

`receive()` and iteration return `str` for text messages and `bytes` for
binary messages. `send()` sends a `str` as text and bytes-like values as
binary, and waits while the socket applies backpressure. Messages are
delivered as-is, including empty ones.

Incoming messages wait in a queue that holds up to `RpcLimits.max_queue_size`
messages. When the handler falls behind, fastapi_rpckit stops reading from the socket.
A message larger than `RpcLimits.max_message_bytes` closes the socket with
1009. A send that blocks longer than `RpcLimits.send_timeout` closes it with
1008 (`Client too slow`).

## Lifecycle and closure

fastapi_rpckit accepts the connection before the handler runs; do not accept it again.
Failures before acceptance, in `before_accept` or in a FastAPI context
dependency, reject the handshake through the endpoint's `rejects=` and the
service's or router's rejections, as for every other endpoint.

After acceptance, the socket closes as follows:

| Situation | Close |
|---|---|
| The handler returns | 1000 |
| `await socket.close(code, reason=...)` | the given code and reason |
| An exception bound in `closes=` | the binding's rejection and message |
| An exception mapped by `rejects=` or rejections | the mapped rejection |
| Any other exception | 1011 `Internal error` |

Exceptions raised inside an `asyncio.TaskGroup` are unwrapped, so an upstream
failure in a forwarding task maps like one raised directly. Dependencies that
fail while the handler's arguments are resolved, after acceptance, use the same
mapping. Messages of unmapped exceptions never reach the client; they may
contain upstream credentials. To replace the generic reason, bind `Exception`
itself as the fallback:

```python
RpcErrorBinding(
    Exception,
    code="cdp_unavailable",
    rejection=RpcRejection.INTERNAL_ERROR,
    message="Browser CDP unavailable",
)
```

A rejection becomes its close code: `UNAUTHORIZED`, `FORBIDDEN`, and
`NOT_FOUND` close with 1008, `PROTOCOL_ERROR` with 1002, `UNAVAILABLE` with
1013, and `INTERNAL_ERROR` with 1011.

When the client disconnects, the connection closes, or the server shuts down,
fastapi_rpckit cancels the handler. Its `finally` blocks and context managers run, so
`async with` releases upstream connections and forwarding tasks. Requesting a
close with `socket.close()` also cancels the handler at its next `await`.

## FastAPI and dependencies

Socket endpoints mount like any other endpoint, with `create_router()` or
`RpcRoutes.mount()`. The route's context function, `rejects=`, rejections,
middleware, and a Dishka resolver apply unchanged:

```python
routes = RpcRoutes(router, context=open_session, resolver=Dishka())
routes.mount(app.endpoint("cdp"))
```

Connection middleware sees sockets as connections. Every
message increments the `stream_frame_sent` and `stream_frame_received`
callbacks, so the OpenTelemetry `fastapi_rpckit.stream.frames` and
`fastapi_rpckit.stream.bytes` counters include them. Sockets do not open a
`stream` middleware scope.

To test a socket without a server, use `RpcTestClient` with
`send_message()` and `next_message()`.

## Contract and generated clients

Sockets are not JSON-RPC methods. The contract lists them in
`x-rpckit-sockets` with their URL, URL variables, message types,
subprotocols, declared close outcomes, and declared protocol:

```json
{
  "name": "browser.cdp",
  "url": "wss://{host}/browser/cdp",
  "messageTypes": ["text"],
  "variables": {"host": {"default": "api.example.com"}},
  "closes": [
    {"code": 1008, "x-rpckit-code": "browser_not_found", "reason": "Unknown browser"}
  ],
  "x-rpckit-protocol": {
    "name": "cdp",
    "version": "1.3",
    "encoding": "json",
    "schemas": [
      "https://raw.githubusercontent.com/ChromeDevTools/devtools-protocol/master/json/browser_protocol.json",
      "https://raw.githubusercontent.com/ChromeDevTools/devtools-protocol/master/json/js_protocol.json"
    ]
  }
}
```

Generated clients keep the declaration as `endpoint.protocol`
(`SocketProtocol` in both languages), so code holding a generic socket can
tell which protocol it speaks.

A close code and reason do not identify a domain exception or carry
structured details. Generated clients therefore raise transport errors for
them. Errors inside the proxied protocol, such as CDP command errors, pass
through as ordinary messages.

Both generators place a socket on the namespace tree of its name:

```python
async with AutomationClient.connect(host="api.example.com") as client:
    async with client.browser.cdp() as socket:
        await socket.send('{"id": 1, "method": "Page.enable"}')
        async for message in socket:
            ...  # str for text, bytes for binary
```

```ts
await using client = await AutomationClient.connect({ host: "api.example.com" });
await using socket = await client.browser.cdp();
await socket.send(JSON.stringify({ id: 1, method: "Page.enable" }));
for await (const message of socket) {
  // string for text, ArrayBuffer for binary
}
```

Leaving the block closes the socket. Iteration ends when the server closes
normally; `receive()` then raises `RpcStreamClosed`. Other close codes raise
`RpcStreamFailed` with `code` and `reason`, and 1008 raises
`RpcStreamRefused`. A rejected handshake fails before a socket exists: Python
raises the `websockets` handshake error, TypeScript rejects with an `Error`.

`connect()` accepts `socket_connection_factory` (`socketConnectionFactory` and
`socketQueueSize` in TypeScript) to customize the socket. Clients built
with `with_transports()` take a `socket_opener` / `socketOpener`;
without one, opening a socket raises `RpcStreamsUnavailableError`.
Request correlation, sessions, reconnection, and replay stay with the
protocol's own client library, such as an existing CDP client.

[Back to documentation](README.md)
