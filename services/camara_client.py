"""
services/camara_client.py

Real CAMARA Quality on Demand API client.
Uses httpx to make authenticated requests to a telecom operator's
QoD sandbox (e.g. Deutsche Telekom, Telefónica Open Gateway).

Set CAMARA_API_BASE_URL, CAMARA_CLIENT_ID, and CAMARA_CLIENT_SECRET
in the .env file to activate this client.

@project  CheeseHacks 2026 — Remote Surgery Interface
@version  0.0.1
@since    2026-03-01
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from config import settings
from models.schemas import (
    CreateSessionRequest,
    ExtendSessionRequest,
    NetworkMetrics,
    QosProfile,
    QosProfileStatus,
    SessionInfo,
)


class CamaraClient:
    """
    HTTP client for the real CAMARA QoD API.

    Handles OAuth2 token acquisition and maps CAMARA responses
    to our Pydantic models.
    """

    def __init__(self) -> None:
        self._base_url = settings.camara_api_base_url.rstrip("/")
        self._token: str | None = None
        self._client = httpx.AsyncClient(timeout=10.0)

    async def _ensure_token(self) -> str:
        """Acquire an OAuth2 access token using client credentials."""
        if self._token:
            return self._token

        resp = await self._client.post(
            settings.camara_token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.camara_client_id,
                "client_secret": settings.camara_client_secret,
            },
        )
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        return self._token

    def _headers(self, token: str) -> dict[str, str]:
        """Build authorization headers."""
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # ── QoS Profiles ──

    async def get_profiles(self) -> list[QosProfile]:
        """Fetch available QoS profiles from the operator."""
        token = await self._ensure_token()
        resp = await self._client.get(
            f"{self._base_url}/qos-profiles",
            headers=self._headers(token),
        )
        resp.raise_for_status()
        return [QosProfile(**p) for p in resp.json()]

    # ── Session Lifecycle ──

    async def create_session(self, req: CreateSessionRequest) -> SessionInfo:
        """Create a QoD session via CAMARA POST /sessions."""
        token = await self._ensure_token()
        body = req.model_dump(by_alias=True, exclude_none=True)
        resp = await self._client.post(
            f"{self._base_url}/sessions",
            headers=self._headers(token),
            json=body,
        )
        resp.raise_for_status()
        return SessionInfo(**resp.json())

    async def get_session(self, session_id: str) -> SessionInfo | None:
        """Retrieve session details via CAMARA GET /sessions/{id}."""
        token = await self._ensure_token()
        resp = await self._client.get(
            f"{self._base_url}/sessions/{session_id}",
            headers=self._headers(token),
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return SessionInfo(**resp.json())

    async def extend_session(
        self, session_id: str, req: ExtendSessionRequest
    ) -> SessionInfo | None:
        """Extend session via CAMARA POST /sessions/{id}/extend."""
        token = await self._ensure_token()
        body = req.model_dump(by_alias=True, exclude_none=True)
        resp = await self._client.post(
            f"{self._base_url}/sessions/{session_id}/extend",
            headers=self._headers(token),
            json=body,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return SessionInfo(**resp.json())

    async def delete_session(self, session_id: str) -> SessionInfo | None:
        """Terminate session via CAMARA DELETE /sessions/{id}."""
        token = await self._ensure_token()
        resp = await self._client.delete(
            f"{self._base_url}/sessions/{session_id}",
            headers=self._headers(token),
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        # DELETE may return 204 with no body
        if resp.status_code == 204:
            return await self.get_session(session_id)
        return SessionInfo(**resp.json())

    async def get_metrics(self, session_id: str | None = None) -> NetworkMetrics:
        """
        Build metrics from the current session state.

        Note: CAMARA doesn't provide real-time telemetry; we derive
        approximate metrics from the session's QoS profile parameters.
        """
        session = None
        if session_id:
            session = await self.get_session(session_id)

        profile_name = session.qos_profile if session else None
        slice_active = session is not None and session.qos_status == "AVAILABLE"

        return NetworkMetrics(
            latencyMs=10.0 if slice_active else 80.0,
            jitterMs=1.0 if slice_active else 15.0,
            throughputMbps=100.0 if slice_active else 25.0,
            packetLossPct=0.01 if slice_active else 1.0,
            signalStrengthDbm=-50 if slice_active else -75,
            sliceActive=slice_active,
            qosProfile=profile_name,
            timestamp=datetime.now(timezone.utc),
        )

    async def close(self) -> None:
        """Clean up the HTTP client."""
        await self._client.aclose()
