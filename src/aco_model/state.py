"""Shared state file for cross-notebook communication."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
from pydantic import BaseModel, Field

from aco_model.models import EconomyParams, MonetizationParams


DEFAULT_STATE_PATH = Path("output/state.json")


class SimState(BaseModel):
    """Shared simulation state persisted to disk."""

    retention_anchors: list[tuple[int, float]]
    monetization: MonetizationParams = Field(default_factory=MonetizationParams)
    economy: EconomyParams | None = None
    sim_days: int
    dau: list[int]
    updated_at: str


def save_state(
    sim,
    retention_anchors: list[tuple[int, float]],
    monetization: MonetizationParams | None = None,
    economy: EconomyParams | None = None,
    path: Path = DEFAULT_STATE_PATH,
) -> None:
    """Save simulation state to a JSON file.

    Args:
        sim: SimResult from retention simulation (or anything with .dau and .sim_days).
        retention_anchors: Current retention curve anchor points.
        monetization: Current monetization params (uses defaults if None).
        path: Output file path.
    """
    state = SimState(
        retention_anchors=retention_anchors,
        monetization=monetization or MonetizationParams(),
        economy=economy,
        sim_days=sim.sim_days,
        dau=[int(x) for x in sim.dau],
        updated_at=datetime.now().isoformat(timespec="seconds"),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(state.model_dump_json(indent=2))


def load_state(path: Path = DEFAULT_STATE_PATH) -> Optional[SimState]:
    """Load simulation state from a JSON file.

    Returns None if the file doesn't exist.
    """
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return SimState(**data)
