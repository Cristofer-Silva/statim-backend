"""
config.py

Application settings loaded from environment variables / .env file.
Toggle between simulation mode and real CAMARA API by setting
CAMARA_API_BASE_URL and CAMARA_CLIENT_ID / CAMARA_CLIENT_SECRET.

@project  CheeseHacks 2026 — Remote Surgery Interface
@version  0.0.1
@since    2026-03-01
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration with .env file support."""

    # ── Server ──
    app_name: str = "Statim Network Orchestrator"
    debug: bool = True
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ── CAMARA QoD API ──
    # Leave blank to use simulation mode (default for hackathon demo).
    # Set to a real operator sandbox URL to switch to live mode.
    camara_api_base_url: str = ""
    camara_client_id: str = ""
    camara_client_secret: str = ""
    camara_token_url: str = ""

    # ── Simulation ──
    sim_base_latency_ms: float = 10.0
    sim_jitter_range_ms: float = 4.0

    @property
    def is_simulation(self) -> bool:
        """True when no real CAMARA endpoint is configured."""
        return not self.camara_api_base_url

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
