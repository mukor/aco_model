"""Currency flow simulation for the Animal Company economy."""

import numpy as np
import pandas as pd

from aco_model.models import EconomyParams
from aco_model.retention import SimResult


class EconomyResult:
    """Currency flow results derived from a retention simulation."""

    def __init__(self, sim: SimResult, params: EconomyParams):
        self.sim = sim
        self.params = params
        dau = sim.dau.astype(float)
        runs_per_day = dau * params.instances_per_day

        # For simplicity, assume players are evenly distributed across tiers.
        # This is a first-pass model — later we can add tier progression modeling.
        n_tiers = len(params.instance_tiers)
        avg_nuts_per_run = np.mean([t.nuts_earned for t in params.instance_tiers])
        avg_scrap_per_run = np.mean([t.scrap_earned for t in params.instance_tiers])
        avg_keycard_return = np.mean([t.keycard_drop_chance for t in params.instance_tiers])

        # ── Nuts ──────────────────────────────────────────────────────────
        # Earned: instance runs + Battle Pass rewards (spread over season)
        bp = params.battle_pass
        bp_buyers = dau * bp.purchase_rate
        bp_nuts_per_day = bp_buyers * (bp.nuts_reward_total / bp.season_days)

        self._nuts_earned = runs_per_day * avg_nuts_per_run + bp_nuts_per_day

        # Spent: keycard merging (simplified — avg merge cost across tiers)
        # Each run consumes 1 keycard, minus the chance of getting one back.
        # Net keycards consumed drives merge demand.
        net_cards_consumed = runs_per_day * (1.0 - avg_keycard_return)
        avg_merge_cost = np.mean([t.merge_cost_nuts for t in params.keycard_tiers if t.merge_cost_nuts > 0])
        # Fraction of cards that need merging (assume ~50% need to be merged up)
        merge_fraction = 0.5
        self._nuts_spent = net_cards_consumed * merge_fraction * avg_merge_cost / n_tiers

        # ── Scrap ─────────────────────────────────────────────────────────
        # Earned: instance runs + Battle Pass rewards
        bp_scrap_per_day = bp_buyers * (bp.scrap_reward_total / bp.season_days)
        self._scrap_earned = runs_per_day * avg_scrap_per_run + bp_scrap_per_day

        # Spent: buffs per run + upgrades (simplified as fraction of earn)
        buff_cost_per_run = params.buffs_per_run * params.buff_cost_scrap
        self._scrap_spent = runs_per_day * buff_cost_per_run

        # ── Coins ─────────────────────────────────────────────────────────
        # In: IAP purchases (from monetization layer, approximated here)
        # We don't double-count with monetization — just model BP flow
        self._coins_in_bp = bp_buyers * bp.cost_coins / bp.season_days  # amortized daily

        # Out: Battle Pass purchase (same as in, it's a wash)
        # Coins returned to completers
        bp_completers = bp_buyers * bp.completion_rate
        self._coins_returned_bp = bp_completers * bp.coins_returned / bp.season_days

        # ── Keycards ──────────────────────────────────────────────────────
        self._keycards_consumed = runs_per_day
        self._keycards_returned = runs_per_day * avg_keycard_return
        bp_cards_per_day = bp_buyers * (bp.keycards_rewarded / bp.season_days)
        self._keycards_from_bp = bp_cards_per_day

    @property
    def daily_nuts_earned(self) -> np.ndarray:
        return self._nuts_earned

    @property
    def daily_nuts_spent(self) -> np.ndarray:
        return self._nuts_spent

    @property
    def nuts_balance(self) -> np.ndarray:
        """Cumulative net nuts in the system."""
        return np.cumsum(self._nuts_earned - self._nuts_spent)

    @property
    def daily_scrap_earned(self) -> np.ndarray:
        return self._scrap_earned

    @property
    def daily_scrap_spent(self) -> np.ndarray:
        return self._scrap_spent

    @property
    def scrap_balance(self) -> np.ndarray:
        """Cumulative net scrap in the system."""
        return np.cumsum(self._scrap_earned - self._scrap_spent)

    @property
    def daily_coins_from_bp(self) -> np.ndarray:
        """Coins entering system via BP purchases (amortized daily)."""
        return self._coins_in_bp

    @property
    def daily_coins_returned_bp(self) -> np.ndarray:
        """Coins returned to BP completers (amortized daily)."""
        return self._coins_returned_bp

    @property
    def daily_keycards_consumed(self) -> np.ndarray:
        return self._keycards_consumed

    @property
    def daily_keycards_net(self) -> np.ndarray:
        """Net keycards consumed (consumed - returned - BP rewards)."""
        return self._keycards_consumed - self._keycards_returned - self._keycards_from_bp

    @property
    def battle_pass_daily_revenue(self) -> np.ndarray:
        """Daily BP revenue in USD."""
        return self._coins_in_bp * self.params.coin_to_usd

    @property
    def battle_pass_total_revenue(self) -> float:
        """Total BP revenue over the simulation."""
        return float(self.battle_pass_daily_revenue.sum())

    def instance_economics_dataframe(self) -> pd.DataFrame:
        """Per-tier value in / value out breakdown for a single instance run."""
        rows = []
        for i, tier in enumerate(self.params.instance_tiers):
            kc = self.params.keycard_tiers[i] if i < len(self.params.keycard_tiers) else None
            value_in = self.params.buff_cost_scrap * self.params.buffs_per_run
            if kc and kc.merge_cost_nuts > 0:
                value_in += kc.merge_cost_nuts / kc.cards_required  # amortized merge cost
            value_out = tier.nuts_earned + tier.scrap_earned
            rows.append({
                "tier": tier.name,
                "nuts_earned": tier.nuts_earned,
                "scrap_earned": tier.scrap_earned,
                "keycard_return_%": round(tier.keycard_drop_chance * 100, 1),
                "value_in": round(value_in, 1),
                "value_out": round(value_out, 1),
                "net_value": round(value_out - value_in, 1),
            })
        return pd.DataFrame(rows)

    def keycard_progression_dataframe(self) -> pd.DataFrame:
        """Key card merge costs and cumulative resource requirements."""
        rows = []
        cumulative_nuts = 0
        cumulative_cards = 0
        for kc in self.params.keycard_tiers:
            cumulative_nuts += kc.merge_cost_nuts
            cumulative_cards += kc.cards_required
            rows.append({
                "tier": kc.name,
                "cards_required": kc.cards_required,
                "merge_cost_nuts": kc.merge_cost_nuts,
                "cumulative_nuts": cumulative_nuts,
                "cumulative_cards": cumulative_cards,
                "instance_tier": kc.instance_tier,
            })
        return pd.DataFrame(rows)

    def to_dataframe(self) -> pd.DataFrame:
        """Daily currency flow summary."""
        return pd.DataFrame({
            "day": np.arange(1, self.sim.sim_days + 1),
            "dau": self.sim.dau,
            "nuts_earned": np.round(self.daily_nuts_earned).astype(int),
            "nuts_spent": np.round(self.daily_nuts_spent).astype(int),
            "nuts_balance": np.round(self.nuts_balance).astype(int),
            "scrap_earned": np.round(self.daily_scrap_earned).astype(int),
            "scrap_spent": np.round(self.daily_scrap_spent).astype(int),
            "scrap_balance": np.round(self.scrap_balance).astype(int),
            "keycards_consumed": np.round(self.daily_keycards_consumed).astype(int),
            "bp_revenue_usd": np.round(self.battle_pass_daily_revenue, 2),
        })


def simulate_economy(sim: SimResult, params: EconomyParams) -> EconomyResult:
    """Simulate currency flows across the game economy.

    Args:
        sim: Retention simulation result (provides DAU).
        params: Economy configuration (currencies, tiers, Battle Pass).

    Returns:
        EconomyResult with daily currency flows and balance tracking.
    """
    return EconomyResult(sim, params)
