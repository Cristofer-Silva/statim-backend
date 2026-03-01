"""
services/simulator.py

Simulated CAMARA QoD API backend for hackathon demo mode.
Produces realistic session lifecycle behaviour and fluctuating
network metrics — no real telecom operator required.

@project  CheeseHacks 2026 — Remote Surgery Interface
@version  0.0.1
@since    2026-03-01
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone

from models.schemas import (
    ApplicationServer,
    CreateSessionRequest,
    ExtendSessionRequest,
    NetworkMetrics,
    QosProfile,
    QosProfileStatus,
    QosStatus,
    SessionInfo,
    StatusInfo,
)


# ─────────────────────────────────────────────
#  Pre-defined QoS profiles for surgery scenarios
# ─────────────────────────────────────────────

SIMULATED_PROFILES: list[QosProfile] = [
    QosProfile(
        name="QOS_E",
        description="Ultra-low latency — ideal for real-time tele-surgery",
        status=QosProfileStatus.ACTIVE,
        maxLatencyMs=10,
        minThroughputKbps=50_000,
    ),
    QosProfile(
        name="QOS_S",
        description="Low latency — suitable for assisted diagnostics",
        status=QosProfileStatus.ACTIVE,
        maxLatencyMs=25,
        minThroughputKbps=25_000,
    ),
    QosProfile(
        name="QOS_M",
        description="Medium latency — video consultation quality",
        status=QosProfileStatus.ACTIVE,
        maxLatencyMs=50,
        minThroughputKbps=10_000,
    ),
    QosProfile(
        name="QOS_L",
        description="Standard latency — data transfer and telemetry",
        status=QosProfileStatus.ACTIVE,
        maxLatencyMs=100,
        minThroughputKbps=5_000,
    ),
]


class CamaraSimulator:
    """
    In-memory simulation of the CAMARA QoD API.

    Stores sessions in a dict and produces realistic fluctuating
    latency/jitter metrics for the surgeon's dashboard.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, SessionInfo] = {}

    # ── QoS Profiles ──

    async def get_profiles(self) -> list[QosProfile]:
        """Return the list of available QoS profiles."""
        return SIMULATED_PROFILES

    # ── Session Lifecycle ──

    async def create_session(self, req: CreateSessionRequest) -> SessionInfo:
        """Create a simulated QoD session — immediately AVAILABLE."""
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        session = SessionInfo(
            sessionId=session_id,
            device=req.device,
            applicationServer=req.application_server,
            qosProfile=req.qos_profile,
            qosStatus=QosStatus.AVAILABLE,
            duration=req.duration,
            startedAt=now,
            expiresAt=now + timedelta(seconds=req.duration),
        )
        self._sessions[session_id] = session
        return session

    async def get_session(self, session_id: str) -> SessionInfo | None:
        """Retrieve a session by ID, or None if not found."""
        session = self._sessions.get(session_id)
        if session and session.expires_at and session.expires_at < datetime.now(timezone.utc):
            # Session expired — mark as unavailable
            session.qos_status = QosStatus.UNAVAILABLE
            session.status_info = StatusInfo.DURATION_EXPIRED
        return session

    async def extend_session(
        self, session_id: str, req: ExtendSessionRequest
    ) -> SessionInfo | None:
        """Add time to an active session."""
        session = await self.get_session(session_id)
        if not session or session.qos_status != QosStatus.AVAILABLE:
            return None

        session.duration += req.additional_duration
        session.expires_at = (
            session.started_at + timedelta(seconds=session.duration)
            if session.started_at
            else None
        )
        return session

    async def delete_session(self, session_id: str) -> SessionInfo | None:
        """Terminate a session (surgeon ends the procedure)."""
        session = self._sessions.pop(session_id, None)
        if not session:
            return None

        session.qos_status = QosStatus.UNAVAILABLE
        session.status_info = StatusInfo.DELETE_REQUESTED
        session.expires_at = datetime.now(timezone.utc)
        return session

    # ── Network Metrics ──

    async def get_metrics(self, session_id: str | None = None) -> NetworkMetrics:
        """
        Generate realistic fluctuating network metrics.

        When a QoD session is active, metrics reflect the requested
        QoS profile (e.g. QOS_E = ~10ms latency). Without an active
        session, metrics show degraded best-effort performance.
        """

        # Check if there's an active session
        active_session: SessionInfo | None = None
        if session_id:
            active_session = await self.get_session(session_id)
        else:
            # Find any active session
            for s in self._sessions.values():
                if s.qos_status == QosStatus.AVAILABLE:
                    active_session = s
                    break

        if active_session and active_session.qos_status == QosStatus.AVAILABLE:
            # ── Enhanced metrics when QoD slice is active ──
            profile_name = active_session.qos_profile
            base_latency = {
                "QOS_E": 8.0, "QOS_S": 18.0, "QOS_M": 35.0, "QOS_L": 70.0
            }.get(profile_name, 30.0)

            latency = base_latency + random.uniform(-2.0, 4.0)
            jitter = random.uniform(0.2, 1.5)
            throughput = random.uniform(80.0, 120.0)
            packet_loss = random.uniform(0.0, 0.02)
            signal = random.randint(-55, -45)
        else:
            # ── Degraded best-effort metrics (no slice) ──
            latency = random.uniform(40.0, 120.0)
            jitter = random.uniform(5.0, 25.0)
            throughput = random.uniform(10.0, 40.0)
            packet_loss = random.uniform(0.1, 2.0)
            signal = random.randint(-80, -65)
            profile_name = None

        return NetworkMetrics(
            latencyMs=round(latency, 1),
            jitterMs=round(jitter, 1),
            throughputMbps=round(throughput, 1),
            packetLossPct=round(packet_loss, 3),
            signalStrengthDbm=signal,
            sliceActive=active_session is not None
            and active_session.qos_status == QosStatus.AVAILABLE,
            qosProfile=profile_name,
            timestamp=datetime.now(timezone.utc),
        )
