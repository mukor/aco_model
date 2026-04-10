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


class ViralParams(BaseModel):
    """K-factor (viral install) parameters.

    Each install generates `k_factor` viral installs total, spread evenly across
    `viral_window_days` days after install, scaled by retention. See USAGE.md
    "Viral Growth (K-Factor)" for the math.
    """

    enabled: bool = Field(default=False, description="Toggle k-factor on/off")
    k_factor: float = Field(default=0.3, ge=0.0,
                            description="Invites per install over the entire viral window")
    viral_window_days: int = Field(default=7, gt=0,
                                    description="Days after install during which a user invites")


class MonetizationParams(BaseModel):
    """High-level revenue estimation parameters."""

    pct_payers: float = Field(default=0.03, ge=0.0, le=1.0,
                              description="Fraction of DAU that are paying users (0.0-1.0)")
    arppu: float = Field(default=1.50, gt=0.0,
                         description="Average revenue per paying user per day (USD)")


# ── Economy Models ────────────────────────────────────────────────────────


class InstanceTier(BaseModel):
    """Loot/cost parameters for a single instance tier."""

    name: str
    nuts_earned: float = Field(ge=0, description="Nuts earned per instance run")
    scrap_earned: float = Field(ge=0, description="Scrap earned per instance run")
    coins_earned: float = Field(default=0, ge=0, description="Avg coins earned per instance run")
    xp_earned: float = Field(default=0, ge=0, description="Avg XP earned per instance run")
    gear_value_usd: float = Field(default=0, ge=0, description="Avg USD value of gear drops per run")
    bronze_kc_drops: float = Field(default=0.3, ge=0,
                                    description="Avg bronze keycards dropped per run")
    buff_cost_scrap: float = Field(default=0, ge=0,
                                    description="Scrap cost per buff for this tier")


class KeyCardTier(BaseModel):
    """Key card merge progression for one tier."""

    name: str
    cards_required: int = Field(default=0, ge=0, description="Lower-tier cards needed to merge")
    merge_cost_nuts: float = Field(default=0, ge=0, description="Nuts cost to merge")
    instance_tier: str = Field(description="Which instance tier this card unlocks")


class BattlePassParams(BaseModel):
    """Battle Pass season parameters."""

    cost_coins: float = Field(default=5.0, ge=0, description="Coin cost to buy the pass")
    season_days: int = Field(default=90, gt=0, description="Season length in days")
    coins_returned: float = Field(default=5.0, ge=0,
                                   description="Coins earned back if pass is completed")
    nuts_reward_total: float = Field(default=500.0, ge=0,
                                      description="Total nuts from BP rewards over season")
    scrap_reward_total: float = Field(default=1000.0, ge=0,
                                       description="Total scrap from BP rewards over season")
    keycards_rewarded: int = Field(default=10, ge=0,
                                    description="Total bronze keycards rewarded over season")
    xp_to_complete: float = Field(default=10000.0, gt=0,
                                   description="Total XP needed to complete the battle pass")
    gear_reward_count: int = Field(default=5, ge=0,
                                    description="Number of gear items rewarded over season")
    gear_avg_value_usd: float = Field(default=3.0, ge=0,
                                       description="Avg USD value per gear item reward")
    completion_rate: float = Field(default=0.3, ge=0.0, le=1.0,
                                    description="Fraction of BP buyers who complete it")
    purchase_rate: float = Field(default=0.1, ge=0.0, le=1.0,
                                  description="Fraction of DAU that buy the BP")


class EconomyParams(BaseModel):
    """Full economy configuration."""

    instances_per_day: int = Field(default=3, gt=0, description="Max instance runs per player per day")
    coin_to_usd: float = Field(default=1.0, gt=0, description="Exchange rate: 1 Coin = X USD")
    seed_coins: float = Field(default=5.0, ge=0, description="Starting coins for new player")
    seed_nuts: float = Field(default=1000.0, ge=0, description="Starting nuts for new player")
    seed_scrap: float = Field(default=1000.0, ge=0, description="Starting scrap for new player")
    seed_keycards: int = Field(default=5, ge=0, description="Starting bronze keycards for new player")
    buffs_per_run: float = Field(default=1.0, ge=0, description="Avg buffs consumed per instance run")
    upgrade_cost_scrap: float = Field(default=100.0, ge=0, description="Scrap per upgrade (placeholder)")
    outfit_price_usd: float = Field(default=7.0, gt=0, description="Outfit price (VR baseline)")
    character_price_usd: float = Field(default=20.0, gt=0, description="Character skin price (VR baseline)")

    instance_tiers: list[InstanceTier] = Field(default_factory=lambda: [
        InstanceTier(name="common",    nuts_earned=30,  scrap_earned=50,  coins_earned=0.5, xp_earned=50,  gear_value_usd=0.10, bronze_kc_drops=0.3, buff_cost_scrap=25),
        InstanceTier(name="uncommon",  nuts_earned=60,  scrap_earned=100, coins_earned=1.0, xp_earned=80,  gear_value_usd=0.25, bronze_kc_drops=0.5, buff_cost_scrap=50),
        InstanceTier(name="rare",      nuts_earned=100, scrap_earned=175, coins_earned=2.0, xp_earned=120, gear_value_usd=0.75, bronze_kc_drops=0.8, buff_cost_scrap=100),
        InstanceTier(name="epic",      nuts_earned=150, scrap_earned=275, coins_earned=4.0, xp_earned=180, gear_value_usd=2.00, bronze_kc_drops=1.2, buff_cost_scrap=200),
        InstanceTier(name="legendary", nuts_earned=225, scrap_earned=400, coins_earned=8.0, xp_earned=300, gear_value_usd=5.00, bronze_kc_drops=2.0, buff_cost_scrap=400),
    ])

    keycard_tiers: list[KeyCardTier] = Field(default_factory=lambda: [
        KeyCardTier(name="bronze",    cards_required=0,  merge_cost_nuts=0,   instance_tier="common"),
        KeyCardTier(name="silver",    cards_required=2,  merge_cost_nuts=100, instance_tier="uncommon"),
        KeyCardTier(name="gold",      cards_required=4,  merge_cost_nuts=200, instance_tier="rare"),
        KeyCardTier(name="mithril",   cards_required=8,  merge_cost_nuts=400, instance_tier="epic"),
        KeyCardTier(name="vibranium", cards_required=16, merge_cost_nuts=800, instance_tier="legendary"),
    ])

    battle_pass: BattlePassParams = Field(default_factory=BattlePassParams)
