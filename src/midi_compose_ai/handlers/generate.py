"""GenerateHandler — CLI/desktop request -> ComposeService -> RenderService."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from midi_compose_ai.bootstrap.container import Container


@dataclass(slots=True)
class GenerateResult:
    midi_path: Path
    tokens: int
    bars: int


class GenerateHandler:
    """Bridges a generate request to the compose + harmonize + render chain.

    No business logic. Overrides from the request are merged into a copy
    of the profile before services see it.
    """

    def __init__(self, container: Container) -> None:
        self._c = container

    def handle(
        self,
        prompt: str | None,
        profile: Path | None,
        bars: int | None,
        seed: int | None,
        out_path: Path | None,
    ) -> GenerateResult:
        cfg = self._c.config_loader().load(profile) if profile else self._c.config_loader().default()
        comp = self._c.composer().compose(prompt=prompt, bars=bars, seed=seed)
        events = self._c.harmonizer().harmonize(comp)
        name = out_path.stem if out_path else f"compose_{comp.seed}"
        result = self._c.renderer().render(
            events=events,
            tempo_bpm=cfg.generation.tempo_bpm,
            out_name=name,
        )
        return GenerateResult(midi_path=result.midi_path, tokens=len(comp.token_ids), bars=comp.bars)