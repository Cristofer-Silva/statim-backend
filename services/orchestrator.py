"""
services/orchestrator.py

Network orchestration layer — selects the real CAMARA client or the
simulated backend based on the application configuration.

This is the single service the router imports; swap between live
and simulated mode happens transparently here.

@project  CheeseHacks 2026 — Remote Surgery Interface
@version  0.0.1
@since    2026-03-01
"""

from __future__ import annotations

from config import settings
from models.schemas import (
    CreateSessionRequest,
    ExtendSessionRequest,
    NetworkMetrics,
    QosProfile,
    SessionInfo,
)
from services.camara_client import CamaraClient
from services.simulator import CamaraSimulator


class NetworkOrchestrator:
    """
    Facade for all network orchestration operations.

    Transparently delegates to the real CAMARA client or the
    simulator depending on whether CAMARA_API_BASE_URL is set.
    """

    def __init__(self) -> None:
        if settings.is_simulation:
            self._backend = CamaraSimulator()
        else:
            self._backend = CamaraClient()

    @property
    def mode(self) -> str:
        """Current operation mode: 'simulation' or 'live'."""
        return "simulation" if settings.is_simulation else "live"

    # ── QoS Profiles ──

    async def get_profiles(self) -> list[QosProfile]:
        """List available QoS profiles."""
        return await self._backend.get_profiles()

    # ── Session Management ──

    async def create_session(self, req: CreateSessionRequest) -> SessionInfo:
        """Request a new QoD network slice for the surgery."""
        return await self._backend.create_session(req)

    async def get_session(self, session_id: str) -> SessionInfo | None:
        """Retrieve the current state of a QoD session."""
        return await self._backend.get_session(session_id)

    async def extend_session(
        self, session_id: str, req: ExtendSessionRequest
    ) -> SessionInfo | None:
        """Extend the duration of an active session."""
        return await self._backend.extend_session(session_id, req)

    async def delete_session(self, session_id: str) -> SessionInfo | None:
        """Tear down the network slice (end procedure)."""
        return await self._backend.delete_session(session_id)

    # ── Metrics ──

    async def get_metrics(self, session_id: str | None = None) -> NetworkMetrics:
        """Get real-time network quality metrics."""
        return await self._backend.get_metrics(session_id)
