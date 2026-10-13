"""YAML config loader with pydantic validation.

Loads `config/*.yaml`, merges overrides, caches parsed profiles by mtime.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from midi_compose_ai.models.config import CompositionProfile


class ConfigError(RuntimeError):
    """Raised when a profile is missing, malformed, or fails validation."""


class ConfigLoader:
    """Reads YAML profiles from a config root.

    Caches by (path, mtime_ns) so hot-reloading an edited profile works
    without restarting the desktop shell.
    """

    def __init__(self, root: Path) -> None:
        self._root = root
        self._cache: dict[tuple[Path, int], CompositionProfile] = {}

    def load(self, name_or_path: str | Path) -> CompositionProfile:
        path = self._resolve(name_or_path)
        key = (path, path.stat().st_mtime_ns)
        if key in self._cache:
            return self._cache[key]
        try:
            raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise ConfigError(f"{path.name}: invalid YAML: {exc}") from exc
        try:
            profile = CompositionProfile.model_validate(raw)
        except ValidationError as exc:
            raise ConfigError(f"{path.name}: {exc}") from exc
        self._cache[key] = profile
        return profile

    def default(self) -> CompositionProfile:
        return self.load("default.yaml")

    def _resolve(self, name_or_path: str | Path) -> Path:
        candidate = Path(name_or_path)
        if candidate.is_file():
            return candidate
        stem = candidate.name if candidate.suffix else f"{candidate.name}.yaml"
        rooted = self._root / stem
        if not rooted.is_file():
            raise ConfigError(f"profile not found: {name_or_path}")
        return rooted