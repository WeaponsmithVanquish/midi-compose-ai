"""WeightsService — fetch + verify model checkpoints.

Optional. The app works without a downloaded checkpoint (Markov fallback).
When `weights.lock` lists a URL + sha256, this service downloads to
`model_weights/` and refuses to load a file whose hash doesn't match.
"""

from __future__ import annotations

import hashlib
import logging
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from midi_compose_ai.utils.logging import get_logger

log = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class WeightEntry:
    name: str
    url: str
    sha256: str


class WeightHashMismatch(RuntimeError):
    """Raised when a downloaded checkpoint fails SHA-256 verification."""


class WeightsService:
    """Downloads and verifies checkpoint files listed in a lockfile."""

    def __init__(self, lockfile: Path, dest: Path = Path("model_weights")) -> None:
        self._lockfile = lockfile
        self._dest = dest

    def _entries(self) -> list[WeightEntry]:
        entries: list[WeightEntry] = []
        for line in self._lockfile.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name, url, sha = (p.strip() for p in line.split("|"))
            entries.append(WeightEntry(name=name, url=url, sha256=sha))
        return entries

    def ensure(self, name: str) -> Path:
        entry = next((e for e in self._entries() if e.name == name), None)
        if entry is None:
            raise KeyError(f"no lockfile entry for {name}")
        target = self._dest / name
        if target.is_file() and self._hash(target) == entry.sha256:
            return target
        log.info("downloading %s from %s", name, entry.url)
        self._dest.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(entry.url, target)
        actual = self._hash(target)
        if actual != entry.sha256:
            target.unlink(missing_ok=True)
            raise WeightHashMismatch(f"{name}: expected {entry.sha256}, got {actual}")
        return target

    @staticmethod
    def _hash(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()