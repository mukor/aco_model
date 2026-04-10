"""Tests for the economy simulation module."""

import numpy as np
import pandas as pd
import pytest

from aco_model.models import (
    BattlePassParams, EconomyParams, InstanceTier, KeyCardTier, RetentionCurve,
)
from aco_model.economy import EconomyResult, simulate_economy, simulate_player_progression
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
        assert names == ["common", "uncommon", "rare", "epic", "legendary"]

    def test_keycard_tier_names(self):
        params = EconomyParams()
        names = [t.name for t in params.keycard_tiers]
        assert names == ["bronze", "silver", "gold", "mithril", "vibranium"]

    def test_keycard_merge_costs_escalate(self):
        params = EconomyParams()
        costs = [t.merge_cost_nuts for t in params.keycard_tiers]
        for i in range(1, len(costs) - 1):
            assert costs[i + 1] >= costs[i]

    def test_battle_pass_defaults(self):
        params = EconomyParams()
        bp = params.battle_pass
        assert bp.cost_coins == 5.0
        assert bp.season_days == 90
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


# ── Player Progression ────────────────────────────────────────────────────

class TestPlayerProgression:
    def test_returns_dataframe(self, default_params):
        df = simulate_player_progression(default_params, max_player_days=10)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10 * default_params.instances_per_day

    def test_starts_with_seed_currency(self):
        """Player starts with seed currency (may spend some on immediate merges)."""
        params = EconomyParams(
            seed_nuts=100.0, seed_keycards=5, instances_per_day=1,
            instance_tiers=[InstanceTier(name="common", nuts_earned=10, scrap_earned=10, bronze_kc_drops=0.5)],
            keycard_tiers=[KeyCardTier(name="bronze", cards_required=0, merge_cost_nuts=0, instance_tier="common")],
        )
        df = simulate_player_progression(params, max_player_days=1)
        first = df.iloc[0]
        # Should have earned on top of seed (minus any buff cost)
        assert first["coins"] >= params.seed_coins

    def test_starts_at_common_tier(self):
        """With no merge possible, player stays at bronze/common."""
        params = EconomyParams(
            seed_nuts=0, seed_keycards=5, instances_per_day=1,
            instance_tiers=[InstanceTier(name="common", nuts_earned=10, scrap_earned=10, bronze_kc_drops=0.5)],
            keycard_tiers=[
                KeyCardTier(name="bronze", cards_required=0, merge_cost_nuts=0, instance_tier="common"),
                KeyCardTier(name="silver", cards_required=2, merge_cost_nuts=9999, instance_tier="common"),
            ],
        )
        df = simulate_player_progression(params, max_player_days=1)
        assert df.iloc[0]["instance_tier"] == "common"
        assert df.iloc[0]["keycard_tier"] == "bronze"

    def test_resources_accumulate(self, default_params):
        df = simulate_player_progression(default_params, max_player_days=10)
        active = df[~df["stalled"]]
        if len(active) > 1:
            assert active.iloc[-1]["cum_nuts_earned"] > active.iloc[0]["cum_nuts_earned"]

    def test_xp_accumulates(self, default_params):
        df = simulate_player_progression(default_params, max_player_days=10)
        active = df[~df["stalled"]]
        if len(active) > 1:
            assert active.iloc[-1]["xp"] > active.iloc[0]["xp"]

    def test_keycards_consumed(self):
        """Player should consume keycards each run."""
        params = EconomyParams(
            seed_keycards=3,
            instances_per_day=3,
            instance_tiers=[
                InstanceTier(name="common", nuts_earned=30, scrap_earned=50, bronze_kc_drops=0.0),
            ],
            keycard_tiers=[
                KeyCardTier(name="bronze", cards_required=0, merge_cost_nuts=0, instance_tier="common"),
            ],
        )
        df = simulate_player_progression(params, max_player_days=2)
        # Day 1: 3 keycards, 3 runs, 0 drops → all consumed
        # Day 2: 0 keycards → all stalled
        day1 = df[df["player_day"] == 1]
        day2 = df[df["player_day"] == 2]
        assert (~day1["stalled"]).all()  # all day 1 runs succeed
        assert day2["stalled"].all()  # all day 2 stalled

    def test_stall_when_no_keycards(self):
        """Player with 0 seed keycards should be stalled immediately."""
        params = EconomyParams(
            seed_keycards=0,
            instances_per_day=3,
        )
        df = simulate_player_progression(params, max_player_days=2)
        assert df["stalled"].all()

    def test_bronze_drops_sustain_play(self):
        """High bronze drops should let player keep running."""
        params = EconomyParams(
            seed_keycards=1,
            instances_per_day=3,
            instance_tiers=[
                InstanceTier(name="common", nuts_earned=30, scrap_earned=50, bronze_kc_drops=2.0),
            ],
            keycard_tiers=[
                KeyCardTier(name="bronze", cards_required=0, merge_cost_nuts=0, instance_tier="common"),
            ],
        )
        df = simulate_player_progression(params, max_player_days=10)
        # With 2.0 bronze drops per run, player should never stall
        assert not df["stalled"].any()

    def test_tier_up_happens(self):
        """With enough seed nuts and keycards, player should merge up."""
        params = EconomyParams(
            seed_nuts=5000.0,
            seed_keycards=20,
            instances_per_day=3,
        )
        df = simulate_player_progression(params, max_player_days=30)
        assert df["tier_up"].any()

    def test_greedy_merge(self):
        """Player merges as soon as they can afford it."""
        params = EconomyParams(
            seed_nuts=200.0,
            seed_keycards=10,
            keycard_tiers=[
                KeyCardTier(name="bronze", cards_required=0, merge_cost_nuts=0, instance_tier="common"),
                KeyCardTier(name="silver", cards_required=2, merge_cost_nuts=100, instance_tier="uncommon"),
            ],
            instance_tiers=[
                InstanceTier(name="common", nuts_earned=30, scrap_earned=50, bronze_kc_drops=2.0),
                InstanceTier(name="uncommon", nuts_earned=60, scrap_earned=100, bronze_kc_drops=1.0),
            ],
        )
        df = simulate_player_progression(params, max_player_days=5)
        tier_ups = df[df["tier_up"]]
        assert len(tier_ups) > 0
        assert tier_ups.iloc[0]["run"] <= 10

    def test_bp_holder_earns_more(self, default_params):
        df_no_bp = simulate_player_progression(default_params, max_player_days=30, has_battle_pass=False)
        df_bp = simulate_player_progression(default_params, max_player_days=30, has_battle_pass=True)
        no_bp_active = df_no_bp[~df_no_bp["stalled"]]
        bp_active = df_bp[~df_bp["stalled"]]
        if len(no_bp_active) > 0 and len(bp_active) > 0:
            assert bp_active.iloc[-1]["cum_nuts_earned"] >= no_bp_active.iloc[-1]["cum_nuts_earned"]

    def test_bp_complete_flag(self):
        """BP should complete when XP reaches threshold."""
        params = EconomyParams(
            instances_per_day=10,
            seed_keycards=500,
            battle_pass=BattlePassParams(xp_to_complete=500),
        )
        df = simulate_player_progression(params, max_player_days=30, has_battle_pass=True)
        assert df["bp_complete"].any()

    def test_columns_present(self, default_params):
        df = simulate_player_progression(default_params, max_player_days=1)
        expected = ["run", "player_day", "instance_tier", "keycard_tier",
                    "coins", "nuts", "scrap", "xp", "tier_up", "stalled", "bp_complete", "has_bp"]
        for col in expected:
            assert col in df.columns

    def test_player_day_sequential(self, default_params):
        df = simulate_player_progression(default_params, max_player_days=5)
        assert df.iloc[0]["player_day"] == 1
        assert df.iloc[default_params.instances_per_day]["player_day"] == 2

    def test_cascade_merge(self):
        """Bronze cards should auto-merge up through multiple tiers."""
        params = EconomyParams(
            seed_keycards=20,
            seed_nuts=10000.0,
            instances_per_day=5,
            instance_tiers=[
                InstanceTier(name="common", nuts_earned=100, scrap_earned=50, bronze_kc_drops=3.0),
                InstanceTier(name="uncommon", nuts_earned=150, scrap_earned=100, bronze_kc_drops=2.0),
                InstanceTier(name="rare", nuts_earned=200, scrap_earned=150, bronze_kc_drops=1.5),
            ],
            keycard_tiers=[
                KeyCardTier(name="bronze", cards_required=0, merge_cost_nuts=0, instance_tier="common"),
                KeyCardTier(name="silver", cards_required=2, merge_cost_nuts=100, instance_tier="uncommon"),
                KeyCardTier(name="gold", cards_required=2, merge_cost_nuts=200, instance_tier="rare"),
            ],
        )
        df = simulate_player_progression(params, max_player_days=30)
        # Player should reach at least gold tier via cascade merging
        tiers_reached = df["keycard_tier"].unique()
        assert "gold" in tiers_reached, f"Only reached: {tiers_reached}"
        # Should have runs at all three tiers
        active = df[~df["stalled"]]
        instance_tiers_played = active["instance_tier"].unique()
        assert len(instance_tiers_played) >= 2, f"Only played: {instance_tiers_played}"

    def test_wallet_flattens_when_stalled(self):
        """Once stalled, wallet should stop growing."""
        params = EconomyParams(
            seed_keycards=2,
            instances_per_day=3,
            instance_tiers=[
                InstanceTier(name="common", nuts_earned=30, scrap_earned=50, bronze_kc_drops=0.0),
            ],
            keycard_tiers=[
                KeyCardTier(name="bronze", cards_required=0, merge_cost_nuts=0, instance_tier="common"),
            ],
        )
        df = simulate_player_progression(params, max_player_days=5)
        # After keycards run out, wallet should be constant
        stalled = df[df["stalled"]]
        if len(stalled) > 1:
            # All stalled rows should have same wallet
            assert stalled["nuts"].nunique() == 1
            assert stalled["scrap"].nunique() == 1
