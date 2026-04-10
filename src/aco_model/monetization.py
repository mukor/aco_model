"""High-level revenue estimation from DAU simulation."""

import numpy as np
import pandas as pd

from aco_model.models import MonetizationParams
from aco_model.retention import SimResult


class RevenueResult:
    """Revenue estimates derived from a retention simulation."""

    def __init__(self, sim: SimResult, params: MonetizationParams):
        self.sim = sim
        self.params = params
        dau = sim.dau.astype(float)
        self._daily_revenue = dau * params.pct_payers * params.arppu
        self._payers = np.round(dau * params.pct_payers).astype(int)

    @property
    def daily_revenue(self) -> np.ndarray:
        """Revenue per day (USD)."""
        return self._daily_revenue

    @property
    def total_revenue(self) -> float:
        """Sum of all daily revenue."""
        return float(self._daily_revenue.sum())

    @property
    def cumulative_revenue(self) -> np.ndarray:
        """Cumulative revenue over time."""
        return np.cumsum(self._daily_revenue)

    @property
    def payers(self) -> np.ndarray:
        """Estimated number of paying users per day."""
        return self._payers

    @property
    def arpdau(self) -> np.ndarray:
        """Average revenue per daily active user."""
        dau = self.sim.dau.astype(float)
        with np.errstate(divide='ignore', invalid='ignore'):
            result = np.where(dau > 0, self._daily_revenue / dau, 0.0)
        return result

    def _revenue_by_origin(self, origin: str) -> np.ndarray:
        """Daily revenue allocated to cohorts of a given origin (organic/viral).

        Splits each day's revenue between origins in proportion to their
        unrounded cohort-matrix contribution to that day. Using the unrounded
        total (rather than `sim.dau`, which is rounded) ensures
        organic_revenue + viral_revenue == daily_revenue exactly.
        """
        if not hasattr(self.sim, "cohort_origin"):
            return self._daily_revenue.copy() if origin == "organic" else np.zeros_like(self._daily_revenue)
        mask = self.sim.cohort_origin == origin
        if not mask.any():
            return self._daily_revenue.copy() if origin == "organic" else np.zeros_like(self._daily_revenue)
        # If all cohorts are of this origin, return full revenue (avoids divide-by-zero
        # and handles the trivial single-origin case cleanly).
        if mask.all():
            return self._daily_revenue.copy()
        origin_sum = self.sim.cohort_matrix[mask].sum(axis=0)
        total_sum = self.sim.cohort_matrix.sum(axis=0)
        with np.errstate(divide='ignore', invalid='ignore'):
            share = np.where(total_sum > 0, origin_sum / total_sum, 0.0)
        return share * self._daily_revenue

    @property
    def organic_revenue(self) -> np.ndarray:
        """Daily revenue from organic cohorts only."""
        return self._revenue_by_origin("organic")

    @property
    def viral_revenue(self) -> np.ndarray:
        """Daily revenue from viral cohorts only (zero if no viral cohorts)."""
        return self._revenue_by_origin("viral")

    @property
    def organic_revenue_total(self) -> float:
        return float(self.organic_revenue.sum())

    @property
    def viral_revenue_total(self) -> float:
        return float(self.viral_revenue.sum())

    @property
    def revenue_per_cohort(self) -> np.ndarray:
        """Total revenue attributed to each install cohort over its lifetime.

        Allocates daily revenue to cohorts proportional to their share of DAU.
        Returns array of length n_cohorts.
        """
        matrix = self.sim.cohort_matrix  # (n_cohorts, sim_days)
        dau = self.sim.dau.astype(float)

        # Each cohort's share of DAU per day
        with np.errstate(divide='ignore', invalid='ignore'):
            share = np.where(dau > 0, matrix / dau, 0.0)

        # Revenue attributed to each cohort per day, then summed over time
        cohort_rev = share * self._daily_revenue  # broadcast (n_cohorts, sim_days)
        return cohort_rev.sum(axis=1)

    @property
    def total_payers(self) -> int:
        """Total unique paying users across all cohorts."""
        return int(np.round(self.sim.install_counts.sum() * self.params.pct_payers))

    @property
    def avg_lifetime_revenue_per_payer(self) -> float:
        """Average lifetime revenue per paying user (ARPPU lifetime)."""
        if self.total_payers == 0:
            return 0.0
        return self.total_revenue / self.total_payers

    @property
    def avg_revenue_per_cohort(self) -> float:
        """Average lifetime revenue across all cohorts."""
        rev = self.revenue_per_cohort
        return float(rev.mean()) if len(rev) > 0 else 0.0

    def to_dataframe(self) -> pd.DataFrame:
        """Summary DataFrame with revenue columns."""
        return pd.DataFrame({
            "day": np.arange(1, self.sim.sim_days + 1),
            "dau": self.sim.dau,
            "payers": self.payers,
            "daily_revenue_usd": np.round(self.daily_revenue, 2),
            "cumulative_revenue_usd": np.round(self.cumulative_revenue, 2),
            "arpdau_usd": np.round(self.arpdau, 4),
        })

    def cohort_revenue_dataframe(self) -> pd.DataFrame:
        """Revenue per install cohort."""
        return pd.DataFrame({
            "cohort_day": self.sim.install_days,
            "installs": self.sim.install_counts.astype(int),
            "lifetime_revenue_usd": np.round(self.revenue_per_cohort, 2),
            "revenue_per_install_usd": np.round(
                np.where(self.sim.install_counts > 0,
                         self.revenue_per_cohort / self.sim.install_counts, 0.0), 4),
        })


def estimate_revenue(sim: SimResult, params: MonetizationParams) -> RevenueResult:
    """Estimate revenue from a retention simulation.

    Args:
        sim: Retention simulation result (provides DAU).
        params: Monetization assumptions (% payers, ARPPU).

    Returns:
        RevenueResult with daily/cumulative revenue and payer counts.
    """
    return RevenueResult(sim, params)
