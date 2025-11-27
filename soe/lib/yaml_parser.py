"""YAML parsing utilities."""

import yaml
from typing import Dict, Any, Union


def parse_yaml(data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Parse YAML string to dict, or return dict as-is."""
    if isinstance(data, str):
        try:
            return yaml.safe_load(data)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
    return data
