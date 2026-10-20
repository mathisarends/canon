"""Normalize only metrics whose units the engine can establish reliably."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest
from aiortc import RTCPeerConnection
from aiortc.stats import RTCInboundRtpStreamStats, RTCStatsReport

from fastapi_webrtc.engines.aiortc import AiortcPeer


@pytest.mark.parametrize(("kind", "jitter"), [("audio", 480), ("video", 900)])
async def test_jitter_without_a_stream_clock_rate_is_unavailable(
    kind: str, jitter: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    connection = RTCPeerConnection()
    report = RTCStatsReport()
    report.add(
        RTCInboundRtpStreamStats(
            timestamp=datetime.now(UTC),
            type="inbound-rtp",
            id="inbound",
            ssrc=42,
            kind=kind,
            transportId="transport",
            packetsReceived=20,
            packetsLost=2,
            jitter=jitter,
        )
    )
    monkeypatch.setattr(connection, "getStats", AsyncMock(return_value=report))
    peer = AiortcPeer(connection, Mock(), {})
    try:
        stats = await peer.stats()
        assert len(stats.inbound) == 1
        media = stats.inbound[0]
        assert media.kind == kind
        assert media.packets == 20
        assert media.packets_lost == 2
        assert media.jitter_seconds is None
    finally:
        await peer.close()
