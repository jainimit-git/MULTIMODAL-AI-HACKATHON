"""
Unit tests for configuration loading and validation.
"""
from src.utils.config_loader import load_config


def test_load_default_config():
    config = load_config()
    assert "system" in config
    assert config["system"]["name"] == "AEROSIS"
    assert "satellites" in config
    assert config["satellites"]["sentinel1"]["same_orbit_track_required"] is True


def test_load_trishuli_config():
    config = load_config("config/trishuli.yaml")
    assert "event" in config
    assert config["event"]["name"] == "August 2026 Trishuli Debris Flood"
    assert config["aoi"]["bbox"] == [85.15, 27.85, 85.45, 28.25]
    assert config["validation"]["reference_layer"] == "EMSR927"
    assert config["validation"]["never_use_as_input"] is True


def test_load_judge_mode_config():
    config = load_config("config/judge_mode.yaml")
    assert config["mode"] == "judge_live_evaluation"
    assert config["defaults"]["auto_select_same_orbit"] is True
