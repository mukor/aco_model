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

### Done

General

- [x] Round floating point display in config.yaml (retention Save to Defaults now rounds to 6 decimals)

Notebook 01: Retention Notebook

- [x] Extend `data/installs.txt` to 180 days (flat-line at day 90 rate)

Notebook 03: Currency and Economy

- [x] Per-tier buff costs: replaced single slider with per-tier values in Instance Loot grid (common=25→legendary=400). Wired to Reset/Save.
- [x] Fix wallet balance: player progression now consumes keycards per run. No keycards = stalled (no loot, no XP). Wallets flatten naturally.
- [x] Bronze KC drops: replaced keycard_drop_chance % with avg bronze keycards per run (fractional). Feeds merge pipeline.
- [x] Seed keycards: new players start with 5 bronze cards (settable input).
- [x] Buff costs separated into own table under Value In (not loot).
- [x] Value In / Value Out visual callouts (red/green section headers).

Notebook 01: Retention Notebook

- [x] DAU simulation: shared y-axis for installs + DAU, avg daily installs + avg DAU text.
- [x] 365-day projection wired to retention sliders (was already using slider-derived curve).

Notebook 03: Currency and Economy

- [x] Total Out ($) column in Instance Loot grid (reactive, green, matches value table).
- [x] Instance tier breakdown graph: stepped line in Key Card Progression (BP vs non-BP), red shading for stall regions.
- [x] Stall point markers on wallet balance graphs (red shading + vertical line at first stall day).
- [x] Enhanced summary: active runs %, stall day, tier-up list for both player types.

### Remaining

(all items completed)

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
