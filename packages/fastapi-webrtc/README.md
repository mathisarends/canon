# fastapi-webrtc

Typed WebRTC sessions for FastAPI. You declare a session like a route: its
factory is an ordinary FastAPI dependency, so authentication, path and query
parameters and `yield` cleanup work as usual. They all run before any peer
connection exists. The package exports a contract and generates a typed,
framework-free browser client from it.

```console
pip install "fastapi-webrtc[aiortc]"
```

The core depends on FastAPI, Pydantic and Starlette >=0.41. The Starlette
lower bound ensures that an admission dependency's `HTTPException` returns an
HTTP response before accepting the WebSocket. Media engines are adapters; the
`aiortc` extra installs the reference engine. Canon, RPCKit and GStreamer are
not dependencies.

## Server

```python
from typing import Annotated

from aiortc.contrib.media import MediaRelay
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel

from fastapi_webrtc import (
    DataChannelSpec,
    Direction,
    IncomingTrack,
    MediaPolicy,
    Peer,
    Session,
    WebRtcRouter,
)
from fastapi_webrtc.engines.aiortc import AiortcEngine


class Prompt(BaseModel):
    text: str


class Feedback(BaseModel):
    text: str
    words: int


def lesson_access(lesson_id: str, token: Annotated[str, Query()]) -> str:
    if token != "demo":
        raise HTTPException(status_code=403)  # HTTP 403; no peer is created.
    return lesson_id


rtc = WebRtcRouter(prefix="/rtc", engine=AiortcEngine(), max_sessions=50)


@rtc.session(
    "/lessons/{lesson_id}",
    name="practice",
    media=MediaPolicy(audio=Direction.SEND_RECEIVE),
    data_channels=(
        DataChannelSpec(name="messages", receive_model=Prompt, send_model=Feedback),
    ),
)
def practice(lesson: Annotated[str, Depends(lesson_access)]) -> Session:
    relay = MediaRelay()

    async def on_track(peer: Peer, track: IncomingTrack) -> None:
        await peer.send_track(relay.subscribe(track.native))  # Echo the microphone.

    async def on_prompt(peer: Peer, prompt: Prompt) -> None:
        await peer.send_message(
            "messages", Feedback(text=prompt.text, words=len(prompt.text.split()))
        )

    return Session(on_track=on_track, on_message={"messages": on_prompt})


app = FastAPI()
app.include_router(rtc)
```

A `Session` is assembled from handlers:

- `on_start(peer)`: runs once the transport is connected and channels are open.
- `run(peer)`: the session's main task. When it returns, the session closes normally.
- `on_track(peer, track)`: called for each incoming track. `track.recv()` or
  `async for frame in track` reads frames.
- `on_message={"channel": handler}`: validated messages per channel. Without a
  handler, a channel can be consumed with `async for message in peer.channel(name)`.
- `on_close(peer, code)`: runs before the engine releases resources.
- `tracks=[...]`: outgoing tracks. `ice_servers` overrides the router's ICE servers.

`Peer` sends with `send_message`, `send_track` and `remove_track`, which
renegotiate. It also provides `stats()`, `close(code)` and `wait_closed()`.
The session stops tracks it owns when it closes. It never stops tracks passed
with `owned=False`.

Set `role=Role.OFFERER` when the server should create the offer, for example
when the browser only watches.

## Browser client

```console
fastapi-webrtc contract --app app:app --output contract.json
fastapi-webrtc generate --contract contract.json --output src/rtc --client-name PracticeRtcClient
```

```ts
import { PracticeRtcClient, isRtcError } from "./rtc/index.js";

const client = new PracticeRtcClient({ baseUrl: "https://api.example.com" });
const microphone = await navigator.mediaDevices.getUserMedia({ audio: true });

const session = await client.practice.connect({
  lessonId: "greetings", // path parameter
  token: "demo", // query parameter
  tracks: microphone, // borrowed: never stopped by the session
  timeoutMs: 10_000,
  onTrack: ({ track }) => {
    audio.srcObject = new MediaStream([track]);
  },
  onMessage: { messages: (feedback) => console.log(feedback.words) },
});

await session.channels.messages.send({ text: "hello" }); // typed as Prompt
await session.close(); // idempotent
```

`timeoutMs` limits connection setup, including asynchronous credential providers,
and stops applying once the session is ready. Use `signal` for cancellation of
the session's entire lifetime: aborting it also closes an already running audio
or video session. An `AbortSignal.timeout(...)` therefore ends the session when
its timer expires, even if connection setup already succeeded.

Later renegotiations, including `addTrack()` and `removeTrack()`, use the
server's `negotiation_timeout_ms` and end the session with `negotiation_timeout`
if they cannot complete. Channel sends wait at most `sendTimeoutMs` (10 seconds
by default) for opening or buffer drainage before ending with `slow_consumer`.
Permanent peer-connection failure rejects pending operations with `transport_lost`.

Failures are `RtcError`s with a stable `code`, such as `session_limit`,
`negotiation_timeout`, `media_rejected` or `transport_lost`. Browsers do not
expose the HTTP status of a refused WebSocket handshake. A session denied by a
dependency therefore fails with `connection_failed`. The full list of codes is
in [the protocol](docs/protocol.md#close-codes).

Both commands accept `--check`, which fails on drift without writing.
Generated directories contain a manifest. Stale generated files are removed;
files you add yourself are kept.

Configure shared credentials with `new PracticeRtcClient({ query: async () =>
({ token: await refreshToken() }) })`. The provider runs for every connection.
Query values are merged in this order, with later sources taking precedence:
the `baseUrl` query string, `client.config.query`, `connect({ query: ... })`, then
named connect parameters such as `connect({ lessonId: "greetings", token: "new" })`.
Use wire aliases as keys inside query maps. An omitted named parameter preserves
shared values; `null` explicitly removes a query value. Required query parameters
are checked after merging. Generated query fields are optional so shared
credentials can supply them; required path parameters must still be passed.

## Security

Session admission is ordinary FastAPI dependency code, so authorization stays in
your application. Two WebSocket properties need attention:

- **Origins.** CORS does not apply to WebSocket handshakes, and browsers attach
  cookies to cross-site handshakes. If admission relies on cookies, pass
  `WebRtcRouter(allowed_origins=["https://app.example.com"])`. Handshakes from
  other origins are refused with HTTP 403 before the session factory runs.
  Requests without an `Origin` header come from non-browser clients and are not
  restricted by this check.
- **Query tokens.** Browsers cannot set headers on a WebSocket, so tokens travel
  in the URL. URLs can appear in proxy and server access logs. Prefer short-lived,
  single-use session tickets issued by an authenticated HTTP endpoint over
  long-lived access tokens, and supply them through the client's `query` provider.

## Limits and ICE

`SessionLimits` bounds negotiation time, pending candidates, signaling and
message sizes, inbound queues and send buffers. It also sets grace periods for
transport and signaling loss. Every limit has a categorized error.
`TurnRestCredentials` issues time-limited TURN REST credentials per user. It can
give the server-side engine internal relay URLs.

## Documentation

- [Signaling protocol](docs/protocol.md)
- [Canon composition and Dishka session/message scopes](docs/canon-dishka.md)
- [Changelog](CHANGELOG.md)
- Runnable example: [`examples/practice`](examples/practice). Its generated
  client is in `examples/practice/client`.

The engine interface abstracts signaling and lifecycle. Native outgoing tracks
and received frames remain engine-specific: aiortc uses `MediaStreamTrack` and
PyAV frames. Its statistics return `jitter_seconds=None` because the public
report does not identify the per-stream codec clock rate needed for conversion.

Generated TypeScript models provide compile-time message types; the browser
runtime checks formats and sizes but does not enforce every JSON Schema rule.
Server-side Pydantic adapters validate incoming and outgoing typed messages.
