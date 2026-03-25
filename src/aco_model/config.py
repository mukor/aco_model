"""Configuration loading and validation."""

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from aco_model.models import EconomyParams, MonetizationParams, RetentionCurve


DEFAULT_CONFIG_PATH = Path("config.yaml")


class Config(BaseModel):
    """Application configuration."""

    retention: RetentionCurve = Field(default_factory=RetentionCurve)
    monetization: MonetizationParams = Field(default_factory=MonetizationParams)
    economy: EconomyParams = Field(default_factory=EconomyParams)
    installs_path: Path = Field(default=Path("data/installs.txt"))
    sim_days: int = Field(default=90)


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> Config:
    """Load configuration from a YAML file."""
    if path.exists():
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return Config(**data)
    return Config()
