from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


class RegistryReadError(Exception):
    pass


class RegistryLoader:
    """Read-only adapter for AVOT registry YAML."""

    def __init__(self, registry_path: str):
        self.registry_path = Path(registry_path)
        if not self.registry_path.exists():
            raise RegistryReadError(f"Registry file not found at {self.registry_path}")

    def load_registry(self) -> Dict[str, Any]:
        try:
            with self.registry_path.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise RegistryReadError(f"Failed to read registry: {e}")

    def get_avot_entry(self, avot_id: str) -> Dict[str, Any]:
        registry = self.load_registry()
        avots = registry.get("avot_registry", {}).get("avots", {})
        entry = avots.get(avot_id, {}) or {}
        return dict(entry)

    def registry_metadata(self) -> Dict[str, Any]:
        registry = self.load_registry()
        meta = dict(registry.get("avot_registry", {}) or {})
        meta.pop("avots", None)
        return meta
