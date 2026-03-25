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
    keycard_drop_chance: float = Field(default=0.0, ge=0.0, le=1.0,
                                       description="Chance of getting a keycard back")


class KeyCardTier(BaseModel):
    """Key card merge progression for one tier."""

    name: str
    cards_required: int = Field(default=0, ge=0, description="Lower-tier cards needed to merge")
    merge_cost_nuts: float = Field(default=0, ge=0, description="Nuts cost to merge")
    instance_tier: str = Field(description="Which instance tier this card unlocks")


class BattlePassParams(BaseModel):
    """Battle Pass season parameters."""

    cost_coins: float = Field(default=5.0, ge=0, description="Coin cost to buy the pass")
    season_days: int = Field(default=60, gt=0, description="Season length in days")
    coins_returned: float = Field(default=5.0, ge=0,
                                   description="Coins earned back if pass is completed")
    nuts_reward_total: float = Field(default=500.0, ge=0,
                                      description="Total nuts from BP rewards over season")
    scrap_reward_total: float = Field(default=1000.0, ge=0,
                                       description="Total scrap from BP rewards over season")
    keycards_rewarded: int = Field(default=10, ge=0,
                                    description="Total keycards rewarded over season")
    completion_rate: float = Field(default=0.3, ge=0.0, le=1.0,
                                    description="Fraction of BP buyers who complete it")
    purchase_rate: float = Field(default=0.1, ge=0.0, le=1.0,
                                  description="Fraction of DAU that buy the BP")


class EconomyParams(BaseModel):
    """Full economy configuration."""

    instances_per_day: int = Field(default=3, gt=0, description="Instance runs per player per day")
    coin_to_usd: float = Field(default=1.0, gt=0, description="Exchange rate: 1 Coin = X USD")
    buff_cost_scrap: float = Field(default=50.0, ge=0, description="Scrap per buff (placeholder)")
    upgrade_cost_scrap: float = Field(default=100.0, ge=0, description="Scrap per upgrade (placeholder)")
    buffs_per_run: float = Field(default=1.0, ge=0, description="Avg buffs consumed per instance run")
    outfit_price_usd: float = Field(default=7.0, gt=0, description="Outfit price (VR baseline)")
    character_price_usd: float = Field(default=20.0, gt=0, description="Character skin price (VR baseline)")

    instance_tiers: list[InstanceTier] = Field(default_factory=lambda: [
        InstanceTier(name="bronze",    nuts_earned=30,  scrap_earned=50,  keycard_drop_chance=0.10),
        InstanceTier(name="silver",    nuts_earned=60,  scrap_earned=100, keycard_drop_chance=0.08),
        InstanceTier(name="gold",      nuts_earned=100, scrap_earned=175, keycard_drop_chance=0.06),
        InstanceTier(name="mithril",   nuts_earned=150, scrap_earned=275, keycard_drop_chance=0.04),
        InstanceTier(name="vibranium", nuts_earned=225, scrap_earned=400, keycard_drop_chance=0.02),
    ])

    keycard_tiers: list[KeyCardTier] = Field(default_factory=lambda: [
        KeyCardTier(name="common",    cards_required=0,  merge_cost_nuts=0,   instance_tier="bronze"),
        KeyCardTier(name="uncommon",  cards_required=2,  merge_cost_nuts=100, instance_tier="silver"),
        KeyCardTier(name="rare",      cards_required=4,  merge_cost_nuts=200, instance_tier="gold"),
        KeyCardTier(name="epic",      cards_required=8,  merge_cost_nuts=400, instance_tier="mithril"),
        KeyCardTier(name="legendary", cards_required=16, merge_cost_nuts=800, instance_tier="vibranium"),
    ])

    battle_pass: BattlePassParams = Field(default_factory=BattlePassParams)
