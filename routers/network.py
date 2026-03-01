"""
routers/network.py

REST API endpoints exposed to the surgeon's dashboard frontend.
All routes are prefixed with /api/network.

@project  CheeseHacks 2026 — Remote Surgery Interface
@version  0.0.1
@since    2026-03-01
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from models.schemas import (
    CreateSessionRequest,
    ExtendSessionRequest,
    NetworkMetrics,
    QosProfile,
    SessionInfo,
)
from services.orchestrator import NetworkOrchestrator

router = APIRouter(prefix="/api/network", tags=["Network Orchestration"])

# Shared orchestrator instance (created at import time)
orchestrator = NetworkOrchestrator()


# ─────────────────────────────────────────────
#  QoS Profiles
# ─────────────────────────────────────────────

@router.get("/profiles", response_model=list[QosProfile])
async def list_profiles():
    """
    List all available QoS profiles.

    Returns a set of network quality tiers the surgeon can choose
    from when starting a procedure. Each profile specifies maximum
    latency and minimum throughput guarantees.
    """
    return await orchestrator.get_profiles()


# ─────────────────────────────────────────────
#  Session Management
# ─────────────────────────────────────────────

@router.post("/session", response_model=SessionInfo, status_code=201)
async def create_session(req: CreateSessionRequest):
    """
    Request a low-latency 5G network slice for a surgical procedure.

    This is the core operation — it tells the telecom operator to
    allocate a dedicated network path (slice) between the surgeon's
    console and the remote robotic system, with guaranteed QoS.
    """
    return await orchestrator.create_session(req)


@router.get("/session/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """
    Check the status of an active network slice.

    Returns current QoS status: REQUESTED → AVAILABLE → UNAVAILABLE.
    The dashboard polls this to show connection health.
    """
    session = await orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/session/{session_id}/extend", response_model=SessionInfo)
async def extend_session(session_id: str, req: ExtendSessionRequest):
    """
    Extend the duration of an active network slice.

    Used when a surgical procedure runs longer than initially expected.
    """
    session = await orchestrator.extend_session(session_id, req)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found or no longer active",
        )
    return session


@router.delete("/session/{session_id}", response_model=SessionInfo)
async def delete_session(session_id: str):
    """
    Tear down the network slice (end the procedure).

    Releases the reserved network resources. Should be called when
    the surgeon completes or aborts the operation.
    """
    session = await orchestrator.delete_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# ─────────────────────────────────────────────
#  Real-Time Metrics
# ─────────────────────────────────────────────

@router.get("/metrics", response_model=NetworkMetrics)
async def get_metrics(
    session_id: Optional[str] = Query(
        None, description="Optional session ID for slice-specific metrics"
    ),
):
    """
    Get real-time network quality metrics.

    Returns latency, jitter, throughput, packet loss, and signal
    strength. When a QoD slice is active, metrics reflect the
    enhanced network quality; otherwise, degraded best-effort values.
    """
    return await orchestrator.get_metrics(session_id)
