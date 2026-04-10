"""Cohort-based retention simulation."""

from pathlib import Path

import numpy as np
import pandas as pd

from aco_model.models import RetentionCurve, ViralParams


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
    """Results of a retention simulation, including per-cohort detail.

    `cohort_origin` is a 1-D array (length n_cohorts) of strings: "organic"
    or "viral". For non-viral simulations all cohorts are tagged "organic".
    """

    def __init__(self, cohort_matrix: np.ndarray, install_days: np.ndarray,
                 install_counts: np.ndarray, sim_days: int,
                 cohort_origin: np.ndarray | None = None):
        self.cohort_matrix = cohort_matrix  # shape: (n_cohorts, sim_days)
        self.install_days = install_days     # 1-based day each cohort installed
        self.install_counts = install_counts
        self.sim_days = sim_days
        if cohort_origin is None:
            cohort_origin = np.array(["organic"] * len(install_days))
        self.cohort_origin = cohort_origin

    @property
    def dau(self) -> np.ndarray:
        """Daily active users (column sums across all cohorts)."""
        return np.round(self.cohort_matrix.sum(axis=0)).astype(int)

    @property
    def organic_dau(self) -> np.ndarray:
        """DAU contributed by organic cohorts only."""
        mask = self.cohort_origin == "organic"
        return np.round(self.cohort_matrix[mask].sum(axis=0)).astype(int)

    @property
    def viral_dau(self) -> np.ndarray:
        """DAU contributed by viral cohorts only."""
        mask = self.cohort_origin == "viral"
        if not mask.any():
            return np.zeros(self.sim_days, dtype=int)
        return np.round(self.cohort_matrix[mask].sum(axis=0)).astype(int)

    @property
    def new_installs(self) -> np.ndarray:
        """New installs per day (organic + viral combined)."""
        arr = np.zeros(self.sim_days)
        for day, count in zip(self.install_days, self.install_counts):
            if day - 1 < self.sim_days:
                arr[day - 1] += count
        return arr.astype(int)

    @property
    def organic_installs(self) -> np.ndarray:
        """Organic installs per day."""
        arr = np.zeros(self.sim_days)
        for day, count, origin in zip(self.install_days, self.install_counts, self.cohort_origin):
            if origin == "organic" and day - 1 < self.sim_days:
                arr[day - 1] += count
        return arr.astype(int)

    @property
    def viral_installs(self) -> np.ndarray:
        """Viral installs per day."""
        arr = np.zeros(self.sim_days)
        for day, count, origin in zip(self.install_days, self.install_counts, self.cohort_origin):
            if origin == "viral" and day - 1 < self.sim_days:
                arr[day - 1] += count
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


def simulate(installs: pd.Series, curve: RetentionCurve, sim_days: int,
             viral: ViralParams | None = None) -> SimResult:
    """Run the retention simulation across all cohorts.

    Args:
        installs: Series of daily installs, indexed by day (1-based).
        curve: Retention curve parameters.
        sim_days: Total number of days to simulate.
        viral: Optional viral params. If enabled, dispatches to the day-by-day
            viral simulation. If None or disabled, runs the vectorized fast path.

    Returns:
        SimResult with per-cohort matrix and summary accessors.
    """
    if viral is not None and viral.enabled:
        return simulate_with_viral(installs, curve, sim_days, viral)

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


def sends_from_k(k_factor: float, conversion_rate: float) -> float:
    """Back out the implied invites-sent-per-install from a k-factor.

    k = sends_per_install * conversion_rate, so sends = k / conversion_rate.
    Returns infinity if conversion_rate <= 0.

    This is the *nominal* sends-per-install — what a player would send if they
    stayed fully retained through the viral window. The model itself does not
    assume any specific conversion rate; this helper is just a translation aid.
    """
    if conversion_rate <= 0:
        return float("inf")
    return k_factor / conversion_rate


def k_from_sends(sends_per_install: float, conversion_rate: float) -> float:
    """Inverse of sends_from_k: compute k-factor from sends and conversion rate."""
    return sends_per_install * conversion_rate


def simulate_with_viral(installs: pd.Series, curve: RetentionCurve, sim_days: int,
                        viral: ViralParams) -> SimResult:
    """Day-by-day cohort simulation with viral install generation.

    For each day d, total installs = organic[d] + Σ over cohorts c of:
        installs[c] · R(d - c) · (k / W),  for 1 ≤ d - c ≤ W

    where R is the retention curve, W = viral_window_days, k = k_factor.
    Each day's total installs become a new cohort tagged organic or viral
    based on which contribution dominates the new cohort. To preserve the
    organic/viral lineage cleanly, organic and viral installs on the same
    day are recorded as TWO separate cohorts (one of each origin).

    See USAGE.md "Viral Growth (K-Factor)" for full math.
    """
    rates = retention_vector(sim_days, curve)
    W = viral.viral_window_days
    k = viral.k_factor
    per_day_share = k / W if W > 0 else 0.0

    # Build organic install lookup: day (1-based) -> count
    organic_by_day = {int(d): float(c) for d, c in zip(installs.index.values, installs.values)}

    # Cohort accumulator: each entry is (day, count, origin)
    cohort_records: list[tuple[int, float, str]] = []
    # Per-day viral install totals (1-indexed via dict)
    viral_by_day: dict[int, float] = {}

    # Walk forward day by day. On each day, emit a new cohort (organic/viral),
    # then later cohorts will pull from it via the viral window.
    for d in range(1, sim_days + 1):
        # 1. Compute viral installs landing on day d from earlier cohorts.
        #    Iterate over all cohorts whose age (d - c) falls in [1, W].
        viral_today = 0.0
        for (c_day, c_count, _origin) in cohort_records:
            age = d - c_day
            if 1 <= age <= W:
                viral_today += c_count * rates[age] * per_day_share
        viral_by_day[d] = viral_today

        # 2. Record cohorts for today.
        organic_today = organic_by_day.get(d, 0.0)
        if organic_today > 0:
            cohort_records.append((d, organic_today, "organic"))
        if viral_today > 0:
            cohort_records.append((d, viral_today, "viral"))

    # Build cohort matrix from records.
    n_cohorts = len(cohort_records)
    matrix = np.zeros((n_cohorts, sim_days))
    install_days = np.zeros(n_cohorts, dtype=int)
    install_counts = np.zeros(n_cohorts, dtype=float)
    cohort_origin = np.empty(n_cohorts, dtype=object)

    for i, (day, count, origin) in enumerate(cohort_records):
        install_days[i] = day
        install_counts[i] = count
        cohort_origin[i] = origin
        start_col = day - 1
        length = sim_days - start_col
        if length > 0:
            matrix[i, start_col:] = count * rates[:length]

    return SimResult(matrix, install_days, install_counts, sim_days,
                     cohort_origin=cohort_origin)
