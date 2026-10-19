# Sockets

A socket is a WebSocket endpoint. Its transport, message codec, application
protocol, and handler lifecycle are separate choices. Inject `RpcSocket` for raw
text/binary, `RpcSocket[Incoming, Outgoing]` for a validated connection, or use a
message handler whose parameter and return annotations describe its messages.
Typed annotations infer JSON. Optional `incoming=` and `outgoing=` models override
each direction's inferred contract; `codec=` selects another codec class or factory.
See [connection codecs](#connection-codecs) and [typed JSON messages](#typed-json-messages).

For an untyped socket,
fastapi_rpckit owns acceptance, dependencies, limits, cancellation, and closure, and
passes every text and binary message through without JSON parsing, JSON-RPC
envelopes, or framing. Use it to proxy a native protocol such as the Chrome
DevTools Protocol (CDP), whose existing clients must keep speaking their own
wire format.

Use a [binary stream](streams.md) when you control the protocol and only move
bytes. Use a socket when the messages belong to someone else's protocol,
or when text and binary messages must keep their type.

## Typed JSON messages

Declare the incoming message as a parameter and the outgoing response as the
return type. The library owns the receive loop and sends one response for each
message, in order:

```python
from pydantic import BaseModel, ConfigDict

from fastapi_rpckit import RpcChannel, RpcService


class Ping(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: int


class Pong(BaseModel):
    value: int


channel = RpcChannel("messages")


@channel.socket("ping")
async def ping(message: Ping) -> Pong:
    return Pong(value=message.value + 1)


service = RpcService()
service.socket("/messages/ping", ping)
```

The first parameter without `Inject[...]` is the incoming message; its name is
not significant. Further non-injected parameters are path variables. Each message
direction needs an annotation or an explicit decorator model. Path parameters
still require annotations. Injected dependencies are resolved in a
fresh invocation scope per message, within the existing connection scope. The
scope stays open through response validation and sending, and is released on
completion, failure, or disconnect. Calls are sequential on each connection.
A `None` return annotation sends JSON `null`; it does not suppress the response.
An explicit `codec=SomeCodec` can replace JSON, including with a binary codec.
The class or factory receives the resolved `incoming=` and `outgoing=` types.
Annotations supply the defaults, so a second message-type declaration is optional.

### Explicit message models

Use `outgoing=` like FastAPI's `response_model`: it defines output validation,
serialization, exported schema, and generated SDK types, independently of the
handler's implementation return annotation. The handler can return a normal
dictionary:

```python
@channel.socket("ping", outgoing=Pong)
async def ping(message: Ping) -> dict[str, int]:
    return {"value": message.value + 1}
```

Input is still inferred from `message: Ping`. Outgoing values undergo strict
Pydantic validation against `Pong`; extra fields are ignored, retained, or rejected
according to its model configuration. Serialization uses the declared output
schema, including when the implementation returns a model subclass.

Both models can live on the decorator:

```python
@channel.socket("ping", incoming=Ping, outgoing=Pong)
async def ping(message):
    return {"value": message.value + 1}
```

The handler receives a validated `Ping`. Python type checkers cannot infer its
type from decorator arguments; annotate it as `Ping` if you want IDE checking,
or use `Any` or omit the annotation for a decorator-only declaration. A concrete
received annotation must match `incoming=` so it describes the object actually
passed to the handler. Conflicts fail at endpoint declaration.

Each explicit direction takes precedence; the other direction still uses its
annotation. `outgoing=` allows omitting a message handler's return annotation.
Explicit `incoming=None` or `outgoing=None` declares JSON `null`, rather than
disabling validation.

### Validation and client contracts

Incoming text is parsed and validated once with a cached Pydantic adapter in
strict mode, before entering the socket queue or calling the handler. Set
`extra="forbid"` on models to reject unknown fields. Pydantic constraints,
unions, discriminators, aliases,
and validators apply, including annotated type aliases. The inferred JSON codec
uses text frames. Explicit codecs declare their own framing and encoding; these
must agree with `messages=` and any declared protocol encoding.

Invalid incoming messages close with 1002, `Invalid incoming socket message`.
Invalid outgoing values close with 1011, `Invalid outgoing socket message`.
Validation failures do not expose payloads, Pydantic error details, or validator
exception messages to the peer. Closure cancels the handler and releases its
dependencies as for untyped sockets. Normal disconnect, message-size limits,
backpressure, and shutdown still apply.

Outgoing values are revalidated, including existing or mutated model instances,
then serialized once. Serialization aliases and custom serializers apply.
Adapters are built at declaration time, not for each message. This validates
message structure; it does not correlate request IDs or track protocol sessions.
For unsolicited messages, multiple responses per input, or an independent
receive/send loop, use a [connection codec](#connection-codecs). Both handler
styles use the same receive validation and send serialization. A connection
handler continues to return `None` and owns all of its messages.

The contract exports `messages.client` and `messages.server` as component schema
references on the socket entry. Input schemas use Pydantic's validation mode and
output schemas use serialization mode. These direction names are independent of
whether the contract is being read by the server or a client.
The socket's `codec` object records its codec `name` and payload `encoding`.

Generated clients keep the same socket lifecycle and reverse the message roles:

```python
async with client.messages.ping() as socket:
    await socket.send(Ping(value=41))
    response = await socket.receive()  # Pong
```

```typescript
await using socket = await client.messages.ping();
await socket.send({ value: 41 });
const response = await socket.receive(); // Pong
```

The returned type is `Socket[Pong, Ping]` in Python and `Socket<Pong, Ping>` in
TypeScript: received first, sent second in both languages. Python validates with
the generated Pydantic models, subject to the existing generator's schema support;
application-only custom validators are not copied into the SDK. TypeScript emits
static payload types and handles JSON encoding/decoding; it does not provide full
runtime schema validation. Server validation remains authoritative in both cases.

`protocol=RpcSocketProtocol(...)` remains optional metadata. Schema URLs alone
do not enable validation or generate models from foreign specifications. To type
CDP, generate or import suitable Pydantic command/response/event types first.
The built-in JSON codec uses generated typed message sockets by default. A
selected protocol binding takes precedence and gets the original wire transport,
including for a JSON codec, so the binding owns client-side decoding and session
behavior. Other codecs require a binding: generators reject an unknown codec
without one rather than guessing JSON from its encoding. Bound sockets are never
also decoded by the generic JSON client.

The [typed socket example](../examples/typed_socket/README.md) includes both
generated clients and tests against a real WebSocket server.

Measure codec CPU cost locally with:

```console
uv run --locked --directory packages/fastapi-rpckit python scripts/bench_socket_messages.py
```

The benchmark reports cached input validation and output validation/serialization
for small and 64 KiB messages, plus adapter construction and standard-library JSON
comparisons. It excludes connection handling, queues, dependency scopes, network,
and application code; it is not an end-to-end latency measurement.

## Connection codecs

By default, the handler annotation defines message types for validation,
contract schemas, SDK generation, and static checking. JSON needs no separate
codec declaration:

```python
from fastapi_rpckit import Inject, RpcSocket

type PingSocket = RpcSocket[Ping, Pong]


@channel.socket("session")
async def session(socket: Inject[PingSocket]) -> None:
    await socket.send(Pong(value=0))  # An unsolicited initial message.
    async for message in socket:
        await socket.send(Pong(value=message.value))
        await socket.send(Pong(value=message.value + 1))


@channel.socket("reply")
async def reply(message: Ping) -> Pong:
    return Pong(value=message.value + 1)
```

The connection handler runs once per connection, with one dependency scope until
it exits. It controls its own tasks, subscriptions, message timing, and reply
counts. `receive()` returns `Ping`; `send()` accepts `Pong`. Malformed input is
rejected before it reaches the queue, and output is validated before writing.
Limits, backpressure, send locking, cancellation, and cleanup still apply.

The socket type arguments are **received, sent**, from the handler's perspective.
The library derives a JSON codec from this same annotation, including through a
type alias. Use shared aliases for complex unions instead of repeating schemas.
For a custom wire mapping, pass its class or a configured factory as `codec=`;
the factory receives the resolved types once at endpoint declaration. Preconfigured
codec instances are rejected, and a factory returning different message types
fails declaration instead of drifting from the static contract.
The handler can inspect `socket.codec` and `socket.protocol` independently.

Connection handlers also accept decorator models. Keep concrete socket type
arguments equal to the corresponding models, or use `Any` for a direction whose
schema is declared only on the decorator. For example, infer the received type
while validating dictionary sends against an explicit outgoing model:

```python
from typing import Any


@channel.socket("session", outgoing=Pong)
async def session(socket: Inject[RpcSocket[Ping, Any]]) -> None:
    async for message in socket:  # Ping, including in the IDE.
        await socket.send({"value": message.value + 1})
```

For both models on the decorator use `RpcSocket[Any, Any]`. Runtime validation
and SDK types still follow the declared models, while `Any` honestly marks the
handler's weaker static typing. Bare `RpcSocket` has raw text/binary static types
and therefore rejects codec/model options; use the generic form for validation.

Bare `Inject[RpcSocket]` retains unchanged text/binary semantics and
does no JSON parsing. `protocol=...` remains optional metadata in both modes.
Neither mode adds a JSON-RPC envelope or implements request correlation, CDP
sessions, event routing, or automatic imports from schema URLs.

See [custom codecs](socket-codecs.md) for the extension contract and a binary
example. A custom codec can be used with either handler style; there is no
registry of supported application protocols in the server.

## Declare and mount an untyped socket

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
to the application. [Typed protocol clients](#typed-protocol-clients) shows how
generated clients can speak it.

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

## Typed protocol clients

A protocol binding replaces the generic socket with a typed session for every
socket that declares its protocol. fastapi_rpckit ships no bindings; the
generators only provide the extension point in
`fastapi_rpckit.codegen.bindings`:

```python
from fastapi_rpckit.codegen.bindings import BindingContext, SocketBinding


class CalcBinding:
    protocol = "calc"

    def bind(self, context: BindingContext) -> SocketBinding:
        if context.language == "python":
            return SocketBinding("calc", PYTHON_SOURCE, "open_calc", "CalcSession")
        return SocketBinding("calc", TYPESCRIPT_SOURCE, "openCalc", "CalcSession")


BINDING = CalcBinding()
```

The generator writes `source` to `bindings/<module>` of the client and imports
`open` and `session` from it. The socket method then returns the session:

| Language | `open` receives | The socket method returns |
|---|---|---|
| Python | `AbstractAsyncContextManager[Socket]` | `AbstractAsyncContextManager[session]` from `open` |
| TypeScript | the opened `Socket` | `Promise<session>`; `open` may return the session or a promise of it |

`BindingContext` carries the language, the declarations of the protocol in the
contract, and `schemas()`, which resolves relative schema references against
the contract file. A binding can read those schemas to generate typed commands.
Install any packages imported by the binding's emitted source in the consuming
application. The generator does not manage the application's dependencies.

Select bindings per client in the generator config, or with `--binding`:

```toml
[[clients]]
language = "python"
output = "python/calc_client"
bindings = ["calc_binding:BINDING"]
```

A `module:attr` reference resolves next to the config file. A bare name looks
up the `fastapi_rpckit.socket_bindings` entry point group, so a binding package
can register itself and be selected as `bindings = ["cdp"]`. A binding whose
protocol no socket declares, or two bindings for one protocol, fail generation.
Sockets whose protocol has no binding keep the generic `Socket`.

The [socket protocol example](../examples/socket_protocol/README.md) binds a
small CDP-shaped protocol in both languages and runs both clients against a
live server. A CDP binding has the same shape: in Python it wraps an existing
CDP client such as cdpify around the socket, and in TypeScript it types
commands and events with the `devtools-protocol` package.

[Back to documentation](README.md)
