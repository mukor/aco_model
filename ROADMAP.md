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

## Phase 2: Visualization & Exploration (In Progress)

- [x] Jupyter notebook for interactive exploration (`notebooks/01_retention.ipynb`)
  - [x] Retention curve with interactive sliders (D1/D7/D30/D90)
  - [x] DAU simulation linked to sliders
  - [x] 365-day extended projection with actual vs projected shading
  - [x] D1 sensitivity analysis
  - [x] Cohort heatmap
- [x] Add matplotlib + jupyter as project dependencies
- [ ] Notebook templates for common analyses

## Phase 3: Monetization Layer

- [ ] Player segmentation (non-payer, minnow, dolphin, whale)
- [ ] IAP conversion rates per segment
- [ ] Ad revenue modeling (rewarded, interstitial)
- [ ] ARPDAU / ARPU / LTV calculations
- [ ] Revenue projections overlaid on DAU

## Phase 4: Currency & Economy

- [ ] Currency definitions (soft currency, hard currency)
- [ ] Source/sink modeling per currency
- [ ] Economy balance validation (inflation detection)
- [ ] Progression-gated currency flow

## Phase 5: Session Modeling

- [ ] Session frequency per retention day
- [ ] Session duration curves
- [ ] Engagement depth (actions per session)
- [ ] Energy/stamina system modeling

## Phase 6: Sensitivity Analysis

- [ ] Parameter sweep framework
- [ ] Monte Carlo simulation support
- [ ] Key metric dashboards (DAU, revenue, LTV, payback)
- [ ] Scenario comparison (optimistic/base/pessimistic)

## Phase 7: Interfaces

- [ ] Curses TUI for terminal dashboards
- [ ] FastAPI web interface for sharing results
- [ ] Interactive parameter controls

## Future Considerations

- A/B test outcome modeling
- UA cost modeling and ROI/payback periods
- LiveOps event impact simulation
- Competitive benchmarking data ingestion
