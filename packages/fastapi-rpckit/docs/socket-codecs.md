# Socket codec extension contract

`RpcSocketCodec[Incoming, Outgoing]` separates wire messages from handler
lifecycle. Handler annotations are the sole message-type declaration. The
library passes them as `incoming=` and `outgoing=` to the codec constructor or
factory, which builds cached Pydantic adapters and output validation. The codec
declares its name, payload encoding, and allowed text/binary frame types. The
resulting instance is cached per endpoint and shared across its connections.

`RpcJsonCodec` implements direct JSON text and is inferred for typed connection
and message handlers. A connection handler injects `RpcSocket[Command, Reply |
Event]` and controls its tasks and reply counts. A message handler annotates its
message and return type for the managed one-input/one-output loop. Neither adds
a JSON-RPC envelope. Explicit `codec=RpcJsonCodec` is equivalent to the default.

Implement another codec by subclassing `RpcSocketCodec` and implementing:

- A constructor accepting keyword-only `incoming` and `outgoing` type forms.
  Forward those types to the base constructor instead of hard-coding them.
- `decode(frame)`: parse a complete wire message and validate the result with
  `self.incoming`. Return the declared incoming type.
- `encode(message)`: call `self.validate_outgoing(message)` to revalidate output
  model instances, then serialize it into `str` or `bytes` matching the declared
  frame types. `self.outgoing` provides Pydantic serialization when needed.

Both methods are synchronous. Keep codec instances stateless and safe to share;
do network I/O, request correlation, and per-connection session work in the
connection handler. The immutable configuration prevents rebinding its declared
types after registration. Do not put connection state into its adapters.

For example, a constrained integer transported as one binary byte:

```python
from typing import Annotated

from pydantic import Field
from typing_extensions import TypeForm

from fastapi_rpckit import (
    RpcChannel,
    RpcMessageType,
    RpcSocketCodec,
    RpcSocketCodecError,
    RpcSocketMessage,
)

type Byte = Annotated[int, Field(ge=0, le=255)]


class ByteCodec(RpcSocketCodec[int, int]):
    def __init__(self, *, incoming: TypeForm[int], outgoing: TypeForm[int]) -> None:
        super().__init__(
            incoming=incoming,
            outgoing=outgoing,
            name="uint8",
            encoding="uint8",
            messages=(RpcMessageType.BINARY,),
        )

    def decode(self, frame: RpcSocketMessage) -> int:
        if not isinstance(frame, bytes) or len(frame) != 1:
            raise RpcSocketCodecError("Expected one binary byte")
        return self.incoming.validate_python(frame[0], strict=True)

    def encode(self, message: int) -> bytes:
        return bytes([self.validate_outgoing(message)])


channel = RpcChannel("counter")


@channel.socket("increment", codec=ByteCodec)
async def increment(message: Byte) -> Byte:
    return message + 1
```

Sending `b"\x29"` produces `b"\x2a"`. Sending `b"\xff"` makes the handler's
response fail output validation because 256 exceeds the declared range.
A connection handler can inject `RpcSocket[Byte, Byte]` with `codec=ByteCodec`
and control when and how often it reads or sends.

For codec-specific settings, pass a callable implementing `RpcSocketCodecFactory`,
for example `codec=partial(FramedCodec, prefix=b"v1:")`. Its remaining keyword
arguments are the annotation-derived `incoming` and `outgoing` type forms. It
runs once when the endpoint is declared. Passing a constructed codec instance is
rejected; a factory that ignores or changes the supplied types is also rejected.
Direct codec construction remains useful outside endpoint declarations, such as
standalone encoding/decoding and benchmarks.

Raise `RpcSocketCodecError` for malformed wire data. Incoming Pydantic validation
errors and codec rejections close with 1002 and a fixed reason; output validation,
serialization, codec rejections, and invalid output frame types close with 1011.
Unexpected decoder exceptions follow the normal internal-error handling path.
Peer-facing error reasons do not include codec exception details or payloads.

The exported socket has directional `messages.client`/`messages.server` schemas
and `codec: {"name": "uint8", "encoding": "uint8"}`. Protocol metadata remains
independent; if provided, its encoding must match. A codec name identifies its
wire mapping, whereas encoding describes the payload representation. A JSON
envelope with a different mapping needs its own codec name even though its
encoding is still `json`. Reserve `json` for the built-in direct JSON mapping.

Client generators implement the built-in JSON mapping by default. An explicitly
selected binding can replace that client for a protocol-specific session API.
Custom codecs require an explicitly selected
[protocol binding](sockets.md#typed-protocol-clients),
which receives the unchanged transport and implements the corresponding wire
mapping. Generation fails without a matching binding, including when a custom
codec happens to use JSON. JSON codecs may also use a binding, whose transport
then bypasses generic JSON decoding. Server extension does not install a matching
client codec or infer session behavior automatically.
