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
        avg_coins_per_run = np.mean([t.coins_earned for t in params.instance_tiers])
        avg_bronze_kc_drops = np.mean([t.bronze_kc_drops for t in params.instance_tiers])

        # ── Nuts ──────────────────────────────────────────────────────────
        # Earned: instance runs + Battle Pass rewards (spread over season)
        bp = params.battle_pass
        bp_buyers = dau * bp.purchase_rate
        bp_nuts_per_day = bp_buyers * (bp.nuts_reward_total / bp.season_days)

        self._nuts_earned = runs_per_day * avg_nuts_per_run + bp_nuts_per_day

        # Spent: keycard merging (simplified — avg merge cost across tiers)
        # Each run consumes 1 keycard, minus the chance of getting one back.
        # Net keycards consumed drives merge demand.
        # Each run consumes 1 keycard but drops fractional bronze cards back
        net_cards_consumed = runs_per_day * (1.0 - avg_bronze_kc_drops)
        merge_costs = [t.merge_cost_nuts for t in params.keycard_tiers if t.merge_cost_nuts > 0]
        avg_merge_cost = np.mean(merge_costs) if merge_costs else 0.0
        # Fraction of cards that need merging (assume ~50% need to be merged up)
        merge_fraction = 0.5
        self._nuts_spent = net_cards_consumed * merge_fraction * avg_merge_cost / n_tiers

        # ── Scrap ─────────────────────────────────────────────────────────
        # Earned: instance runs + Battle Pass rewards
        bp_scrap_per_day = bp_buyers * (bp.scrap_reward_total / bp.season_days)
        self._scrap_earned = runs_per_day * avg_scrap_per_run + bp_scrap_per_day

        # Spent: per-tier buff costs (averaged across tiers)
        avg_buff_cost = np.mean([t.buff_cost_scrap for t in params.instance_tiers])
        buff_cost_per_run = params.buffs_per_run * avg_buff_cost
        self._scrap_spent = runs_per_day * buff_cost_per_run

        # ── Coins ─────────────────────────────────────────────────────────
        # Earned from instances
        self._coins_earned_instances = runs_per_day * avg_coins_per_run

        # BP flow
        self._coins_in_bp = bp_buyers * bp.cost_coins / bp.season_days  # amortized daily
        bp_completers = bp_buyers * bp.completion_rate
        self._coins_returned_bp = bp_completers * bp.coins_returned / bp.season_days

        # ── Keycards ──────────────────────────────────────────────────────
        self._keycards_consumed = runs_per_day
        self._keycards_returned = runs_per_day * avg_bronze_kc_drops
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
    def daily_coins_earned(self) -> np.ndarray:
        """Coins earned from instance runs."""
        return self._coins_earned_instances

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
            value_in = tier.buff_cost_scrap * self.params.buffs_per_run
            if kc and kc.merge_cost_nuts > 0 and kc.cards_required > 0:
                value_in += kc.merge_cost_nuts / kc.cards_required
            value_out = tier.nuts_earned + tier.scrap_earned + tier.coins_earned
            rows.append({
                "tier": tier.name,
                "nuts_earned": tier.nuts_earned,
                "scrap_earned": tier.scrap_earned,
                "bronze_kc_drops": tier.bronze_kc_drops,
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


def simulate_player_progression(
    params: EconomyParams,
    max_player_days: int = 180,
    has_battle_pass: bool = False,
) -> pd.DataFrame:
    """Simulate a single average player's progression from install.

    Deterministic model: keycard drops are fractional (expected value),
    greedy tier progression (merge up as soon as affordable).
    Players must have keycards to run instances — no card = stalled.

    Args:
        params: Economy configuration.
        max_player_days: How many days to simulate.
        has_battle_pass: Whether the player bought the BP.

    Returns:
        DataFrame with one row per run slot, tracking wallet, tier, XP, stall state.
    """
    # Build lookups
    kc_order = [kc.name for kc in params.keycard_tiers]
    kc_by_name = {kc.name: kc for kc in params.keycard_tiers}
    kc_to_instance = {kc.name: kc.instance_tier for kc in params.keycard_tiers}
    tier_by_name = {t.name: t for t in params.instance_tiers}

    # Initial state
    coins = params.seed_coins
    nuts = params.seed_nuts
    scrap = params.seed_scrap
    xp = 0.0
    current_kc_idx = 0  # start at bronze (highest tier player has reached)

    # Keycard inventory (fractional for deterministic model)
    kc_inventory = {name: 0.0 for name in kc_order}
    kc_inventory[kc_order[0]] = float(params.seed_keycards)  # starting bronze cards

    # BP reward rates per XP point
    bp = params.battle_pass
    bp_nuts_per_xp = 0.0
    bp_scrap_per_xp = 0.0
    bp_coins_per_xp = 0.0
    bp_kc_per_xp = 0.0
    if has_battle_pass and bp.xp_to_complete > 0:
        bp_nuts_per_xp = bp.nuts_reward_total / bp.xp_to_complete
        bp_scrap_per_xp = bp.scrap_reward_total / bp.xp_to_complete
        bp_coins_per_xp = bp.coins_returned / bp.xp_to_complete
        bp_kc_per_xp = bp.keycards_rewarded / bp.xp_to_complete

    cum_nuts_earned = 0.0
    cum_scrap_earned = 0.0
    cum_coins_earned = 0.0
    cum_xp_earned = 0.0
    run_counter = 0
    rows = []

    for player_day in range(1, max_player_days + 1):
        for run_slot in range(params.instances_per_day):
            run_counter += 1

            # Find a tier the player can run (has keycard for)
            run_kc_idx = current_kc_idx
            stalled = False

            # Check if player has a keycard at their highest reached tier
            if kc_inventory[kc_order[run_kc_idx]] < 1.0:
                # Try lower tiers
                found = False
                for lower_idx in range(run_kc_idx - 1, -1, -1):
                    if kc_inventory[kc_order[lower_idx]] >= 1.0:
                        run_kc_idx = lower_idx
                        found = True
                        break
                if not found:
                    # No keycards anywhere — player is stalled
                    stalled = True

            tier_up = False

            if stalled:
                # Record idle slot — no loot, no progress
                rows.append({
                    "run": run_counter,
                    "player_day": player_day,
                    "instance_tier": kc_to_instance[kc_order[current_kc_idx]],
                    "keycard_tier": kc_order[current_kc_idx],
                    "coins": round(coins, 2),
                    "nuts": round(nuts, 2),
                    "scrap": round(scrap, 2),
                    "xp": round(xp, 2),
                    "cum_nuts_earned": round(cum_nuts_earned, 2),
                    "cum_scrap_earned": round(cum_scrap_earned, 2),
                    "cum_coins_earned": round(cum_coins_earned, 2),
                    "cum_xp_earned": round(cum_xp_earned, 2),
                    "tier_up": False,
                    "stalled": True,
                    "bp_complete": has_battle_pass and xp >= bp.xp_to_complete,
                    "has_bp": has_battle_pass,
                })
                continue

            # Consume 1 keycard
            run_kc_name = kc_order[run_kc_idx]
            kc_inventory[run_kc_name] -= 1.0

            # Get the instance tier for this run
            current_instance = kc_to_instance[run_kc_name]
            tier = tier_by_name[current_instance]

            # Earn from this run
            earned_nuts = tier.nuts_earned
            earned_scrap = tier.scrap_earned
            earned_coins = tier.coins_earned
            earned_xp = tier.xp_earned

            # Spend: per-tier buff cost (clamped to available scrap)
            buff_cost = tier.buff_cost_scrap * params.buffs_per_run
            spent_scrap = min(buff_cost, scrap + earned_scrap)

            # Update wallet
            nuts += earned_nuts
            scrap += earned_scrap - spent_scrap
            coins += earned_coins
            xp += earned_xp

            cum_nuts_earned += earned_nuts
            cum_scrap_earned += earned_scrap
            cum_coins_earned += earned_coins
            cum_xp_earned += earned_xp

            # Bronze keycard drops (fractional)
            kc_inventory[kc_order[0]] += tier.bronze_kc_drops

            # BP holder bonus (amortized by XP, stops at completion)
            bp_complete = False
            if has_battle_pass and xp <= bp.xp_to_complete:
                bp_nuts = earned_xp * bp_nuts_per_xp
                bp_scrap = earned_xp * bp_scrap_per_xp
                bp_coins = earned_xp * bp_coins_per_xp
                nuts += bp_nuts
                scrap += bp_scrap
                coins += bp_coins
                cum_nuts_earned += bp_nuts
                cum_scrap_earned += bp_scrap
                cum_coins_earned += bp_coins
                kc_inventory[kc_order[0]] += earned_xp * bp_kc_per_xp
            if has_battle_pass and xp >= bp.xp_to_complete:
                bp_complete = True

            # Greedy tier progression: try to merge up
            while current_kc_idx + 1 < len(kc_order):
                next_kc_name = kc_order[current_kc_idx + 1]
                next_kc = kc_by_name[next_kc_name]
                prev_kc_name = kc_order[current_kc_idx]

                cards_available = kc_inventory[prev_kc_name]
                cards_needed = next_kc.cards_required
                nuts_needed = next_kc.merge_cost_nuts

                if cards_needed > 0 and cards_available >= cards_needed and nuts >= nuts_needed:
                    kc_inventory[prev_kc_name] -= cards_needed
                    nuts -= nuts_needed
                    kc_inventory[next_kc_name] += 1
                    current_kc_idx += 1
                    tier_up = True
                else:
                    break

            rows.append({
                "run": run_counter,
                "player_day": player_day,
                "instance_tier": current_instance,
                "keycard_tier": kc_order[current_kc_idx],
                "coins": round(coins, 2),
                "nuts": round(nuts, 2),
                "scrap": round(scrap, 2),
                "xp": round(xp, 2),
                "cum_nuts_earned": round(cum_nuts_earned, 2),
                "cum_scrap_earned": round(cum_scrap_earned, 2),
                "cum_coins_earned": round(cum_coins_earned, 2),
                "cum_xp_earned": round(cum_xp_earned, 2),
                "tier_up": tier_up,
                "stalled": False,
                "bp_complete": bp_complete,
                "has_bp": has_battle_pass,
            })

    return pd.DataFrame(rows)
