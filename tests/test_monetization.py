"""Tests for the monetization module."""

import numpy as np
import pandas as pd
import pytest

from aco_model.models import MonetizationParams, RetentionCurve, ViralParams
from aco_model.monetization import RevenueResult, estimate_revenue
from aco_model.retention import SimResult, load_installs, simulate


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def sample_installs_file(tmp_path):
    path = tmp_path / "installs.txt"
    path.write_text("day\tinstalls\n1\t1000\n2\t1000\n3\t1000\n")
    return path


@pytest.fixture
def sim_result(sample_installs_file):
    installs = load_installs(sample_installs_file)
    return simulate(installs, RetentionCurve(), sim_days=10)


@pytest.fixture
def default_params():
    return MonetizationParams()


# ── MonetizationParams Model ─────────────────────────────────────────────

class TestMonetizationParams:
    def test_defaults(self):
        params = MonetizationParams()
        assert params.pct_payers == 0.03
        assert params.arppu == 1.50

    def test_custom_values(self):
        params = MonetizationParams(pct_payers=0.05, arppu=2.00)
        assert params.pct_payers == 0.05
        assert params.arppu == 2.00

    def test_pct_payers_rejects_negative(self):
        with pytest.raises(Exception):
            MonetizationParams(pct_payers=-0.1)

    def test_pct_payers_rejects_over_one(self):
        with pytest.raises(Exception):
            MonetizationParams(pct_payers=1.5)

    def test_arppu_rejects_zero(self):
        with pytest.raises(Exception):
            MonetizationParams(arppu=0)

    def test_arppu_rejects_negative(self):
        with pytest.raises(Exception):
            MonetizationParams(arppu=-1.0)

    def test_serialization_roundtrip(self):
        params = MonetizationParams(pct_payers=0.07, arppu=3.00)
        data = params.model_dump()
        restored = MonetizationParams(**data)
        assert restored.pct_payers == params.pct_payers
        assert restored.arppu == params.arppu


# ── RevenueResult ─────────────────────────────────────────────────────────

class TestRevenueResult:
    def test_returns_revenue_result(self, sim_result, default_params):
        rev = estimate_revenue(sim_result, default_params)
        assert isinstance(rev, RevenueResult)

    def test_daily_revenue_formula(self, sim_result, default_params):
        rev = estimate_revenue(sim_result, default_params)
        expected = sim_result.dau.astype(float) * 0.03 * 1.50
        np.testing.assert_array_almost_equal(rev.daily_revenue, expected)

    def test_total_revenue_is_sum(self, sim_result, default_params):
        rev = estimate_revenue(sim_result, default_params)
        assert abs(rev.total_revenue - rev.daily_revenue.sum()) < 0.01

    def test_cumulative_revenue_monotonic(self, sim_result, default_params):
        rev = estimate_revenue(sim_result, default_params)
        cum = rev.cumulative_revenue
        for i in range(1, len(cum)):
            assert cum[i] >= cum[i - 1]

    def test_cumulative_final_equals_total(self, sim_result, default_params):
        rev = estimate_revenue(sim_result, default_params)
        assert abs(rev.cumulative_revenue[-1] - rev.total_revenue) < 0.01

    def test_payers_array(self, sim_result, default_params):
        rev = estimate_revenue(sim_result, default_params)
        expected = np.round(sim_result.dau.astype(float) * 0.03).astype(int)
        np.testing.assert_array_equal(rev.payers, expected)

    def test_zero_payers_zero_revenue(self, sim_result):
        params = MonetizationParams(pct_payers=0.0, arppu=5.00)
        rev = estimate_revenue(sim_result, params)
        assert rev.total_revenue == 0.0
        assert np.all(rev.daily_revenue == 0.0)

    def test_revenue_scales_with_arppu(self, sim_result):
        rev1 = estimate_revenue(sim_result, MonetizationParams(pct_payers=0.05, arppu=1.00))
        rev2 = estimate_revenue(sim_result, MonetizationParams(pct_payers=0.05, arppu=2.00))
        assert abs(rev2.total_revenue - rev1.total_revenue * 2) < 0.01

    def test_revenue_scales_with_pct_payers(self, sim_result):
        rev1 = estimate_revenue(sim_result, MonetizationParams(pct_payers=0.02, arppu=1.50))
        rev2 = estimate_revenue(sim_result, MonetizationParams(pct_payers=0.04, arppu=1.50))
        assert abs(rev2.total_revenue - rev1.total_revenue * 2) < 0.01

    def test_arpdau(self, sim_result, default_params):
        rev = estimate_revenue(sim_result, default_params)
        # ARPDAU = pct_payers * arppu for all days with nonzero DAU
        expected = default_params.pct_payers * default_params.arppu
        for i in range(len(rev.arpdau)):
            if sim_result.dau[i] > 0:
                assert abs(rev.arpdau[i] - expected) < 0.0001

    def test_arpdau_zero_dau(self, sim_result):
        """ARPDAU should be 0 for days with no DAU."""
        # Simulate far enough that all cohorts churn
        from aco_model.retention import load_installs, simulate
        from aco_model.models import RetentionCurve
        installs = pd.Series([1000], index=[1], name='installs')
        installs.index.name = 'day'
        sim = simulate(installs, RetentionCurve(), sim_days=200)
        rev = estimate_revenue(sim, MonetizationParams())
        # Last days should have DAU=0 and ARPDAU=0
        assert rev.arpdau[-1] == 0.0

    def test_revenue_per_cohort_length(self, sim_result, default_params):
        rev = estimate_revenue(sim_result, default_params)
        assert len(rev.revenue_per_cohort) == len(sim_result.install_days)

    def test_revenue_per_cohort_sums_to_total(self, sim_result, default_params):
        rev = estimate_revenue(sim_result, default_params)
        assert abs(rev.revenue_per_cohort.sum() - rev.total_revenue) < 0.10

    def test_revenue_per_cohort_non_negative(self, sim_result, default_params):
        rev = estimate_revenue(sim_result, default_params)
        assert np.all(rev.revenue_per_cohort >= 0)

    def test_avg_revenue_per_cohort(self, sim_result, default_params):
        rev = estimate_revenue(sim_result, default_params)
        expected = rev.revenue_per_cohort.mean()
        assert abs(rev.avg_revenue_per_cohort - expected) < 0.01

    def test_total_payers(self, sim_result, default_params):
        rev = estimate_revenue(sim_result, default_params)
        total_installs = sim_result.install_counts.sum()
        expected = int(np.round(total_installs * default_params.pct_payers))
        assert rev.total_payers == expected

    def test_avg_lifetime_revenue_per_payer(self, sim_result, default_params):
        rev = estimate_revenue(sim_result, default_params)
        expected = rev.total_revenue / rev.total_payers
        assert abs(rev.avg_lifetime_revenue_per_payer - expected) < 0.01

    def test_avg_lifetime_revenue_per_payer_zero_payers(self, sim_result):
        params = MonetizationParams(pct_payers=0.0, arppu=5.00)
        rev = estimate_revenue(sim_result, params)
        assert rev.avg_lifetime_revenue_per_payer == 0.0

    def test_cohort_revenue_dataframe(self, sim_result, default_params):
        rev = estimate_revenue(sim_result, default_params)
        df = rev.cohort_revenue_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(sim_result.install_days)
        assert list(df.columns) == [
            "cohort_day", "installs", "lifetime_revenue_usd", "revenue_per_install_usd"
        ]

    def test_to_dataframe(self, sim_result, default_params):
        rev = estimate_revenue(sim_result, default_params)
        df = rev.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10
        assert list(df.columns) == [
            "day", "dau", "payers", "daily_revenue_usd", "cumulative_revenue_usd",
            "arpdau_usd"
        ]

    def test_dataframe_day_column(self, sim_result, default_params):
        rev = estimate_revenue(sim_result, default_params)
        df = rev.to_dataframe()
        assert list(df["day"]) == list(range(1, 11))

    def test_sim_reference(self, sim_result, default_params):
        rev = estimate_revenue(sim_result, default_params)
        assert rev.sim is sim_result


# ── Viral Revenue Split ──────────────────────────────────────────────────

class TestViralRevenue:
    @pytest.fixture
    def viral_sim(self, sample_installs_file):
        """A SimResult with viral cohorts mixed in."""
        installs = load_installs(sample_installs_file)
        return simulate(installs, RetentionCurve(), sim_days=30,
                        viral=ViralParams(enabled=True, k_factor=0.5))

    def test_organic_plus_viral_equals_total(self, viral_sim, default_params):
        rev = estimate_revenue(viral_sim, default_params)
        np.testing.assert_allclose(
            rev.organic_revenue + rev.viral_revenue,
            rev.daily_revenue,
            rtol=1e-12,
        )

    def test_viral_revenue_zero_when_disabled(self, sim_result, default_params):
        """A non-viral SimResult should attribute everything to organic."""
        rev = estimate_revenue(sim_result, default_params)
        assert rev.viral_revenue_total == 0.0
        assert rev.organic_revenue_total == pytest.approx(rev.total_revenue)

    def test_viral_lift_matches_dau_lift(self, sample_installs_file, default_params):
        """Since revenue is linear in DAU, % lift on revenue == % lift on DAU."""
        installs = load_installs(sample_installs_file)
        baseline = simulate(installs, RetentionCurve(), sim_days=30)
        viral = simulate(installs, RetentionCurve(), sim_days=30,
                          viral=ViralParams(enabled=True, k_factor=0.5))
        rev_base = estimate_revenue(baseline, default_params)
        rev_viral = estimate_revenue(viral, default_params)
        dau_lift = viral.dau.sum() / baseline.dau.sum() - 1
        rev_lift = rev_viral.total_revenue / rev_base.total_revenue - 1
        assert dau_lift == pytest.approx(rev_lift, rel=1e-6)

    def test_viral_revenue_proportional_to_viral_dau(self, viral_sim, default_params):
        """On any day with viral activity, viral_rev/total_rev == viral_share_of_cohort_matrix."""
        rev = estimate_revenue(viral_sim, default_params)
        # Compare against the unrounded cohort matrix shares (since rev splits on
        # the unrounded values too — sim.dau is rounded and would introduce noise).
        viral_mask = viral_sim.cohort_origin == "viral"
        viral_sum = viral_sim.cohort_matrix[viral_mask].sum(axis=0)
        total_sum = viral_sim.cohort_matrix.sum(axis=0)
        active = (total_sum > 0) & (viral_sum > 0)
        assert active.any(), "fixture should have at least one viral-active day"
        rev_share = rev.viral_revenue[active] / rev.daily_revenue[active]
        cohort_share = viral_sum[active] / total_sum[active]
        np.testing.assert_allclose(rev_share, cohort_share, rtol=1e-12)
