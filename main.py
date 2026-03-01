"""
main.py

FastAPI application entry point for the Statim Network Orchestrator.
Provides REST API endpoints for 5G network slice orchestration
via the CAMARA Quality on Demand API.

Run locally:
    cd backend
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000

@project  CheeseHacks 2026 — Remote Surgery Interface
@version  0.0.1
@since    2026-03-01
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from models.schemas import HealthResponse
from routers.network import router as network_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle events."""
    mode = "SIMULATION" if settings.is_simulation else "LIVE"
    print(f"🏥 Statim Network Orchestrator starting in {mode} mode")
    if not settings.is_simulation:
        print(f"   CAMARA endpoint: {settings.camara_api_base_url}")
    yield
    print("🏥 Statim Network Orchestrator shutting down")


app = FastAPI(
    title=settings.app_name,
    description=(
        "Backend service for the CheeseHacks 2026 Remote Surgery Interface. "
        "Orchestrates low-latency 5G network slices via the CAMARA QoD API "
        "to enable tele-surgery in medical deserts."
    ),
    version="0.0.1",
    lifespan=lifespan,
)

# ── CORS — allow the React frontend to call the API ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers ──
app.include_router(network_router)


# ── Health check ──
@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Server health check.

    Returns the current operating mode (simulation or live)
    and the configured CAMARA endpoint if in live mode.
    """
    return HealthResponse(
        status="ok",
        mode="simulation" if settings.is_simulation else "live",
        camara_endpoint=(
            settings.camara_api_base_url if not settings.is_simulation else None
        ),
    )
