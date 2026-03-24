# ACO Model

Game economic model for Animal Company — a Meta Quest game being converted to mobile.

Simulates player retention, DAU projections, and revenue estimates with interactive Jupyter notebooks and a CLI.

## Requirements

- Python 3.10+
- [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/)

## Setup

```bash
git clone <repo-url> && cd aco_model
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

Launch the interactive notebooks:

```bash
jupyter lab notebooks/
```

## Project Structure

```
src/aco_model/
├── cli.py            CLI commands (aco simulate, aco revenue)
├── config.py         YAML config loading
├── models.py         Pydantic models (RetentionCurve, MonetizationParams)
├── retention.py      Cohort-based retention simulation
├── monetization.py   Revenue estimation from DAU
├── state.py          Shared state file for cross-notebook communication
└── engine.py         Core simulation engine (stub)

notebooks/
├── 01_retention.ipynb      Retention curves, DAU projections, sensitivity
└── 02_monetization.ipynb   Revenue, ARPDAU, cohort revenue analysis

data/
└── installs.txt      Daily install counts (tab-separated)

config.yaml           Retention and monetization parameters
```

## Configuration

Edit `config.yaml` to set retention targets and monetization assumptions:

```yaml
retention:
  anchors:
    - [0, 100.0]
    - [1, 40.0]     # D1 retention
    - [7, 20.0]     # D7 retention
    - [30, 5.0]     # D30 retention
    - [90, 1.0]     # D90 retention
    - [180, 0.0]    # hard churn

monetization:
  pct_payers: 0.03   # 3% of DAU
  arppu: 1.50         # $/day per payer

installs_path: data/installs.txt
sim_days: 90
```

## Tests

```bash
pytest
```

## Documentation

See [USAGE.md](USAGE.md) for detailed CLI and notebook documentation, and [ROADMAP.md](ROADMAP.md) for planned features.
