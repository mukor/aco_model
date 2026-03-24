"""Pydantic models for the game economy."""

from pydantic import BaseModel, Field


class RetentionCurve(BaseModel):
    """Retention curve defined by anchor points with log-linear interpolation.

    Anchors are (day, retention%) pairs. Retention is interpolated log-linearly
    between anchors. Days beyond the last anchor get 0% retention.
    """

    anchors: list[tuple[int, float]] = Field(
        default=[(0, 100.0), (1, 40.0), (7, 20.0), (30, 5.0), (90, 1.0), (180, 0.0)],
        description="(day, retention%) pairs defining the curve",
    )


class MonetizationParams(BaseModel):
    """High-level revenue estimation parameters."""

    pct_payers: float = Field(default=0.03, ge=0.0, le=1.0,
                              description="Fraction of DAU that are paying users (0.0-1.0)")
    arppu: float = Field(default=1.50, gt=0.0,
                         description="Average revenue per paying user per day (USD)")
