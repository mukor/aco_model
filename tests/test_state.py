"""Tests for shared state file."""

import json

import numpy as np
import pytest

from aco_model.models import MonetizationParams, RetentionCurve
from aco_model.retention import load_installs, simulate
from aco_model.state import SimState, load_state, save_state


@pytest.fixture
def sample_installs_file(tmp_path):
    path = tmp_path / "installs.txt"
    path.write_text("day\tinstalls\n1\t1000\n2\t1000\n3\t1000\n")
    return path


@pytest.fixture
def sim_result(sample_installs_file):
    installs = load_installs(sample_installs_file)
    return simulate(installs, RetentionCurve(), sim_days=10)


@pytest.fixture
def state_path(tmp_path):
    return tmp_path / "state.json"


class TestSaveState:
    def test_creates_file(self, sim_result, state_path):
        save_state(sim_result, RetentionCurve().anchors, path=state_path)
        assert state_path.exists()

    def test_valid_json(self, sim_result, state_path):
        save_state(sim_result, RetentionCurve().anchors, path=state_path)
        data = json.loads(state_path.read_text())
        assert "dau" in data
        assert "retention_anchors" in data
        assert "updated_at" in data

    def test_creates_parent_dirs(self, sim_result, tmp_path):
        deep_path = tmp_path / "a" / "b" / "state.json"
        save_state(sim_result, RetentionCurve().anchors, path=deep_path)
        assert deep_path.exists()

    def test_saves_monetization(self, sim_result, state_path):
        params = MonetizationParams(pct_payers=0.07, arppu=3.00)
        save_state(sim_result, RetentionCurve().anchors, monetization=params, path=state_path)
        data = json.loads(state_path.read_text())
        assert data["monetization"]["pct_payers"] == 0.07
        assert data["monetization"]["arppu"] == 3.00

    def test_defaults_monetization(self, sim_result, state_path):
        save_state(sim_result, RetentionCurve().anchors, path=state_path)
        data = json.loads(state_path.read_text())
        assert data["monetization"]["pct_payers"] == 0.03


class TestLoadState:
    def test_missing_file_returns_none(self, tmp_path):
        result = load_state(tmp_path / "nonexistent.json")
        assert result is None

    def test_roundtrip(self, sim_result, state_path):
        anchors = [(0, 100.0), (1, 35.0), (7, 15.0), (30, 3.0), (90, 0.5), (180, 0.0)]
        params = MonetizationParams(pct_payers=0.05, arppu=2.50)
        save_state(sim_result, anchors, monetization=params, path=state_path)

        state = load_state(state_path)
        assert state is not None
        assert state.retention_anchors == anchors
        assert state.monetization.pct_payers == 0.05
        assert state.monetization.arppu == 2.50
        assert state.sim_days == 10

    def test_dau_preserved(self, sim_result, state_path):
        save_state(sim_result, RetentionCurve().anchors, path=state_path)
        state = load_state(state_path)
        np.testing.assert_array_equal(state.dau, sim_result.dau)

    def test_dau_length(self, sim_result, state_path):
        save_state(sim_result, RetentionCurve().anchors, path=state_path)
        state = load_state(state_path)
        assert len(state.dau) == sim_result.sim_days

    def test_updated_at_present(self, sim_result, state_path):
        save_state(sim_result, RetentionCurve().anchors, path=state_path)
        state = load_state(state_path)
        assert len(state.updated_at) > 0
