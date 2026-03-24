"""Tests for the retention simulation module."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from aco_model.models import RetentionCurve
from aco_model.retention import SimResult, load_installs, retention_vector, simulate


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def sample_installs_file(tmp_path):
    """3-day installs file, 1000/day."""
    path = tmp_path / "installs.txt"
    path.write_text("day\tinstalls\n1\t1000\n2\t1000\n3\t1000\n")
    return path


@pytest.fixture
def large_installs_file(tmp_path):
    """90-day installs file, varying counts."""
    path = tmp_path / "installs.txt"
    lines = ["day\tinstalls"]
    for d in range(1, 91):
        lines.append(f"{d}\t{5000 + d * 50}")
    path.write_text("\n".join(lines))
    return path


@pytest.fixture
def default_curve():
    return RetentionCurve()


@pytest.fixture
def steep_curve():
    """Very aggressive churn — 10% D1, zero by D30."""
    return RetentionCurve(anchors=[
        (0, 100.0), (1, 10.0), (7, 2.0), (30, 0.0),
    ])


@pytest.fixture
def flat_curve():
    """High retention — 90% D1, 50% out to D180."""
    return RetentionCurve(anchors=[
        (0, 100.0), (1, 90.0), (7, 80.0), (30, 70.0), (90, 60.0), (180, 50.0),
    ])


# ── RetentionCurve Model ─────────────────────────────────────────────────

class TestRetentionCurveModel:
    def test_default_anchors(self):
        curve = RetentionCurve()
        assert len(curve.anchors) == 6
        assert curve.anchors[0] == (0, 100.0)
        assert curve.anchors[-1] == (180, 0.0)

    def test_custom_anchors(self):
        curve = RetentionCurve(anchors=[(0, 100.0), (1, 50.0), (30, 0.0)])
        assert len(curve.anchors) == 3

    def test_serialization_roundtrip(self):
        curve = RetentionCurve()
        data = curve.model_dump()
        restored = RetentionCurve(**data)
        assert restored.anchors == curve.anchors


# ── Retention Vector ──────────────────────────────────────────────────────

class TestRetentionVector:
    def test_day_zero_is_100_percent(self, default_curve):
        rates = retention_vector(10, default_curve)
        assert rates[0] == 1.0

    def test_monotonically_decreasing(self, default_curve):
        rates = retention_vector(180, default_curve)
        for i in range(1, len(rates) - 1):
            assert rates[i] >= rates[i + 1]

    def test_rates_between_0_and_1(self, default_curve):
        rates = retention_vector(200, default_curve)
        assert np.all(rates >= 0.0)
        assert np.all(rates <= 1.0)

    def test_default_anchor_points_exact(self, default_curve):
        rates = retention_vector(181, default_curve)
        assert abs(rates[1] - 0.40) < 0.001
        assert abs(rates[7] - 0.20) < 0.001
        assert abs(rates[30] - 0.05) < 0.001
        assert abs(rates[90] - 0.01) < 0.001
        assert rates[180] == 0.0

    def test_hard_churn_after_last_anchor(self, default_curve):
        rates = retention_vector(200, default_curve)
        assert rates[180] == 0.0
        assert rates[181] == 0.0
        assert rates[199] == 0.0

    def test_single_day(self, default_curve):
        rates = retention_vector(1, default_curve)
        assert len(rates) == 1
        assert rates[0] == 1.0

    def test_interpolation_between_anchors(self, default_curve):
        """Values between anchors should be between their neighbors."""
        rates = retention_vector(181, default_curve)
        assert 0.20 < rates[4] < 0.40

    def test_steep_curve(self, steep_curve):
        rates = retention_vector(50, steep_curve)
        assert abs(rates[1] - 0.10) < 0.001
        assert abs(rates[7] - 0.02) < 0.001
        assert rates[30] == 0.0
        assert rates[31] == 0.0

    def test_flat_curve(self, flat_curve):
        rates = retention_vector(181, flat_curve)
        assert abs(rates[1] - 0.90) < 0.001
        assert abs(rates[180] - 0.50) < 0.001

    def test_unsorted_anchors_still_work(self):
        """Anchors provided out of order should produce the same result."""
        curve_sorted = RetentionCurve(anchors=[
            (0, 100.0), (1, 40.0), (30, 5.0), (90, 1.0), (180, 0.0),
        ])
        curve_unsorted = RetentionCurve(anchors=[
            (90, 1.0), (0, 100.0), (180, 0.0), (30, 5.0), (1, 40.0),
        ])
        r1 = retention_vector(181, curve_sorted)
        r2 = retention_vector(181, curve_unsorted)
        np.testing.assert_array_almost_equal(r1, r2)

    def test_max_days_shorter_than_curve(self, default_curve):
        """Requesting fewer days than the curve spans should work."""
        rates = retention_vector(5, default_curve)
        assert len(rates) == 5
        assert rates[0] == 1.0
        assert abs(rates[1] - 0.40) < 0.001


# ── Load Installs ─────────────────────────────────────────────────────────

class TestLoadInstalls:
    def test_loads_correctly(self, sample_installs_file):
        installs = load_installs(sample_installs_file)
        assert len(installs) == 3
        assert installs[1] == 1000
        assert installs[3] == 1000

    def test_index_is_day(self, sample_installs_file):
        installs = load_installs(sample_installs_file)
        assert installs.index.name == "day"
        assert list(installs.index) == [1, 2, 3]

    def test_large_file(self, large_installs_file):
        installs = load_installs(large_installs_file)
        assert len(installs) == 90
        assert installs[1] == 5050
        assert installs[90] == 9500

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(Exception):
            load_installs(tmp_path / "nonexistent.txt")

    def test_single_day_file(self, tmp_path):
        path = tmp_path / "installs.txt"
        path.write_text("day\tinstalls\n1\t500\n")
        installs = load_installs(path)
        assert len(installs) == 1
        assert installs[1] == 500


# ── SimResult ─────────────────────────────────────────────────────────────

class TestSimResult:
    def test_returns_sim_result(self, sample_installs_file, default_curve):
        installs = load_installs(sample_installs_file)
        sim = simulate(installs, default_curve, sim_days=5)
        assert isinstance(sim, SimResult)

    def test_cohort_matrix_shape(self, sample_installs_file, default_curve):
        installs = load_installs(sample_installs_file)
        sim = simulate(installs, default_curve, sim_days=10)
        assert sim.cohort_matrix.shape == (3, 10)

    def test_dau_property(self, sample_installs_file, default_curve):
        installs = load_installs(sample_installs_file)
        sim = simulate(installs, default_curve, sim_days=5)
        assert len(sim.dau) == 5
        assert sim.dau[0] == 1000

    def test_new_installs_property(self, sample_installs_file, default_curve):
        installs = load_installs(sample_installs_file)
        sim = simulate(installs, default_curve, sim_days=5)
        assert sim.new_installs[0] == 1000
        assert sim.new_installs[3] == 0

    def test_cohort_access(self, sample_installs_file, default_curve):
        installs = load_installs(sample_installs_file)
        sim = simulate(installs, default_curve, sim_days=10)
        c1 = sim.cohort(1)
        assert len(c1) == 10
        # Cohort 1 starts on sim day 1 (index 0) with full installs
        assert c1[0] == 1000
        # Cohort 1 should be zero before install day — but day 1 is the first, so index 0 is nonzero
        rates = retention_vector(10, default_curve)
        np.testing.assert_almost_equal(c1[1], 1000 * rates[1])

    def test_cohort_invalid_day_raises(self, sample_installs_file, default_curve):
        installs = load_installs(sample_installs_file)
        sim = simulate(installs, default_curve, sim_days=5)
        with pytest.raises(ValueError):
            sim.cohort(99)

    def test_to_dataframe(self, sample_installs_file, default_curve):
        installs = load_installs(sample_installs_file)
        sim = simulate(installs, default_curve, sim_days=5)
        df = sim.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5
        assert list(df.columns) == ["day", "new_installs", "dau"]

    def test_cohort_dataframe(self, sample_installs_file, default_curve):
        installs = load_installs(sample_installs_file)
        sim = simulate(installs, default_curve, sim_days=5)
        cdf = sim.cohort_dataframe()
        assert isinstance(cdf, pd.DataFrame)
        assert cdf.shape == (3, 5)
        assert cdf.index.name == "cohort_day"
        assert cdf.columns.name == "sim_day"

    def test_cohort_matrix_sums_to_dau(self, sample_installs_file, default_curve):
        """Column sums of cohort matrix should equal DAU."""
        installs = load_installs(sample_installs_file)
        sim = simulate(installs, default_curve, sim_days=10)
        col_sums = np.round(sim.cohort_matrix.sum(axis=0)).astype(int)
        np.testing.assert_array_equal(col_sums, sim.dau)


# ── Simulate (via to_dataframe) ──────────────────────────────────────────

class TestSimulate:
    def test_output_shape(self, sample_installs_file, default_curve):
        installs = load_installs(sample_installs_file)
        result = simulate(installs, default_curve, sim_days=5).to_dataframe()
        assert len(result) == 5
        assert list(result.columns) == ["day", "new_installs", "dau"]

    def test_day_column_sequential(self, sample_installs_file, default_curve):
        installs = load_installs(sample_installs_file)
        result = simulate(installs, default_curve, sim_days=10).to_dataframe()
        assert list(result["day"]) == list(range(1, 11))

    def test_day1_dau_equals_installs(self, sample_installs_file, default_curve):
        installs = load_installs(sample_installs_file)
        result = simulate(installs, default_curve, sim_days=5).to_dataframe()
        assert result.iloc[0]["dau"] == 1000

    def test_dau_increases_with_new_cohorts(self, sample_installs_file, default_curve):
        installs = load_installs(sample_installs_file)
        result = simulate(installs, default_curve, sim_days=5).to_dataframe()
        assert result.iloc[1]["dau"] > result.iloc[0]["dau"]

    def test_new_installs_zero_after_data(self, sample_installs_file, default_curve):
        installs = load_installs(sample_installs_file)
        result = simulate(installs, default_curve, sim_days=5).to_dataframe()
        assert result.iloc[3]["new_installs"] == 0
        assert result.iloc[4]["new_installs"] == 0

    def test_dau_decays_after_installs_stop(self, sample_installs_file, default_curve):
        installs = load_installs(sample_installs_file)
        result = simulate(installs, default_curve, sim_days=10).to_dataframe()
        peak_idx = result["dau"].idxmax()
        last_dau = result.iloc[-1]["dau"]
        peak_dau = result.iloc[peak_idx]["dau"]
        assert last_dau < peak_dau

    def test_dau_reaches_zero_eventually(self, sample_installs_file, default_curve):
        installs = load_installs(sample_installs_file)
        result = simulate(installs, default_curve, sim_days=200).to_dataframe()
        assert result.iloc[-1]["dau"] == 0

    def test_day2_math_is_correct(self, sample_installs_file, default_curve):
        installs = load_installs(sample_installs_file)
        result = simulate(installs, default_curve, sim_days=5).to_dataframe()
        rates = retention_vector(5, default_curve)
        expected_day2 = round(1000 * rates[1] + 1000 * rates[0])
        assert result.iloc[1]["dau"] == expected_day2

    def test_single_cohort(self, tmp_path, default_curve):
        path = tmp_path / "installs.txt"
        path.write_text("day\tinstalls\n1\t10000\n")
        installs = load_installs(path)
        result = simulate(installs, default_curve, sim_days=10).to_dataframe()
        rates = retention_vector(10, default_curve)
        for i in range(10):
            expected = round(10000 * rates[i])
            assert result.iloc[i]["dau"] == expected

    def test_large_sim(self, large_installs_file, default_curve):
        installs = load_installs(large_installs_file)
        result = simulate(installs, default_curve, sim_days=365).to_dataframe()
        assert len(result) == 365
        assert result["dau"].iloc[0] > 0
        assert result.iloc[-1]["dau"] == 0

    def test_dau_non_negative(self, large_installs_file, default_curve):
        installs = load_installs(large_installs_file)
        result = simulate(installs, default_curve, sim_days=365).to_dataframe()
        assert (result["dau"] >= 0).all()

    def test_steep_curve_fast_decay(self, sample_installs_file, steep_curve):
        installs = load_installs(sample_installs_file)
        result = simulate(installs, steep_curve, sim_days=50).to_dataframe()
        assert result.iloc[-1]["dau"] == 0

    def test_flat_curve_high_dau(self, sample_installs_file, flat_curve):
        installs = load_installs(sample_installs_file)
        result = simulate(installs, flat_curve, sim_days=5).to_dataframe()
        assert result.iloc[1]["dau"] > 1800
