# ACO Model

Game economic model for Animal Company — a Meta Quest game being converted to mobile.

Simulates player retention, DAU projections, revenue estimates, and currency flows with interactive Jupyter notebooks and a CLI.

## Requirements

- Python 3.10+
- git
- [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/) (recommended, falls back to venv)

## Quick Install

One-liner — clones into the current directory and sets everything up:

```bash
bash <(curl -sSL https://raw.githubusercontent.com/mukor/aco_model/main/install.sh)
```

Or specify an install directory:

```bash
bash <(curl -sSL https://raw.githubusercontent.com/mukor/aco_model/main/install.sh) ~/dev/aco_model
```

## Manual Setup

```bash
git clone git@github.com:mukor/aco_model.git && cd aco_model
mkvirtualenv -p python3 aco_model
pip install -e ".[dev,notebook]"
setvirtualenvproject
```

Future sessions:

```bash
workon aco_model
```

## Quick Start

Run the retention simulation:

```bash
aco simulate
```

Estimate revenue:

```bash
aco revenue
aco revenue --pct-payers 0.05 --arppu 2.50
```

Simulate the currency economy:

```bash
aco economy
```

Launch the interactive notebooks:

```bash
jupyter lab notebooks/
```

## Project Structure

```
src/aco_model/
├── cli.py            CLI commands (aco simulate, aco revenue, aco economy)
├── config.py         YAML config loading
├── models.py         Pydantic models (RetentionCurve, MonetizationParams, EconomyParams)
├── retention.py      Cohort-based retention simulation
├── monetization.py   Revenue estimation from DAU
├── economy.py        Currency flow simulation (Coins, Nuts, Scrap, Key Cards, Battle Pass)
├── state.py          Shared state file for cross-notebook communication
└── engine.py         Core simulation engine (stub)

notebooks/
├── 01_retention.ipynb      Retention curves, DAU projections, sensitivity
├── 02_monetization.ipynb   Revenue, ARPDAU, cohort revenue analysis
└── 03_economy.ipynb        Currency flows, Key Card progression, Battle Pass economics

data/
└── installs.txt      Daily install counts (tab-separated)

tests/
├── test_retention.py       Retention simulation tests
├── test_monetization.py    Revenue estimation tests
├── test_economy.py         Economy simulation tests
├── test_config.py          Configuration loading tests
├── test_state.py           Shared state tests
└── test_notebooks.py       Headless notebook execution tests

config.yaml           All model parameters (retention, monetization, economy)
```

## Configuration

Edit `config.yaml` to set retention targets, monetization assumptions, and economy parameters. See [USAGE.md](USAGE.md) for the full config reference.

## Tests

```bash
pytest                  # all tests (117)
pytest -m "not slow"    # unit tests only (~0.3s)
pytest -m slow          # notebook smoke tests (~10s)
```

## Documentation

- [USAGE.md](USAGE.md) — detailed CLI, notebook, and test documentation
- [ROADMAP.md](ROADMAP.md) — planned features and progress
