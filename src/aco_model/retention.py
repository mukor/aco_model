"""Cohort-based retention simulation."""

from pathlib import Path

import numpy as np
import pandas as pd

from aco_model.models import RetentionCurve


def load_installs(path: Path) -> pd.Series:
    """Load daily install counts from a tab-separated file.

    Returns a Series indexed by day number (1-based).
    """
    df = pd.read_csv(path, sep="\t")
    return df.set_index("day")["installs"]


def retention_vector(max_days: int, curve: RetentionCurve) -> np.ndarray:
    """Compute retention rates for days 0..max_days-1.

    Log-linear interpolation between anchor points.
    Days beyond the last anchor get 0% retention.
    """
    anchors = sorted(curve.anchors)
    last_day = anchors[-1][0]

    rates = np.zeros(max_days)
    rates[0] = 1.0

    # Build lookup from anchors: log-linear interpolation between each pair
    for seg_idx in range(len(anchors) - 1):
        d0, r0 = anchors[seg_idx]
        d1, r1 = anchors[seg_idx + 1]

        # Days in this segment (exclusive of start for segments after first)
        start = d0 if seg_idx == 0 else d0 + 1
        end = min(d1, max_days - 1)

        if start > end or start >= max_days:
            continue

        days_in_seg = np.arange(start, end + 1)

        if r0 <= 0 or r1 <= 0:
            # Can't log-interpolate through zero; linear falloff to zero
            for d in days_in_seg:
                t = (d - d0) / (d1 - d0) if d1 != d0 else 1.0
                rates[d] = r0 / 100.0 * (1.0 - t)
        else:
            log_r0 = np.log(r0)
            log_r1 = np.log(r1)
            for d in days_in_seg:
                t = (d - d0) / (d1 - d0) if d1 != d0 else 1.0
                rates[d] = np.exp(log_r0 + t * (log_r1 - log_r0)) / 100.0

    return np.clip(rates, 0.0, 1.0)


class SimResult:
    """Results of a retention simulation, including per-cohort detail."""

    def __init__(self, cohort_matrix: np.ndarray, install_days: np.ndarray,
                 install_counts: np.ndarray, sim_days: int):
        self.cohort_matrix = cohort_matrix  # shape: (n_cohorts, sim_days)
        self.install_days = install_days     # 1-based day each cohort installed
        self.install_counts = install_counts
        self.sim_days = sim_days

    @property
    def dau(self) -> np.ndarray:
        """Daily active users (column sums across all cohorts)."""
        return np.round(self.cohort_matrix.sum(axis=0)).astype(int)

    @property
    def new_installs(self) -> np.ndarray:
        """New installs per day."""
        arr = np.zeros(self.sim_days)
        for day, count in zip(self.install_days, self.install_counts):
            if day - 1 < self.sim_days:
                arr[day - 1] = count
        return arr.astype(int)

    def cohort(self, day: int) -> np.ndarray:
        """Get the retained user counts for a single cohort by install day (1-based)."""
        idx = np.where(self.install_days == day)[0]
        if len(idx) == 0:
            raise ValueError(f"No cohort for install day {day}")
        return self.cohort_matrix[idx[0]]

    def to_dataframe(self) -> pd.DataFrame:
        """Summary DataFrame with columns: day, new_installs, dau."""
        return pd.DataFrame({
            "day": np.arange(1, self.sim_days + 1),
            "new_installs": self.new_installs,
            "dau": self.dau,
        })

    def cohort_dataframe(self) -> pd.DataFrame:
        """Full cohort matrix as a DataFrame. Rows=cohort install day, cols=sim day."""
        return pd.DataFrame(
            np.round(self.cohort_matrix).astype(int),
            index=pd.Index(self.install_days, name="cohort_day"),
            columns=pd.RangeIndex(1, self.sim_days + 1, name="sim_day"),
        )


def simulate(installs: pd.Series, curve: RetentionCurve, sim_days: int) -> SimResult:
    """Run the retention simulation across all cohorts.

    Args:
        installs: Series of daily installs, indexed by day (1-based).
        curve: Retention curve parameters.
        sim_days: Total number of days to simulate.

    Returns:
        SimResult with per-cohort matrix and summary accessors.
    """
    n_cohorts = len(installs)
    rates = retention_vector(sim_days, curve)

    install_days = installs.index.values  # 1-based day numbers
    install_counts = installs.values.astype(float)

    matrix = np.zeros((n_cohorts, sim_days))
    for i, (day, count) in enumerate(zip(install_days, install_counts)):
        start_col = day - 1
        length = sim_days - start_col
        if length > 0:
            matrix[i, start_col:] = count * rates[:length]

    return SimResult(matrix, install_days, install_counts, sim_days)
