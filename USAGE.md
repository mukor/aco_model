# Usage

## Installation

```bash
mkvirtualenv -p python3 aco_model
pip install -e ".[dev,notebook]"
setvirtualenvproject
```

Future sessions: `workon aco_model`

## CLI Commands

All commands read from `config.yaml` by default. Override with `--config path/to/config.yaml`.

### aco simulate

Run the retention simulation and display DAU projections.

```bash
aco simulate
aco simulate --output output/custom.csv
aco simulate --config my_config.yaml
```

**Output:** Rich table (Day, New Installs, DAU) + CSV file at `output/retention_sim.csv`.

### aco revenue

Estimate revenue from the DAU simulation using % payers and ARPPU assumptions.

```bash
aco revenue
aco revenue --pct-payers 0.05
aco revenue --arppu 2.50
aco revenue --pct-payers 0.05 --arppu 2.50
```

CLI flags override `config.yaml` values without editing the file.

**Output:** Rich table (Day, DAU, Payers, Daily Rev, Cumulative Rev) + CSV file at `output/revenue_estimate.csv`. Summary includes Total Revenue, ARPDAU, and Avg Revenue per Cohort.

**Key metrics:**
- **ARPDAU** — average revenue per daily active user (`pct_payers × ARPPU`)
- **Avg Lifetime Rev per Payer** — total revenue / total unique payers. Reflects how much a paying user generates over their retained lifetime, not just a single day.
- **Revenue per Cohort** — lifetime revenue attributed to each daily install cohort

### aco economy

Simulate currency flows across the game economy.

```bash
aco economy
```

**Output:** Instance economics table (per-tier value in/out), keycard progression table, and daily currency flow summary. CSV at `output/economy_sim.csv`.

## Configuration

Edit `config.yaml` in the project root:

```yaml
# Retention curve anchor points: (day, retention%)
retention:
  anchors:
    - [0, 100.0]    # install day
    - [1, 40.0]     # D1 retention
    - [7, 20.0]     # D7 retention
    - [30, 5.0]     # D30 retention
    - [90, 1.0]     # D90 retention
    - [180, 0.0]    # hard churn

# Revenue assumptions
monetization:
  pct_payers: 0.03   # 3% of DAU are payers
  arppu: 1.50         # $1.50/day per paying user

# Economy — currencies, instances, keycards, Battle Pass
economy:
  instances_per_day: 3
  coin_to_usd: 1.0
  instance_tiers:
    - {name: common,    nuts_earned: 30,  scrap_earned: 50,  coins_earned: 0.5, gear_value_usd: 0.10, keycard_drop_chance: 0.1}
    - {name: uncommon,  nuts_earned: 60,  scrap_earned: 100, coins_earned: 1.0, gear_value_usd: 0.25, keycard_drop_chance: 0.08}
    - {name: rare,      nuts_earned: 100, scrap_earned: 175, coins_earned: 2.0, gear_value_usd: 0.75, keycard_drop_chance: 0.06}
    - {name: epic,      nuts_earned: 150, scrap_earned: 275, coins_earned: 4.0, gear_value_usd: 2.00, keycard_drop_chance: 0.04}
    - {name: legendary, nuts_earned: 225, scrap_earned: 400, coins_earned: 8.0, gear_value_usd: 5.00, keycard_drop_chance: 0.02}
  keycard_tiers:
    - {name: bronze,    cards_required: 0,  merge_cost_nuts: 0,   instance_tier: common}
    - {name: silver,    cards_required: 2,  merge_cost_nuts: 100, instance_tier: uncommon}
    - {name: gold,      cards_required: 4,  merge_cost_nuts: 200, instance_tier: rare}
    - {name: mithril,   cards_required: 8,  merge_cost_nuts: 400, instance_tier: epic}
    - {name: vibranium, cards_required: 16, merge_cost_nuts: 800, instance_tier: legendary}
  battle_pass:
    cost_coins: 5.0
    season_days: 60
    completion_rate: 0.3
    purchase_rate: 0.1

viral:
  enabled: false           # k-factor off by default
  k_factor: 0.3            # invites per install over the whole window
  viral_window_days: 7     # how long after install a user keeps inviting

installs_path: data/installs.txt
sim_days: 90
```

### Install Data

`data/installs.txt` is a tab-separated file with daily install counts:

```
day	installs
1	15000
2	13000
3	12000
...
90	7500
```

## Viral Growth (K-Factor)

The retention sim supports an optional viral lineage on top of the organic install series. When enabled, each install generates additional installs over a short window, which themselves generate more installs — recursively — and feed into the same retention curve.

### Interpretation

- **`k_factor`** — invites per install over the **entire** viral window (one-shot total, *not* per day). Example: `k = 0.3, window = 7` means a new player generates 0.3 installs spread across their first 7 days.
- **`viral_window_days`** — how long after install a user keeps inviting. Real-world mobile virality is heavily front-loaded, so the default is 7.

### The math

Each cohort `c` contributes viral installs on simulation day `d` based on how many of its members are still retained:

```
viral_emit(c, d) = installs[c] · R(d - c) · (k / W)    for 1 ≤ d - c ≤ W
                   0                                    otherwise
```

where `R(age)` is the retention rate at the given age (from the retention curve), `W` is `viral_window_days`, and `k` is `k_factor`.

The total installs on day `d` are:

```
total_installs[d] = organic_installs[d] + Σ_c viral_emit(c, d)
```

`total_installs[d]` becomes a new cohort, which itself begins emitting viral installs on day `d+1`. Viral cohorts are tagged at creation so their downstream DAU stays separable in the charts.

### Why retention-weighted

A user who churned on day 2 doesn't invite anyone on day 5. Multiplying by `R(d - c)` means churned users stop contributing — the effective k-factor is always lower than the nominal `k`:

```
k_effective ≈ k · (average retention over the viral window)
```

So with `k = 0.3` and a window where average retention is ~50%, the realized lift per install is about 0.15.

### Stability

The viral lineage converges as long as `k · R̄_window < 1`. Above that threshold the model goes super-exponential — which is intentional, so you can see the takeoff point in the DAU chart.

### Nominal vs effective k

`k_factor` in the model is **nominal** — it describes player behavior assuming a fully retained player ("if a player stays engaged through the whole window, they generate `k` viral installs"). The model never stores or computes a separate `k_effective`; the realized number emerges at runtime when retention multiplies through the cohort math:

```
k_effective ≈ k · R̄_window
```

This is intentional: it means improving retention automatically improves viral output at the same `k`, which is how virality actually behaves. If you have analytics that quote a measured install lift and want to back into a `k_factor` value, do:

```
nominal_k ≈ desired_lift_ratio / R̄_window
```

### Translating k to invites sent

`k_factor` is the product of two things — how many invites each player sends, and how often those invites convert to installs:

```
k = sends_per_install × conversion_rate
```

So given an assumed conversion rate, you can back out the implied invite volume:

```
sends_per_install = k / conversion_rate    # nominal — what a fully-retained player would send
```

`aco_model.retention` exposes two helpers for this translation:

```python
from aco_model.retention import sends_from_k, k_from_sends

sends_from_k(0.3, 0.10)   # → 3.0 sends per install at 10% conversion
k_from_sends(4.0, 0.12)   # → 0.48 k-factor for 4 sends @ 12% conversion
```

Notebook 01 displays a live readout under the k-factor slider showing implied sends/install at 5%, 10%, and 15% conversion — useful for sanity-checking whether a chosen `k` corresponds to plausible player behavior.

Typical mobile invite→install conversion rates:

| Channel | Conversion |
|---|---|
| Cold share link (clipboard) | 3–7% |
| Native invite UI (in-app) | 8–15% |
| Direct SMS / messenger | 15–25% |

### K-factor benchmarks from real games

These are **publicly-discussed estimates**, not internal measurements — use them as rough goalposts for what's plausible, not as ground truth. Real k-factors vary by season, region, and feature releases.

| K range | What it looks like | Examples |
|---|---|---|
| **0.0 – 0.05** | No viral mechanic at all — pure paid UA loop | Most premium console ports, single-player games |
| **0.05 – 0.15** | Typical mobile F2P with a basic share button | Most casual mobile games, hyper-casual titles |
| **0.15 – 0.30** | Social features baked in: friend lists, leaderboards, gifting | Candy Crush Saga (with FB connect), Words with Friends, Clash of Clans |
| **0.30 – 0.50** | Strong social loop — co-op play, clans, gift economies | Clash Royale, Pokémon GO (steady-state), Monopoly GO |
| **0.50 – 0.80** | "Tell-a-friend" reflex baked into core gameplay | Among Us (2020 peak), Fall Guys (launch month) |
| **0.80 – 1.20** | Cultural moment — sharing IS the gameplay | Wordle (Jan 2022), Flappy Bird (Feb 2014) |
| **≥ 1.20** | Pandemic-tier; doubles weekly without paid UA | Pokémon GO launch week, ChatGPT (not a game, but the canonical example) |

A few takeaways:

- **Most successful mobile games sit in 0.1–0.3.** Above 0.5 is rare and usually temporary.
- **k > 1.0 is almost never sustainable.** It's what launches look like, not what steady-state looks like. Wordle's k crashed once everyone who'd hear about it had heard about it.
- **For ACO planning**, a realistic baseline is probably `0.1–0.2` (mobile F2P with a friend-invite button), with `0.3–0.5` as an aspirational case if the game has co-op or a gift loop. Anything above `0.6` should be modeled as a "what if we go viral" stress test, not a base case.
- **Retention shapes the achievable k.** A game with poor D7 retention can't sustain a high effective k even if the nominal k is high — there's no one left to invite. This is why retention work usually pays back more than viral-loop work in early-stage games.

### Toggle

The feature lives in two places:

- **`config.yaml`** — the `viral:` block sets the persistent default (off by default).
- **`notebooks/01_retention.ipynb`** — a checkbox + sliders override the config value for the live session. **Save as Defaults** writes the current notebook values back to `config.yaml`.

When the toggle is off, the sim falls back to the original (non-viral) fast path and produces identical results to before.

### Future: viral retention bonus

Friend-referred users typically retain better than UA-acquired users. A planned v2 enhancement adds a `viral_retention_multiplier` (e.g. `1.10`) that boosts retention rates only for viral cohorts. The implementation would store a per-cohort retention scaler and multiply `R(age) × scaler` when filling each cohort row of the matrix. Out of scope for v1.

### Future: viral monetization bonus

Friend-referred users often pay slightly more than cold UA installs (better pre-qualification). A planned v2 enhancement adds a `viral_arppu_multiplier` field on `ViralParams` (e.g. `1.10`) which would multiply `ARPPU` only for the viral lineage when computing `RevenueResult.viral_revenue`. The implementation is a one-line change at the cohort-revenue allocation site in `monetization.py` — out of scope for v1, deferred until we have a measurement to anchor the value to.

## Notebooks

Launch with JupyterLab for a tabbed interface:

```bash
jupyter lab notebooks/
```

Each notebook has a **Hide Code** button to collapse code cells, and **Reset to Defaults** / **Save as Defaults** buttons to manage config values.

### Shared State

The notebooks share state via `output/state.json`. When you adjust sliders in one notebook, the state file is updated. Re-run cell 1 in other notebooks to pick up changes.

- **Notebook 01** writes: retention anchors + DAU array
- **Notebook 02** reads: retention/DAU from state, writes: monetization params
- **Notebook 03** reads: retention/DAU from state, writes: economy params
- Falls back to `config.yaml` defaults if no state file exists

### 01_retention.ipynb

Interactive retention and DAU exploration.

- **Retention Curve** — sliders for D1, D7, D30, D90 retention targets. Plots update live (linear + log scale). Reset/Save to Defaults buttons persist to config.yaml.
- **DAU Simulation** — DAU vs new installs chart, linked to the retention sliders.
- **365-Day Projection** — extends installs at the last observed rate. Shows actual vs projected regions.
- **D1 Sensitivity** — overlaid DAU curves for different D1 retention values.
- **Cohort Heatmap** — retained users by cohort and simulation day.
- **K-Factor Toggle** — checkbox to enable viral installs, with `k_factor` and `viral_window_days` sliders. When on: DAU and daily-installs charts switch to stacked organic/viral layers, a viral-share line is added, and a dashed `k=0` baseline is overlaid for comparison. See [Viral Growth (K-Factor)](#viral-growth-k-factor) for the math.

### 02_monetization.ipynb

Revenue projections built on the DAU simulation. Loads retention/DAU from shared state.

- **Revenue Estimation** — sliders for % payers (0.5–15%) and ARPPU ($0.25–$50). Three charts: daily revenue, cumulative revenue, ARPDAU. Summary includes avg lifetime revenue per payer, total payers, and avg revenue per cohort. Reset/Save to Defaults buttons.
- **Revenue Sensitivity** — side-by-side charts showing impact of varying % payers and ARPPU independently.
- **Revenue per Install Cohort** — bar charts showing lifetime revenue and revenue-per-install for each daily cohort.
- **Combined View** — DAU and daily revenue overlaid on the same chart.
- **K-Factor pass-through** — viral params are inherited from `output/state.json` (set in notebook 01). When viral is enabled, the daily and cumulative revenue charts switch to stacked organic/viral layers with a dashed `k=0` baseline overlay, the cohort revenue bars are color-coded by origin, and the summary prints organic vs viral revenue split plus the viral lift % over baseline.

### 03_economy.ipynb

Currency flow simulation for the Animal Company economy. Loads retention/DAU from shared state.

- **Resource Values & Exchange Rates** — input fields for USD value of coins, nuts, scrap. Cross-rate exchange table. Reset/Save to Defaults buttons.
- **Key Card Costs** — set bronze coin price (higher tiers cascade automatically). Per-tier merge cost in nuts, cards required, and derived $ value including cascading merge fees.
- **Instance Loot** — per-tier editable outputs: nuts, scrap, coins, gear value ($), keycard drop %. All values flow into instance economics calculations.
- **Instance Value per Run (USD)** — table and charts showing value-in vs value-out per tier, including coins and gear drops. Net profit/loss per run.
- **Currency Flows** — daily nuts/scrap earned vs spent, keycard consumption.
- **Wallet Balances** — cumulative currency in system over time + avg per player.
- **Key Card Progression** — merge cost escalation, cumulative investment, days-to-afford per tier.
- **Battle Pass Economics** — cumulative BP revenue, net revenue by completion rate, player ROI breakdown.

## Tests

### Running Tests

```bash
pytest                    # run all tests (117 total)
pytest -m "not slow"      # fast — unit tests only (114 tests, <1s)
pytest -m slow            # notebook smoke tests only (3 tests, ~10s)
pytest -v                 # verbose output
```

### Test Modules

| Module | Tests | What it covers |
|--------|-------|----------------|
| `tests/test_retention.py` | 49 | Retention curve, install loading, SimResult, cohort matrix |
| `tests/test_monetization.py` | 29 | MonetizationParams, RevenueResult, ARPDAU, cohort revenue |
| `tests/test_economy.py` | 23 | EconomyParams, currency flows, instance economics, keycard progression |
| `tests/test_config.py` | 11 | Config loading, YAML parsing, defaults, monetization config |
| `tests/test_state.py` | 10 | Shared state save/load roundtrip, DAU preservation |
| `tests/test_notebooks.py` | 3 | Headless execution of all notebooks (marked `slow`) |

### Notebook Smoke Tests

The notebook tests (`tests/test_notebooks.py`) run each notebook headless via `jupyter nbconvert --execute` and verify no cells throw exceptions. This catches:

- Import errors
- Missing variables from cells run out of order
- Wrong function signatures
- Config/data loading failures

Notebooks detect headless mode via `ACO_HEADLESS=1` env var (set by the test). In headless mode, plot functions are called directly instead of through widget bindings, avoiding widget event loop hangs.

To run just the notebook tests:

```bash
pytest tests/test_notebooks.py -v
```

## Output Files

All generated output goes to the `output/` directory:

| File | Generated by |
|------|-------------|
| `output/retention_sim.csv` | `aco simulate` |
| `output/revenue_estimate.csv` | `aco revenue` |
| `output/economy_sim.csv` | `aco economy` |
| `output/state.json` | Notebook sliders (shared state) |
