"""Typed WebRTC sessions for FastAPI.

Declare sessions on a :class:`WebRtcRouter`; the router provides WebSocket
signaling, admission through FastAPI dependencies, limits and cleanup, while an
engine adapter (see :mod:`fastapi_webrtc.engines`) owns the peer connection.
"""

from fastapi_webrtc.declarations import (
    DataChannelSpec,
    Direction,
    MediaPolicy,
    Role,
    Session,
    SessionContext,
    SessionDeclaration,
    SessionLimits,
)
from fastapi_webrtc.engine import (
    CandidatePairStats,
    ConnectionStats,
    Engine,
    EngineCapabilities,
    MediaStats,
)
from fastapi_webrtc.errors import ErrorCode, SessionClosedError, WebRtcError
from fastapi_webrtc.events import EventHook, SessionEvent
from fastapi_webrtc.ice import (
    IceServer,
    IceServers,
    IceServerSource,
    TurnRestCredentials,
)
from fastapi_webrtc.peer import Channel, IncomingTrack, OutgoingTrack, Peer
from fastapi_webrtc.protocol import PROTOCOL_VERSION, SUBPROTOCOL
from fastapi_webrtc.router import WebRtcRouter

__version__ = "0.1.0"

__all__ = [
    "PROTOCOL_VERSION",
    "SUBPROTOCOL",
    "CandidatePairStats",
    "Channel",
    "ConnectionStats",
    "DataChannelSpec",
    "Direction",
    "Engine",
    "EngineCapabilities",
    "ErrorCode",
    "EventHook",
    "IceServer",
    "IceServerSource",
    "IceServers",
    "IncomingTrack",
    "MediaPolicy",
    "MediaStats",
    "OutgoingTrack",
    "Peer",
    "Role",
    "Session",
    "SessionClosedError",
    "SessionContext",
    "SessionDeclaration",
    "SessionEvent",
    "SessionLimits",
    "TurnRestCredentials",
    "WebRtcError",
    "WebRtcRouter",
    "__version__",
]
