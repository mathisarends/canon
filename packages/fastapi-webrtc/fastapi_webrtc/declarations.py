"""Session declarations: media policy, data channels, limits and handlers."""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from functools import cached_property
from typing import TYPE_CHECKING, Any, Literal

from fastapi import WebSocket
from pydantic import TypeAdapter

from fastapi_webrtc.errors import ErrorCode

if TYPE_CHECKING:
    from fastapi_webrtc.ice import IceServerSource
    from fastapi_webrtc.peer import IncomingTrack, Peer


class Direction(StrEnum):
    """Allowed media flow, from the server's point of view."""

    SEND = "send"
    """The server sends media; the browser only receives."""
    RECEIVE = "receive"
    """The browser sends media; the server only receives."""
    SEND_RECEIVE = "send_receive"

    @property
    def sends(self) -> bool:
        return self is not Direction.RECEIVE

    @property
    def receives(self) -> bool:
        return self is not Direction.SEND


class Role(StrEnum):
    """Which peer creates the initial offer."""

    ANSWERER = "answerer"
    """The browser offers and the server answers (the default)."""
    OFFERER = "offerer"
    """The server offers; useful for server-originated media."""


@dataclass(frozen=True)
class MediaPolicy:
    """Media kinds and directions a session accepts.

    A kind set to ``None`` is rejected: remote descriptions that offer it to the
    server fail with ``media_rejected``. ``max_incoming_tracks`` bounds remote
    active tracks per kind; ended tracks release their slot.
    """

    audio: Direction | None = None
    video: Direction | None = None
    max_incoming_tracks: int = 4

    def __post_init__(self) -> None:
        if self.max_incoming_tracks < 0:
            raise ValueError("max_incoming_tracks cannot be negative")

    def direction(self, kind: str) -> Direction | None:
        if kind == "audio":
            return self.audio
        if kind == "video":
            return self.video
        return None


MessageFormat = Literal["raw", "text", "binary", "json"]

_CHANNEL_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")


@dataclass(frozen=True)
class DataChannelSpec:
    """A declared data channel and its message models in both directions.

    ``receive_model`` validates messages from the browser and ``send_model``
    validates messages to it. A Pydantic model or any type that Pydantic can
    validate is sent as a JSON text message. ``str`` and ``bytes`` select text
    and binary messages without validation; ``None`` accepts both unvalidated.

    Channels are pre-negotiated by default: both peers create them with the same
    stream ID before negotiation, so no in-band open handshake is needed and the
    remote peer cannot open undeclared channels under a declared name.
    """

    name: str
    receive_model: Any = None
    send_model: Any = None
    ordered: bool = True
    max_retransmits: int | None = None
    max_packet_life_time_ms: int | None = None
    max_message_bytes: int | None = None
    """Overrides ``SessionLimits.max_data_channel_message_bytes`` for this channel."""
    negotiated: bool = True
    id: int | None = None
    """Explicit SCTP stream ID; defaults to the declaration index."""

    def __post_init__(self) -> None:
        if not _CHANNEL_NAME.fullmatch(self.name):
            raise ValueError(
                f"Data channel name {self.name!r} must be an identifier of at most "
                "63 characters"
            )
        if (
            self.max_retransmits is not None
            and self.max_packet_life_time_ms is not None
        ):
            raise ValueError(
                "max_retransmits and max_packet_life_time_ms are mutually exclusive"
            )
        for name in ("max_retransmits", "max_packet_life_time_ms"):
            value = getattr(self, name)
            if value is not None and (
                type(value) is not int or not 0 <= value <= 65535
            ):
                raise ValueError(f"{name} must be an integer between 0 and 65535")
        if self.max_message_bytes is not None and self.max_message_bytes <= 0:
            raise ValueError("max_message_bytes must be positive")
        if self.id is not None and not 0 <= self.id <= 65534:
            raise ValueError("Data channel IDs must be between 0 and 65534")

    @property
    def receive_format(self) -> MessageFormat:
        return _format(self.receive_model)

    @property
    def send_format(self) -> MessageFormat:
        return _format(self.send_model)

    @cached_property
    def receive_adapter(self) -> TypeAdapter[Any] | None:
        return _adapter(self.receive_model)

    @cached_property
    def send_adapter(self) -> TypeAdapter[Any] | None:
        return _adapter(self.send_model)


def _format(model: Any) -> MessageFormat:
    if model is None:
        return "raw"
    if model is str:
        return "text"
    if model is bytes:
        return "binary"
    return "json"


def _adapter(model: Any) -> TypeAdapter[Any] | None:
    return TypeAdapter(model) if _format(model) == "json" else None


@dataclass(frozen=True)
class SessionLimits:
    """Deadlines and resource bounds for every session of a router or endpoint."""

    negotiation_timeout_seconds: float = 15
    """Time from admission until the transport is connected and all declared
    channels are open."""
    media_timeout_seconds: float | None = None
    """When set, time after connection until every expected incoming media kind
    has produced a track. ``None`` disables the deadline."""
    signaling_loss_grace_seconds: float = 0
    """How long an established media session survives an abnormal signaling
    close. ``0`` terminates immediately; renegotiation is unavailable meanwhile."""
    transport_loss_grace_seconds: float = 5
    """How long the transport may stay ``disconnected`` before termination."""
    shutdown_timeout_seconds: float = 5
    """Deadline for ``on_close``, handler cancellation and engine cleanup."""
    max_pending_candidates: int = 128
    """Remote candidates buffered before the remote description is applied."""
    max_signaling_message_bytes: int = 256 * 1024
    max_outbound_signals: int = 256
    """Signaling messages queued for a slow client before termination."""
    max_data_channel_message_bytes: int = 64 * 1024
    max_queued_messages: int = 64
    """Inbound messages buffered per channel while its handler is busy."""
    send_buffer_high_bytes: int = 1024 * 1024
    """``send_message`` waits while a channel's buffered amount exceeds this."""
    send_timeout_seconds: float = 10
    """How long ``send_message`` waits for buffer space before ``slow_consumer``."""

    def __post_init__(self) -> None:
        positive = (
            "negotiation_timeout_seconds",
            "shutdown_timeout_seconds",
            "max_signaling_message_bytes",
            "max_outbound_signals",
            "max_data_channel_message_bytes",
            "max_queued_messages",
            "send_buffer_high_bytes",
            "send_timeout_seconds",
        )
        for name in positive:
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        non_negative = (
            "signaling_loss_grace_seconds",
            "transport_loss_grace_seconds",
            "max_pending_candidates",
        )
        for name in non_negative:
            if getattr(self, name) < 0:
                raise ValueError(f"{name} cannot be negative")
        if self.media_timeout_seconds is not None and self.media_timeout_seconds <= 0:
            raise ValueError("media_timeout_seconds must be positive")


PeerHandler = Callable[["Peer"], Awaitable[None]]
TrackHandler = Callable[["Peer", "IncomingTrack"], Awaitable[None]]
MessageHandler = Callable[["Peer", Any], Awaitable[None]]
CloseHandler = Callable[["Peer", ErrorCode], Awaitable[None]]


@dataclass(frozen=True)
class Session:
    """Handlers and resources for one admitted session, returned by its factory.

    Every handler runs in a task owned by the session and is cancelled when the
    session terminates. ``on_start`` runs once the transport is connected and all
    declared channels are open, before any message handler. ``run`` then runs for
    the session's lifetime: returning closes the session normally and raising
    closes it with ``handler_failure``. Without ``run`` the session lasts until a
    peer closes it or a failure occurs.

    ``on_track`` runs concurrently, once per incoming track. Message handlers run
    sequentially per channel, in arrival order. ``on_close`` runs exactly once
    after the session was admitted, with the termination category, while the
    factory's dependencies are still open.

    ``tracks`` are native engine tracks attached before the initial negotiation.
    Like ``Peer.send_track(track)`` they are owned by the session and stopped on
    cleanup; pass them through ``Peer.send_track(track, owned=False)`` instead to
    keep a shared source running.
    """

    on_start: PeerHandler | None = None
    run: PeerHandler | None = None
    on_track: TrackHandler | None = None
    on_message: Mapping[str, MessageHandler] = field(default_factory=dict)
    on_close: CloseHandler | None = None
    tracks: Sequence[Any] = ()
    ice_servers: IceServerSource | None = None
    """Overrides the router's ICE servers for this session."""


@dataclass(frozen=True)
class SessionContext:
    """Session identity passed to ICE providers and lifecycle observers."""

    name: str
    session_id: str
    websocket: WebSocket = field(repr=False)


@dataclass(frozen=True)
class SessionDeclaration:
    """A registered session endpoint, as exported to contracts and clients."""

    name: str
    path: str
    role: Role
    media: MediaPolicy
    channels: tuple[DataChannelSpec, ...]
    limits: SessionLimits
    max_sessions: int | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        if not _CHANNEL_NAME.fullmatch(self.name):
            raise ValueError(
                f"Session name {self.name!r} must be an identifier of at most "
                "63 characters"
            )
        if self.max_sessions is not None and self.max_sessions <= 0:
            raise ValueError("max_sessions must be positive")
        names = [spec.name for spec in self.channels]
        if len(set(names)) != len(names):
            raise ValueError(f"Session {self.name!r} declares duplicate channels")
        ids = [i for i in self.channel_ids.values() if i is not None]
        if len(set(ids)) != len(ids):
            raise ValueError(f"Session {self.name!r} declares duplicate channel IDs")

    @cached_property
    def channel_ids(self) -> dict[str, int | None]:
        """SCTP stream IDs of pre-negotiated channels, in declaration order."""
        return {
            spec.name: (index if spec.id is None else spec.id)
            if spec.negotiated
            else None
            for index, spec in enumerate(self.channels)
        }

    def channel(self, name: str) -> DataChannelSpec:
        for spec in self.channels:
            if spec.name == name:
                return spec
        raise KeyError(name)

    def max_message_bytes(self, spec: DataChannelSpec) -> int:
        if spec.max_message_bytes is not None:
            return spec.max_message_bytes
        return self.limits.max_data_channel_message_bytes

    def server_creates(self, spec: DataChannelSpec) -> bool:
        """Pre-negotiated channels are created by both peers; in-band channels
        are created by the initial offerer."""
        return spec.negotiated or self.role is Role.OFFERER
