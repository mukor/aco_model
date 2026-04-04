"""Tests for configuration loading."""

from pathlib import Path

import pytest

from aco_model.config import Config, load_config
from aco_model.models import MonetizationParams, RetentionCurve


class TestConfig:
    def test_default_config(self):
        config = load_config()
        assert isinstance(config, Config)

    def test_default_retention_curve(self):
        config = load_config()
        assert isinstance(config.retention, RetentionCurve)
        assert len(config.retention.anchors) == 6

    def test_default_sim_days(self, tmp_path):
        """Test that missing sim_days uses model default (90)."""
        cfg_path = tmp_path / "test.yaml"
        cfg_path.write_text("monetization: {pct_payers: 0.03, arppu: 1.5}\n")
        config = load_config(cfg_path)
        assert config.sim_days == 90

    def test_default_installs_path(self):
        config = load_config()
        assert config.installs_path == Path("data/installs.txt")

    def test_missing_config_file_uses_defaults(self, tmp_path):
        config = load_config(tmp_path / "nonexistent.yaml")
        assert isinstance(config, Config)
        assert config.sim_days == 90

    def test_custom_config_file(self, tmp_path):
        cfg_path = tmp_path / "test.yaml"
        cfg_path.write_text("sim_days: 180\n")
        config = load_config(cfg_path)
        assert config.sim_days == 180

    def test_custom_retention_in_config(self, tmp_path):
        cfg_path = tmp_path / "test.yaml"
        cfg_path.write_text(
            "retention:\n"
            "  anchors:\n"
            "    - [0, 100.0]\n"
            "    - [1, 50.0]\n"
            "    - [30, 0.0]\n"
        )
        config = load_config(cfg_path)
        assert len(config.retention.anchors) == 3
        assert config.retention.anchors[1] == (1, 50.0)

    def test_partial_config_keeps_defaults(self, tmp_path):
        cfg_path = tmp_path / "test.yaml"
        cfg_path.write_text("sim_days: 365\n")
        config = load_config(cfg_path)
        assert config.sim_days == 365
        # Retention should still have defaults
        assert len(config.retention.anchors) == 6

    def test_default_monetization(self, tmp_path):
        """Test that missing monetization section uses model defaults."""
        cfg_path = tmp_path / "test.yaml"
        cfg_path.write_text("sim_days: 90\n")
        config = load_config(cfg_path)
        assert isinstance(config.monetization, MonetizationParams)
        assert config.monetization.pct_payers == 0.03
        assert config.monetization.arppu == 1.50

    def test_custom_monetization_in_config(self, tmp_path):
        cfg_path = tmp_path / "test.yaml"
        cfg_path.write_text(
            "monetization:\n"
            "  pct_payers: 0.05\n"
            "  arppu: 2.00\n"
        )
        config = load_config(cfg_path)
        assert config.monetization.pct_payers == 0.05
        assert config.monetization.arppu == 2.00

    def test_missing_monetization_uses_defaults(self, tmp_path):
        cfg_path = tmp_path / "test.yaml"
        cfg_path.write_text("sim_days: 90\n")
        config = load_config(cfg_path)
        assert config.monetization.pct_payers == 0.03
