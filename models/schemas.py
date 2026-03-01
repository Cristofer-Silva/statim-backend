"""
models/schemas.py

Pydantic models matching the CAMARA Quality on Demand API data structures.
Used for request/response validation and serialization.

References:
  - CAMARA QoD OpenAPI spec: https://github.com/camaraproject/QualityOnDemand

@project  CheeseHacks 2026 — Remote Surgery Interface
@version  0.0.1
@since    2026-03-01
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
#  Enumerations
# ─────────────────────────────────────────────

class QosStatus(str, Enum):
    """CAMARA session lifecycle states."""
    REQUESTED = "REQUESTED"
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class StatusInfo(str, Enum):
    """Reason a session became UNAVAILABLE."""
    DURATION_EXPIRED = "DURATION_EXPIRED"
    NETWORK_TERMINATED = "NETWORK_TERMINATED"
    DELETE_REQUESTED = "DELETE_REQUESTED"


class QosProfileStatus(str, Enum):
    """Whether a QoS profile is currently usable."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DEPRECATED = "DEPRECATED"


# ─────────────────────────────────────────────
#  Device & Server Identifiers
# ─────────────────────────────────────────────

class Device(BaseModel):
    """End-user equipment identifier (surgeon console)."""
    ipv4_address: Optional[str] = Field(None, alias="ipv4Address")
    ipv6_address: Optional[str] = Field(None, alias="ipv6Address")
    phone_number: Optional[str] = Field(None, alias="phoneNumber")

    model_config = {"populate_by_name": True}


class ApplicationServer(BaseModel):
    """Backend server identifier (remote surgical robot)."""
    ipv4_address: Optional[str] = Field(None, alias="ipv4Address")
    ipv6_address: Optional[str] = Field(None, alias="ipv6Address")

    model_config = {"populate_by_name": True}


# ─────────────────────────────────────────────
#  QoS Profiles
# ─────────────────────────────────────────────

class QosProfile(BaseModel):
    """A network quality profile offered by the operator."""
    name: str
    description: str
    status: QosProfileStatus = QosProfileStatus.ACTIVE
    max_latency_ms: Optional[int] = Field(None, alias="maxLatencyMs")
    min_throughput_kbps: Optional[int] = Field(None, alias="minThroughputKbps")

    model_config = {"populate_by_name": True}


# ─────────────────────────────────────────────
#  Session Management
# ─────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    """Request body to create a QoD session (maps to CAMARA POST /sessions)."""
    device: Optional[Device] = None
    application_server: ApplicationServer = Field(..., alias="applicationServer")
    qos_profile: str = Field(..., alias="qosProfile")
    duration: int = Field(3600, ge=1, description="Session duration in seconds")
    sink: Optional[str] = Field(None, description="Notification callback URL")

    model_config = {"populate_by_name": True}


class SessionInfo(BaseModel):
    """Full session state returned by the API (maps to CAMARA SessionInfo)."""
    session_id: str = Field(..., alias="sessionId")
    device: Optional[Device] = None
    application_server: ApplicationServer = Field(..., alias="applicationServer")
    qos_profile: str = Field(..., alias="qosProfile")
    qos_status: QosStatus = Field(..., alias="qosStatus")
    status_info: Optional[StatusInfo] = Field(None, alias="statusInfo")
    duration: int
    started_at: Optional[datetime] = Field(None, alias="startedAt")
    expires_at: Optional[datetime] = Field(None, alias="expiresAt")

    model_config = {"populate_by_name": True}


class ExtendSessionRequest(BaseModel):
    """Request body to extend an active session."""
    additional_duration: int = Field(
        ..., alias="requestedAdditionalDuration", ge=1,
        description="Extra seconds to add"
    )

    model_config = {"populate_by_name": True}


# ─────────────────────────────────────────────
#  Network Metrics (custom — for the dashboard)
# ─────────────────────────────────────────────

class NetworkMetrics(BaseModel):
    """Real-time network quality telemetry for the surgeon's dashboard."""
    latency_ms: float = Field(..., alias="latencyMs")
    jitter_ms: float = Field(..., alias="jitterMs")
    throughput_mbps: float = Field(..., alias="throughputMbps")
    packet_loss_pct: float = Field(..., alias="packetLossPct")
    signal_strength_dbm: int = Field(..., alias="signalStrengthDbm")
    slice_active: bool = Field(..., alias="sliceActive")
    qos_profile: Optional[str] = Field(None, alias="qosProfile")
    timestamp: datetime

    model_config = {"populate_by_name": True}


# ─────────────────────────────────────────────
#  Health Check
# ─────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Server health and configuration status."""
    status: str = "ok"
    mode: str  # "simulation" | "live"
    version: str = "0.0.1"
    camara_endpoint: Optional[str] = None
