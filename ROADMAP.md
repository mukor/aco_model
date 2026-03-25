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

## Phase 3: Currency & Economy (In Progress)

> **Reference:** `animalco_economy.md` in brain-rag vault — currency definitions,
> taps/sinks, Battle Pass design, Key Card merging tiers.
> VR baseline data in `2026-03-25.md` daily note (pricing, LTV, ARPPU from Spatial).

### Answered questions
- [x] Key Card merge cost currency: **Nuts** (typo in notes corrected)
- [x] Battle Pass price: **5 Coins ($5)**
- [x] Instance runs per day: **3**
- [x] Key Card consumed per run: **yes, 1 per instance**
- [x] Battle Pass season length: **60 days**
- [x] Mobile pricing: **start with VR baseline** ($7 outfits, $15-$20 characters), tunable

### Still pending (waiting on Sienna / Stainless)
- [ ] Specific Scrap/Nuts earn rates per instance tier (using placeholders)
- [ ] Additional Nut sinks beyond Key Cards
- [ ] Item catalog and cost ranges
- [ ] Buff/upgrade tiers and Scrap costs

### Implementation
- [x] Currency models (Pydantic): InstanceTier, KeyCardTier, BattlePassParams, EconomyParams
- [x] Source/sink definitions per currency (Nuts, Scrap, Coins flows)
- [x] Per-instance currency flow: value-in vs value-out by tier
- [x] Key Card progression model (merge tree: bronze → vibranium, escalating Nut costs)
- [x] Battle Pass model: cost, season length, completion rate, breakeven analysis
- [x] Wallet balance tracking over time (per `2026-02-11_GameGou_call.md` recommendations)
- [x] Economy balance: cumulative Nuts/Scrap in system + avg per player
- [x] Notebook: `03_economy.ipynb` — 5 interactive sections with sliders
- [x] CLI: `aco economy` command with instance economics + keycard progression tables
- [x] Economy params in shared state file
- [x] Test suite: 23 economy tests (114 total)
- [ ] VR baseline comparison: model current VR metrics as a benchmark target
- [ ] Economy balance validation (inflation alerts when currencies accumulate too fast)

## Phase 4: Session Modeling

- [ ] Session frequency per retention day
- [ ] Session duration curves
- [ ] Engagement depth (actions per session)
- [ ] Energy/stamina system modeling

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

## Phase 4.5: New user funnel
After first beta...
Simulate changes in the funnel falloff graph to show effect on D1 retention.

## Future Considerations

- A/B test outcome modeling
- UA cost modeling and ROI/payback periods
- LiveOps event impact simulation
- Competitive benchmarking data ingestion
