# ACO Model Roadmap

Game economic model for Animal Company mobile conversion.

## Phase 1: Retention Foundation (Complete)

- [x] Cohort-based retention simulation
- [x] Configurable retention curve (anchor-point interpolation: D1/D7/D30/D90 targets)
- [x] Daily install ingestion from data file
- [x] DAU calculation across stacked cohorts
- [x] Per-cohort tracking via SimResult (cohort matrix, individual cohort access)
- [x] CLI output with Rich tables
- [x] CSV export
- [x] Test suite (49 tests)

## Phase 2: Visualization & Exploration (Complete)

- [x] Jupyter notebook for interactive exploration (`notebooks/01_retention.ipynb`)
  - [x] Retention curve with interactive sliders (D1/D7/D30/D90)
  - [x] DAU simulation linked to sliders
  - [x] 365-day extended projection with actual vs projected shading
  - [x] D1 sensitivity analysis
  - [x] Cohort heatmap
- [x] Add matplotlib + jupyter as project dependencies
- [x] Monetization notebook (`notebooks/02_monetization.ipynb`)
  - [x] Revenue estimation with interactive sliders (% payers, ARPPU)
  - [x] ARPDAU, lifetime revenue per payer, cohort revenue
  - [x] Sensitivity analysis, combined DAU + revenue view
- [x] Shared state file (`output/state.json`) for cross-notebook communication
- [x] Hide Code toggle button, Save/Reset to Defaults buttons
- [ ] Notebook templates for common analyses

## Phase 3: Currency & Economy (Complete)

> **Reference:** `animalco_economy.md` in brain-rag vault — currency definitions,
> taps/sinks, Battle Pass design, Key Card merging tiers.
> VR baseline data in `2026-03-25.md` daily note (pricing, LTV, ARPPU from Spatial).

### Design Decisions
- Key Card merge cost paid in **Nuts** (not Coins)
- Battle Pass costs **5 Coins ($5)**, 90-day season, returns all coins if completed
- 1 Key Card consumed per instance run
- Mobile pricing starts with **VR baseline** ($7 outfits, $15-$20 characters), tunable in notebooks
- New players seeded with **5 coins, 1000 nuts, 1000 scrap**
- XP modeled as **avg per tier** (50/80/120/180/300), combining quest + instance XP
- Player progression uses **greedy tier advancement** — merge up as soon as affordable
- Non-payers modeled on earning side only; economy balanced so common/uncommon achievable without BP, higher tiers need BP
- BP and sim days are **independent** — sim runs 180 days (2 seasons), BP season is 90 days
- Spender profiles defined by **purchase spend ($)** — coin spend as proxy

### Implementation
- [x] Currency models: InstanceTier (with XP), KeyCardTier, BattlePassParams (with XP/gear), EconomyParams (with seed currency)
- [x] Source/sink definitions per currency (Nuts, Scrap, Coins flows)
- [x] Per-instance currency flow: value-in vs value-out by tier (USD)
- [x] Key Card cost grid: bronze coin cost cascades to higher tiers, includes merge fees
- [x] Instance loot grid: nuts, scrap, coins, XP, gear, keycard drop % per tier
- [x] Single-player progression engine (`simulate_player_progression`): deterministic, greedy, BP holder variant
- [x] Wallet balance tracking: per-player-day (non-payer vs BP holder, with tier-up markers)
- [x] Total Economy Balance: daily earn/spend + cumulative per currency (sim-day x-axis)
- [x] Key Card Progression: runs-to-afford and days-to-afford each tier
- [x] Battle Pass Economics: XP analysis by spender profile, days-to-complete, payout breakdown, per-run value boost
- [x] CLI: `aco economy` command
- [x] Economy params in shared state file
- [x] Reset/Save to Defaults on all inputs
- [x] Test suite: 35 economy tests (137 total with notebook smoke tests)

### Still Pending (Sienna / Stainless)
- [ ] Additional Nut sinks beyond Key Cards
- [ ] Buff/upgrade tiers and Scrap costs

### Not Yet Implemented
- [ ] VR baseline comparison: model current VR metrics as a benchmark target
- [ ] Economy balance validation (inflation alerts when currencies accumulate too fast)
- [ ] Apply single-player progression to cohorts (multiply wallet model × DAU per cohort)
- [ ] BP season reset modeling (XP resets, currency carries over)
- [ ] Graphs by instance run number (in addition to player day)

## Phase 3.1: Event Spec (Complete)

Event specification for aco_economy telemetry: `event_spec/event_spec.md`

- [x] 9 event types: session, instance, store_purchase, battle_pass, buff, merge, quest_complete, loot_crate_open, mob_kill
- [x] Common envelope: user_id, timestamp, platform, session_id, locale (BCP 47), device_make, device_model
- [x] client_ip captured server-side by collector
- [x] JSON Schema payload definitions with example payloads
- [x] Implementation notes (buffering, timestamps, PII, partitioning)

## Phase 4: Session Modeling

- [ ] Session frequency per retention day
- [ ] Session duration curves
- [ ] Engagement depth (actions per session)
- [ ] Energy/stamina system modeling

## Phase 4.5: New User Funnel

After first beta — simulate changes in the funnel falloff graph to show effect on D1 retention.

## Phase 5: Advanced Monetization

> Basic monetization (% payers, ARPPU, ARPDAU, lifetime rev per payer) done in Phase 2.

- [ ] Player segmentation (non-payer, minnow, dolphin, whale)
- [ ] IAP conversion rates per segment
- [ ] Ad revenue modeling (rewarded, interstitial)
- [ ] LTV modeling by segment
- [ ] IAP catalog modeling (bundles, skins, Battle Pass — from VR pricing data in `2026-03-25.md`)

## Phase 6: Sensitivity Analysis

- [ ] Parameter sweep framework
- [ ] Monte Carlo simulation support
- [ ] Key metric dashboards (DAU, revenue, LTV, payback)
- [ ] Scenario comparison (optimistic/base/pessimistic)

## Phase 7: Interfaces

- [ ] Curses TUI for terminal dashboards
- [ ] FastAPI web interface for sharing results
- [ ] Interactive parameter controls
- [ ] Slack interface to spit out stats

## Tweaks & Polish

### Today

General

- [ ] Round floating point display in config.yaml (e.g., retention anchors show 5.499999 instead of 5.5)

Notebook 01: Retention Notebook

- [ ] Lengthen DAU simulation to 180 days. Extend `data/installs.txt` to 180 days of mock data.
- [ ] In DAU simulation section: add avg daily installs and avg DAU text below the chart. Use same y-axis for Installs and DAU.
- [ ] Wire 365-day projection to retention sliders (currently uses config.yaml retention)

> **Q: Mock installs for days 91-180** — the current install data has a launch spike decaying into organic growth over 90 days. For days 91-180 should we: (a) continue the organic trend from day 90, (b) flat-line at the day 90 rate, or (c) add a marketing beat / seasonal bump? I'll go with (b) unless you say otherwise.
>

go with option b

Notebook 02: Monetization 

Notebook 03: Currency and Economy

- [ ] Add a "Total Out ($)" column to the Instance Loot grid that shows the dollarized value per row, updating reactively. Should match Total Out in the Instance Value per Run (USD) table.
- [ ] Per-tier buff costs: replace single buff_cost_scrap slider with an input grid (one scrap value per tier). Wire to Reset/Save defaults.
- [ ] Instance tier breakdown graph: line chart showing how many instances a player plays per day, broken out by tier. One graph for BP players, one for non-BP. Place in Key Card Progression section.
- [ ] Fix wallet balance dependency on key card progression: currently wallets grow unbounded because the player progression sim may not be consuming resources correctly when stalled. Wallet balances should flatten or decline when player can't afford to progress.

> **Q: Per-tier buff costs** — should we also remove the single "Buff (scrap)" slider, or keep it as a global multiplier/default? I'm thinking: replace the slider entirely with the per-tier grid, default values scaling up (e.g., common=25, uncommon=50, rare=100, epic=200, legendary=400). Sound right?
>
replace with the per-tier grid.

> **Q: Instance tier breakdown graph** — the player progression sim already tracks which tier the player is on each run. To show "instances per day by tier" do you want: (a) a single player's tier over time (stepped line showing when they advance), or (b) across the whole DAU, what % of runs are at each tier on each sim day? I think (a) fits Key Card Progression since it's player-centric.
>
go with (a)

> **Q: Wallet balance fix** — I think the root issue is that `simulate_player_progression` earns resources every run but only spends on merges (greedy) and buffs. If the player can't merge (not enough cards or nuts), they just accumulate. The fix would be: once the player is at max tier they can reach, stop accumulating (or model some spending). Should we: (a) show a "stall point" marker on the wallet graphs where progression stops, (b) cap accumulation by adding other sinks (store purchases, upgrades), or (c) both?
>
Let's show a "stall point"

### Later

Small improvements that can be done independently of the main phases.

- [ ] Add weighted loot table for gear drops (replace flat avg value)
- [ ] Wallet balance graphs by instance run number (x=run, in addition to x=player_day)
- [ ] Add `aco validate` CLI command to check economy balance (currency inflation detection)
- [ ] Notebook loading indicator (show "Computing..." during _update_all)
- [ ] Export notebook state to a shareable PDF/HTML report
- [ ] Config.yaml: bring `bronze_coin_cost`, `nut_value_usd`, `scrap_value_usd` into the Pydantic model (currently raw YAML extras)

## Future Considerations

- **Group instance runs** — up to 4 players per instance, 1 keycard for the group. Drops effective keycard cost to 25% in a full group. Needs matchmaking assumptions.
- A/B test outcome modeling
- UA cost modeling and ROI/payback periods
- LiveOps event impact simulation
- Competitive benchmarking data ingestion
