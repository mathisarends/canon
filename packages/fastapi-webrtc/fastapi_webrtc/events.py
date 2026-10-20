"""Lifecycle events for metrics and audit hooks.

Events carry identifiers, categories and timings only. They never contain SDP,
ICE candidates, addresses, credentials or message payloads.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

from fastapi_webrtc.errors import ErrorCode

SessionEventKind = Literal[
    "admitted",
    "rejected",
    "connected",
    "ready",
    "media_ready",
    "track",
    "renegotiated",
    "closed",
]


@dataclass(frozen=True)
class SessionEvent:
    """One step in a session's lifecycle.

    * ``admitted``: dependencies succeeded and a session slot was reserved.
    * ``rejected``: the session was refused after admission (``code`` says why).
    * ``connected``: the transport connected and every channel opened.
    * ``ready``: ``on_start`` finished; message handlers and ``run`` started.
    * ``media_ready``: every expected incoming media kind delivered packets.
    * ``track``: an incoming track arrived (``media_kind`` is set).
    * ``renegotiated``: a later offer/answer exchange completed.
    * ``closed``: cleanup finished (``code`` is the termination category).
    """

    kind: SessionEventKind
    name: str
    session_id: str
    elapsed_seconds: float
    """Seconds since admission."""
    code: ErrorCode | None = None
    media_kind: Literal["audio", "video"] | None = None
    attributes: dict[str, str | int | float | bool] = field(default_factory=dict)


EventHook = Callable[[SessionEvent], None]
"""A synchronous, non-blocking observer. Exceptions are logged and ignored."""
