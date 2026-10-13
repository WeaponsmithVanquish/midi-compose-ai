"""REMI-style MIDI tokenizer.

Vocabulary is trained offline (`tools/train_tokenizer.py`) and cached as
JSON. This module only loads and applies it — no training here.

Token families:
    P_<key>          — pitch, 0..127
    V_<0..31>        — velocity bucket
    D_<ticks>        — duration in 10ms ticks
    T_<ticks>        — time delta from previous event
    B_<bar>          — bar marker
    C_<chord>        — chord symbol (roman + quality)
    S_<track>        — track separator / track id
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class TokenizerSpec:
    vocab_size: int
    pad_id: int
    bos_id: int
    eos_id: int


class RemiTokenizer:
    """Loads a REMI vocab from JSON and maps tokens <-> ids.

    Unknown tokens map to `<unk>` (id 1). This is lossy on purpose —
    the composer tolerates a few unknown tokens per bar.
    """

    def __init__(self, token_to_id: dict[str, int], spec: TokenizerSpec) -> None:
        self._t2i = token_to_id
        self._i2t = {v: k for k, v in token_to_id.items()}
        self.spec = spec

    @classmethod
    def from_cache(cls, path: Path) -> "RemiTokenizer":
        if not path.is_file():
            raise FileNotFoundError(
                f"tokenizer cache missing at {path}. Run tools/train_tokenizer.py first."
            )
        payload = json.loads(path.read_text(encoding="utf-8"))
        spec = TokenizerSpec(
            vocab_size=payload["vocab_size"],
            pad_id=payload["special"]["pad"],
            bos_id=payload["special"]["bos"],
            eos_id=payload["special"]["eos"],
        )
        return cls(token_to_id=payload["token_to_id"], spec=spec)

    def encode(self, tokens: list[str]) -> list[int]:
        return [self._t2i.get(t, 1) for t in tokens]

    def decode(self, ids: list[int]) -> list[str]:
        return [self._i2t.get(i, "<unk>") for i in ids]

    def __len__(self) -> int:
        return self.spec.vocab_size