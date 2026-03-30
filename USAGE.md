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

# Install data and simulation length
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

## Notebooks

Launch with JupyterLab for a tabbed interface:

```bash
jupyter lab notebooks/
```

### Shared State

The notebooks share state via `output/state.json`. When you adjust sliders in one notebook, the state file is updated. Re-run cell 1 in other notebooks to pick up changes.

- **Notebook 01** writes: retention anchors + DAU array
- **Notebook 02** reads: retention/DAU from state, writes: monetization params
- Falls back to `config.yaml` defaults if no state file exists

### 01_retention.ipynb

Interactive retention and DAU exploration.

- **Retention Curve** — sliders for D1, D7, D30, D90 retention targets. Plots update live (linear + log scale).
- **DAU Simulation** — DAU vs new installs chart, linked to the retention sliders. Saves state on every change.
- **365-Day Projection** — extends installs at the last observed rate. Shows actual vs projected regions.
- **D1 Sensitivity** — overlaid DAU curves for different D1 retention values.
- **Cohort Heatmap** — retained users by cohort and simulation day.

### 02_monetization.ipynb

Revenue projections built on the DAU simulation. Loads retention/DAU from shared state.

- **Revenue Estimation** — sliders for % payers (0.5–15%) and ARPPU ($0.25–$50). Three charts: daily revenue, cumulative revenue, ARPDAU. Summary includes avg lifetime revenue per payer, total payers, and avg revenue per cohort. Saves state on every change.
- **Revenue Sensitivity** — side-by-side charts showing impact of varying % payers and ARPPU independently.
- **Revenue per Install Cohort** — bar charts showing lifetime revenue and revenue-per-install for each daily cohort.
- **Combined View** — DAU and daily revenue overlaid on the same chart.

## Tests

### Running Tests

```bash
pytest                    # run all tests (114 unit + 3 notebook smoke)
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
