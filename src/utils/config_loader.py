"""
YAML and environment configuration loader.
"""
from typing import Dict, Any, Optional
import os
import yaml
from pathlib import Path


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Loads configuration YAML files, starting from default.yaml and layering
    event-specific configurations if provided.
    """
    base_dir = Path(__file__).parent.parent.parent
    default_config_path = base_dir / "config" / "default.yaml"

    config: Dict[str, Any] = {}
    if default_config_path.exists():
        with open(default_config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

    if config_path:
        override_path = Path(config_path)
        if not override_path.is_absolute():
            override_path = base_dir / config_path
        
        if override_path.exists():
            with open(override_path, "r", encoding="utf-8") as f:
                override_data = yaml.safe_load(f) or {}
                config = _deep_update(config, override_data)
        else:
            raise FileNotFoundError(f"Config file not found at {override_path}")

    # Environment variable overrides
    if "COPERNICUS_CLIENT_ID" in os.environ:
        config.setdefault("satellites", {}).setdefault("copernicus_cdse", {})["client_id"] = os.environ["COPERNICUS_CLIENT_ID"]
    if "COPERNICUS_CLIENT_SECRET" in os.environ:
        config.setdefault("satellites", {}).setdefault("copernicus_cdse", {})["client_secret"] = os.environ["COPERNICUS_CLIENT_SECRET"]

    return config


def _deep_update(base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively updates a nested dictionary.
    """
    for k, v in update_dict.items():
        if isinstance(v, dict) and k in base_dict and isinstance(base_dict[k], dict):
            base_dict[k] = _deep_update(base_dict[k], v)
        else:
            base_dict[k] = v
    return base_dict
