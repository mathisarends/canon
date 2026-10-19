# Socket codec extension contract

`RpcSocketCodec[Incoming, Outgoing]` separates wire messages from handler
lifecycle. Its named constructor arguments define the server's incoming and
outgoing types, cached Pydantic adapters, codec name, payload encoding, and
allowed text/binary frame types. These are the same definitions used for
contract schemas. The instance is reusable across connections and handler styles.

`RpcJsonCodec(incoming=Command, outgoing=Reply | Event)` implements the normal
JSON text case. Use it with a typed connection handler to send unsolicited events
or manage independent producer tasks, or with a message handler for the managed
one-input/one-output loop. Neither codec nor handler creates a JSON-RPC envelope.

Implement another codec by subclassing `RpcSocketCodec` and implementing:

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

from fastapi_rpckit import (
    RpcChannel,
    RpcMessageType,
    RpcSocketCodec,
    RpcSocketCodecError,
    RpcSocketMessage,
)

type Byte = Annotated[int, Field(ge=0, le=255)]


class ByteCodec(RpcSocketCodec[Byte, Byte]):
    def __init__(self) -> None:
        super().__init__(
            incoming=Byte,
            outgoing=Byte,
            name="uint8",
            encoding="uint8",
            messages=(RpcMessageType.BINARY,),
        )

    def decode(self, frame: RpcSocketMessage) -> Byte:
        if not isinstance(frame, bytes) or len(frame) != 1:
            raise RpcSocketCodecError("Expected one binary byte")
        return self.incoming.validate_python(frame[0], strict=True)

    def encode(self, message: Byte) -> bytes:
        return bytes([self.validate_outgoing(message)])


channel = RpcChannel("counter")
BYTE = ByteCodec()


@channel.socket("increment", codec=BYTE)
async def increment(message: Byte) -> Byte:
    return message + 1
```

Sending `b"\x29"` produces `b"\x2a"`. Sending `b"\xff"` makes the handler's
response fail output validation because 256 exceeds the declared range.
A connection handler can inject `RpcSocket[Byte, Byte]` with the same `codec=BYTE`
and control when and how often it reads or sends.

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
