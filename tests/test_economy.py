"""Tests for the economy simulation module."""

import numpy as np
import pandas as pd
import pytest

from aco_model.models import (
    BattlePassParams, EconomyParams, InstanceTier, KeyCardTier, RetentionCurve,
)
from aco_model.economy import EconomyResult, simulate_economy
from aco_model.retention import load_installs, simulate


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
    return EconomyParams()


# ── EconomyParams Model ──────────────────────────────────────────────────

class TestEconomyParams:
    def test_defaults(self):
        params = EconomyParams()
        assert params.instances_per_day == 3
        assert params.coin_to_usd == 1.0
        assert len(params.instance_tiers) == 5
        assert len(params.keycard_tiers) == 5

    def test_instance_tier_names(self):
        params = EconomyParams()
        names = [t.name for t in params.instance_tiers]
        assert names == ["bronze", "silver", "gold", "mithril", "vibranium"]

    def test_keycard_tier_names(self):
        params = EconomyParams()
        names = [t.name for t in params.keycard_tiers]
        assert names == ["common", "uncommon", "rare", "epic", "legendary"]

    def test_keycard_merge_costs_escalate(self):
        params = EconomyParams()
        costs = [t.merge_cost_nuts for t in params.keycard_tiers]
        for i in range(1, len(costs) - 1):
            assert costs[i + 1] >= costs[i]

    def test_battle_pass_defaults(self):
        params = EconomyParams()
        bp = params.battle_pass
        assert bp.cost_coins == 5.0
        assert bp.season_days == 60
        assert bp.coins_returned == 5.0
        assert bp.completion_rate == 0.3

    def test_custom_instances_per_day(self):
        params = EconomyParams(instances_per_day=5)
        assert params.instances_per_day == 5

    def test_serialization_roundtrip(self):
        params = EconomyParams()
        data = params.model_dump()
        restored = EconomyParams(**data)
        assert len(restored.instance_tiers) == len(params.instance_tiers)
        assert restored.battle_pass.cost_coins == params.battle_pass.cost_coins


# ── EconomyResult ─────────────────────────────────────────────────────────

class TestEconomyResult:
    def test_returns_economy_result(self, sim_result, default_params):
        result = simulate_economy(sim_result, default_params)
        assert isinstance(result, EconomyResult)

    def test_nuts_earned_positive(self, sim_result, default_params):
        result = simulate_economy(sim_result, default_params)
        assert np.all(result.daily_nuts_earned >= 0)

    def test_nuts_spent_positive(self, sim_result, default_params):
        result = simulate_economy(sim_result, default_params)
        assert np.all(result.daily_nuts_spent >= 0)

    def test_scrap_earned_positive(self, sim_result, default_params):
        result = simulate_economy(sim_result, default_params)
        assert np.all(result.daily_scrap_earned >= 0)

    def test_scrap_spent_positive(self, sim_result, default_params):
        result = simulate_economy(sim_result, default_params)
        assert np.all(result.daily_scrap_spent >= 0)

    def test_nuts_earned_scales_with_dau(self, sim_result, default_params):
        result = simulate_economy(sim_result, default_params)
        # Day 1 has fewer users than day 3, so less nuts earned
        assert result.daily_nuts_earned[0] < result.daily_nuts_earned[2]

    def test_keycards_consumed_equals_runs(self, sim_result, default_params):
        result = simulate_economy(sim_result, default_params)
        expected = sim_result.dau.astype(float) * default_params.instances_per_day
        np.testing.assert_array_almost_equal(result.daily_keycards_consumed, expected)

    def test_nuts_balance_is_cumulative(self, sim_result, default_params):
        result = simulate_economy(sim_result, default_params)
        net = result.daily_nuts_earned - result.daily_nuts_spent
        expected = np.cumsum(net)
        np.testing.assert_array_almost_equal(result.nuts_balance, expected)

    def test_scrap_balance_is_cumulative(self, sim_result, default_params):
        result = simulate_economy(sim_result, default_params)
        net = result.daily_scrap_earned - result.daily_scrap_spent
        expected = np.cumsum(net)
        np.testing.assert_array_almost_equal(result.scrap_balance, expected)

    def test_bp_revenue_positive(self, sim_result, default_params):
        result = simulate_economy(sim_result, default_params)
        assert result.battle_pass_total_revenue > 0

    def test_bp_revenue_scales_with_dau(self, sim_result, default_params):
        result = simulate_economy(sim_result, default_params)
        # More DAU = more BP buyers = more revenue
        assert result.battle_pass_daily_revenue[2] > result.battle_pass_daily_revenue[0]

    def test_zero_dau_produces_zero_flows(self, sample_installs_file, default_params):
        installs = load_installs(sample_installs_file)
        sim = simulate(installs, RetentionCurve(), sim_days=200)
        result = simulate_economy(sim, default_params)
        # Last days have zero DAU
        assert result.daily_nuts_earned[-1] == 0
        assert result.daily_scrap_earned[-1] == 0
        assert result.daily_keycards_consumed[-1] == 0

    def test_more_instances_more_resources(self, sim_result):
        low = simulate_economy(sim_result, EconomyParams(instances_per_day=1))
        high = simulate_economy(sim_result, EconomyParams(instances_per_day=5))
        assert high.daily_nuts_earned[0] > low.daily_nuts_earned[0]
        assert high.daily_scrap_earned[0] > low.daily_scrap_earned[0]


# ── DataFrames ────────────────────────────────────────────────────────────

class TestEconomyDataFrames:
    def test_to_dataframe(self, sim_result, default_params):
        result = simulate_economy(sim_result, default_params)
        df = result.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10
        assert "nuts_earned" in df.columns
        assert "scrap_balance" in df.columns
        assert "bp_revenue_usd" in df.columns

    def test_instance_economics_dataframe(self, sim_result, default_params):
        result = simulate_economy(sim_result, default_params)
        df = result.instance_economics_dataframe()
        assert len(df) == 5
        assert "tier" in df.columns
        assert "net_value" in df.columns
        # Higher tiers should have higher net value
        assert df.iloc[-1]["net_value"] > df.iloc[0]["net_value"]

    def test_keycard_progression_dataframe(self, sim_result, default_params):
        result = simulate_economy(sim_result, default_params)
        df = result.keycard_progression_dataframe()
        assert len(df) == 5
        assert "cumulative_nuts" in df.columns
        # Cumulative costs should increase
        assert df.iloc[-1]["cumulative_nuts"] > df.iloc[0]["cumulative_nuts"]
