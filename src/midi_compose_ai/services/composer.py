"""ComposeService — turns a profile + prompt into a token sequence.

This is the core entry for generation. It does NOT touch the filesystem
beyond reading the model checkpoint; writing is the renderer's job.

Backend note: when `torch` is installed the sampler runs on the real
model. When it isn't, we fall back to a deterministic Markov sampler
that ships with the repo so the CLI still works for demos.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass

from midi_compose_ai.models.config import CompositionProfile
from midi_compose_ai.models.tokenizer import RemiTokenizer
from midi_compose_ai.utils.logging import get_logger

log = get_logger(__name__)


@dataclass(slots=True)
class Composition:
    token_ids: list[int]
    tokens: list[str]
    seed: int
    bars: int
    prompt: str | None


class ComposeService:
    """Generates a raw token sequence from a conditioning context.

    Sampling: temperature / top_p / top_k from the profile. Seed is
    per-composition; passing the same seed + profile + prompt reproduces
    the exact token stream (byte-stable) as long as the checkpoint and
    tokenizer cache are unchanged.
    """

    def __init__(self, tokenizer: RemiTokenizer, config: CompositionProfile) -> None:
        self._tok = tokenizer
        self._cfg = config
        self._rng = random.Random()
        self._model = self._load_backend()

    def _load_backend(self):
        try:
            import torch  # noqa: F401
        except ImportError:
            log.warning("torch not installed — using Markov fallback sampler")
            return None
        from midi_compose_ai.models.neural import NeuralBackend

        return NeuralBackend(self._cfg.model.checkpoint, self._tok.spec)

    def compose(self, prompt: str | None = None, bars: int | None = None, seed: int | None = None) -> Composition:
        seed = self._cfg.seed if seed is None else seed
        bars = self._cfg.generation.bars if bars is None else bars
        self._rng.seed(seed)
        prompt = prompt or self._cfg.conditioning.prompt

        # Seed context: BOS + prompt tokens + first bar marker.
        ctx = ["<bos>", "B_0"]
        if prompt:
            ctx.extend(self._prompt_tokens(prompt))

        if self._model is None:
            ids = self._markov_sample(ctx, bars)
        else:
            ids = self._model.sample(
                ctx_ids=self._tok.encode(ctx),
                max_tokens=min(self._cfg.model.max_tokens, bars * 96),
                temperature=self._cfg.model.temperature,
                top_p=self._cfg.model.top_p,
                top_k=self._cfg.model.top_k,
                rng=self._rng,
            )
        tokens = self._tok.decode(ids)
        return Composition(token_ids=ids, tokens=tokens, seed=seed, bars=bars, prompt=prompt)

    def _prompt_tokens(self, prompt: str) -> list[str]:
        # Cheap keyword -> chord-family hint. The real model does this in
        # its conditioning encoder; here it's a fallback so Markov mode
        # isn't totally blind to the prompt.
        lowered = prompt.lower()
        hints: list[str] = []
        if any(w in lowered for w in ("rain", "nocturne", "sad", "minor")):
            hints.append("C_min")
        if any(w in lowered for w in ("bright", "major", "sun")):
            hints.append("C_maj")
        return hints

    def _markov_sample(self, ctx: list[str], bars: int) -> list[int]:
        # Placeholder transition table. Real one lives in model_weights/.
        vocab = list(self._tok._t2i.keys())  # noqa: SLF001 — internal by design
        ids = self._tok.encode(ctx)
        target = bars * 96
        while len(ids) < target:
            nxt = self._rng.choice(vocab)
            ids.append(self._tok._t2i.get(nxt, 1))
        return ids