"""Dependency container.

Wires services + adapters once at process start. Handlers receive the
container, not raw services, so tests can swap implementations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from midi_compose_ai.adapters.midi_io import MidiFileSink
from midi_compose_ai.adapters.fluidsynth import FluidSynthRenderer
from midi_compose_ai.adapters.winmm import WinMMPlayer
from midi_compose_ai.config.loader import ConfigLoader
from midi_compose_ai.models.tokenizer import RemiTokenizer
from midi_compose_ai.services.composer import ComposeService
from midi_compose_ai.services.harmonizer import HarmonizeService
from midi_compose_ai.services.renderer import RenderService
from midi_compose_ai.services.weights_service import WeightsService


@dataclass(slots=True)
class Container:
    """Lazy-initialized service graph.

    Services are constructed on first access; adapters are constructed
    eagerly because they're cheap and hold OS handles.
    """

    config_root: Path = field(default_factory=lambda: Path("config"))
    output_root: Path = field(default_factory=lambda: Path("output"))

    _config_loader: ConfigLoader | None = None
    _tokenizer: RemiTokenizer | None = None
    _composer: ComposeService | None = None
    _harmonizer: HarmonizeService | None = None
    _renderer: RenderService | None = None
    _weights: WeightsService | None = None

    def config_loader(self) -> ConfigLoader:
        if self._config_loader is None:
            self._config_loader = ConfigLoader(self.config_root)
        return self._config_loader

    def tokenizer(self) -> RemiTokenizer:
        if self._tokenizer is None:
            self._tokenizer = RemiTokenizer.from_cache(
                self.config_loader().default().model.tokenizer
            )
        return self._tokenizer

    def composer(self) -> ComposeService:
        if self._composer is None:
            self._composer = ComposeService(
                tokenizer=self.tokenizer(),
                config=self.config_loader().default(),
            )
        return self._composer

    def harmonizer(self) -> HarmonizeService:
        if self._harmonizer is None:
            self._harmonizer = HarmonizeService(self.config_loader().default())
        return self._harmonizer

    def renderer(self) -> RenderService:
        if self._renderer is None:
            self._renderer = RenderService(
                sink=MidiFileSink(self.output_root),
                backend=FluidSynthRenderer(self.config_loader().default().render),
                player=WinMMPlayer(),
            )
        return self._renderer

    def weights(self) -> WeightsService:
        if self._weights is None:
            self._weights = WeightsService(lockfile=Path("config/weights.lock"))
        return self._weights