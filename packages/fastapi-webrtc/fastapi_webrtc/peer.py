"""Public handles passed to session handlers."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from fastapi_webrtc.engine import ConnectionStats, EngineSender, EngineTrack, MediaKind
from fastapi_webrtc.errors import ErrorCode

if TYPE_CHECKING:
    from fastapi_webrtc.declarations import DataChannelSpec
    from fastapi_webrtc.runtime import SessionRuntime, _Channel


class IncomingTrack:
    """A remote audio or video track.

    ``recv()`` returns frames in the engine's native type (for the aiortc engine,
    ``av.AudioFrame``/``av.VideoFrame``). ``native`` exposes the engine track for
    engine-specific consumers such as recorders or relays. The session owns the
    track: it is stopped during cleanup and must not be used afterwards.

    When a session has no ``on_track`` handler, the runtime consumes and discards
    frames so that unread media cannot accumulate.
    """

    def __init__(self, track: EngineTrack) -> None:
        self._track = track
        self._ended = asyncio.Event()
        track.on_ended(self._ended.set)

    @property
    def id(self) -> str:
        return self._track.id

    @property
    def kind(self) -> MediaKind:
        return self._track.kind

    @property
    def native(self) -> Any:
        return self._track.native

    @property
    def ended(self) -> bool:
        return self._ended.is_set()

    async def recv(self) -> Any:
        return await self._track.recv()

    async def wait_ended(self) -> None:
        await self._ended.wait()

    def __aiter__(self) -> AsyncIterator[Any]:
        return self._frames()

    async def _frames(self) -> AsyncIterator[Any]:
        while not self._ended.is_set():
            try:
                frame = await self._track.recv()
            except Exception:
                if self._ended.is_set():
                    return
                raise
            yield frame

    def _stop(self) -> None:
        self._track.stop()
        self._ended.set()

    def __repr__(self) -> str:
        return f"IncomingTrack(id={self.id!r}, kind={self.kind!r})"


class OutgoingTrack:
    """A local track attached with :meth:`Peer.send_track`.

    ``owned`` tracks are stopped when they are removed or the session ends.
    Borrowed tracks (``owned=False``) stay running for their owner.
    """

    def __init__(
        self, runtime: SessionRuntime, native: Any, kind: MediaKind, owned: bool
    ) -> None:
        self._runtime = runtime
        self.native = native
        self.kind: MediaKind = kind
        self.owned = owned
        self._sender: EngineSender | None = None
        self.removed = False

    async def remove(self) -> None:
        """Detach the track and renegotiate. Idempotent."""
        await self._runtime.remove_track(self)

    def __repr__(self) -> str:
        return f"OutgoingTrack(kind={self.kind!r}, owned={self.owned})"


class Channel:
    """A declared data channel of one session."""

    def __init__(self, runtime: SessionRuntime, state: _Channel) -> None:
        self._runtime = runtime
        self._state = state

    @property
    def name(self) -> str:
        return self._state.spec.name

    @property
    def spec(self) -> DataChannelSpec:
        return self._state.spec

    @property
    def is_open(self) -> bool:
        return self._state.is_open

    @property
    def buffered_amount(self) -> int:
        engine = self._state.engine
        return 0 if engine is None else engine.buffered_amount

    async def send(self, message: Any) -> None:
        """Validate, encode and send ``message``; see :meth:`Peer.send_message`."""
        await self._runtime.send_message(self.name, message)

    def __aiter__(self) -> AsyncIterator[Any]:
        """Iterate over received messages of a channel without an ``on_message``
        handler. Iteration ends when the session or channel closes."""
        return self._runtime.receive_messages(self._state)


class Peer:
    """The server side of one session, passed to every session handler."""

    def __init__(self, runtime: SessionRuntime) -> None:
        self._runtime = runtime

    @property
    def session_id(self) -> str:
        return self._runtime.session_id

    @property
    def name(self) -> str:
        return self._runtime.declaration.name

    @property
    def closed(self) -> bool:
        return self._runtime.code is not None

    @property
    def close_code(self) -> ErrorCode | None:
        """The termination category once the session started closing."""
        return self._runtime.code

    @property
    def incoming_tracks(self) -> tuple[IncomingTrack, ...]:
        return tuple(self._runtime.incoming)

    def channel(self, name: str) -> Channel:
        return Channel(self._runtime, self._runtime.channel_state(name))

    async def send_message(self, channel: str, message: Any) -> None:
        """Send a message on a declared channel.

        Waits until the channel is open and its send buffer is below
        ``SessionLimits.send_buffer_high_bytes``. Raises ``WebRtcError`` with
        ``invalid_message`` or ``message_too_large`` without affecting the
        session, ``channel_closed`` if the channel closed, and
        ``SessionClosedError`` once the session terminates. A buffer that does
        not drain within ``send_timeout_seconds`` terminates the session with
        ``slow_consumer``.
        """
        await self._runtime.send_message(channel, message)

    async def send_track(self, track: Any, *, owned: bool = True) -> OutgoingTrack:
        """Attach a native local track and renegotiate when necessary.

        Returns once the remote peer accepted the new description. ``owned``
        transfers the track to the session, which stops it on removal or cleanup.
        """
        return await self._runtime.send_track(track, owned=owned)

    async def remove_track(self, track: OutgoingTrack) -> None:
        await self._runtime.remove_track(track)

    async def stats(self) -> ConnectionStats:
        return await self._runtime.stats()

    def close(self, code: ErrorCode = ErrorCode.CLOSED) -> None:
        """Request termination; cleanup runs after the calling handler returns
        or is cancelled."""
        self._runtime.terminate(code)

    async def wait_closed(self) -> ErrorCode:
        return await self._runtime.wait_closed()

    def __repr__(self) -> str:
        return f"Peer(name={self.name!r}, session_id={self.session_id!r})"
