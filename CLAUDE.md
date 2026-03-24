# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Session Start

**At the start of each session, ask which development system is being used:**

| System | OS | Hardware |
|--------|-----|----------|
| **Desktop** | Windows 11 / WSL2 Ubuntu 22.04 | AMD 5950x, 32GB RAM, 3080 Ti |
| **Framework 16** | Ubuntu 25.1 | AMD AI 300, 64GB RAM, 5070 |
| **MacBook Pro** | macOS | M4 Max 16-core, 128GB RAM, 40-core GPU |

This affects paths, GPU availability, and testing approaches.

## Project Overview

aco_model is a game economic model built in Python. It simulates and analyzes game economies with support for multiple interfaces: CLI (primary), web (FastAPI), and curses (terminal UI).

**Current State:** Initial scaffolding. Core models and simulation engine not yet implemented.

## Technology Stack

- **Language:** Python 3.10+
- **Build:** Hatchling
- **CLI:** Typer + Rich
- **Web:** FastAPI + Uvicorn (optional)
- **TUI:** curses (optional)
- **Models:** Pydantic
- **Config:** YAML (PyYAML)

## Architecture

```
src/aco_model/
├── __init__.py   - Package root
├── cli.py        - Typer CLI entry point
├── config.py     - Configuration loading/validation
├── engine.py     - Core simulation engine
└── models.py     - Pydantic models for game economy
tests/
└── test_config.py
```

## Commands

```bash
# Install (editable)
pip install -e ".[dev]"

# Install with web interface
pip install -e ".[dev,web]"

# Run CLI
aco run
aco status

# Tests
pytest
```

## Configuration

`config.yaml` in the project root. Schema TBD as the model takes shape.
