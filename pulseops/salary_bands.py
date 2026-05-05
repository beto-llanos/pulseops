"""Configurable salary bands. Defaults sourced from public market data
(Levels.fyi medians, BLS, Glassdoor) for US tech roles in 2025.

Per-hour cost includes a 1.3x burden multiplier (benefits, taxes, overhead),
which is the standard accounting figure used to estimate fully-loaded labor cost.
"""
from __future__ import annotations

BURDEN_MULTIPLIER = 1.3
WORK_HOURS_PER_YEAR = 2080  # 40h * 52w

# annual base salary (USD)
DEFAULT_BANDS: dict[str, int] = {
    "intern": 55_000,
    "junior_engineer": 110_000,
    "engineer": 165_000,
    "senior_engineer": 215_000,
    "staff_engineer": 290_000,
    "engineering_manager": 245_000,
    "director": 340_000,
    "vp": 420_000,
    "designer": 145_000,
    "product_manager": 180_000,
    "senior_product_manager": 230_000,
    "data_scientist": 175_000,
    "support": 75_000,
    "sales": 130_000,
    "marketing": 120_000,
    "operations": 105_000,
    "executive": 380_000,
    "default": 150_000,
}


def hourly_cost(role: str, bands: dict[str, int] | None = None) -> float:
    """Return fully-loaded cost per hour for a given role."""
    bands = bands or DEFAULT_BANDS
    base = bands.get(role.lower(), bands["default"])
    return (base * BURDEN_MULTIPLIER) / WORK_HOURS_PER_YEAR


def per_minute(role: str, bands: dict[str, int] | None = None) -> float:
    return hourly_cost(role, bands) / 60.0


def cost_for(role: str, minutes: float, bands: dict[str, int] | None = None) -> float:
    return per_minute(role, bands) * minutes
