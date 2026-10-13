"""RenderService — writes MIDI, renders audio, optionally plays.

Two sinks: `MidiFileSink` always runs (produces the .mid). Audio backend
runs only if `--render-audio` is passed or the desktop shell requests it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from midi_compose_ai.adapters.base import MidiSink, RenderBackend, MidiPlayer
from midi_compose_ai.utils.logging import get_logger

log = get_logger(__name__)


@dataclass(slots=True)
class RenderResult:
    midi_path: Path
    audio_path: Path | None
    played: bool


class RenderService:
    """Orchestrates sink/backend/player.

    Order: write .mid -> (optional) render audio -> (optional) play.
    Failures are non-fatal except for the .mid write, which is the
    contract.
    """

    def __init__(self, sink: MidiSink, backend: RenderBackend, player: MidiPlayer) -> None:
        self._sink = sink
        self._backend = backend
        self._player = player

    def render(
        self,
        events: dict[str, list],
        tempo_bpm: int,
        out_name: str,
        render_audio: bool = False,
        play: bool = False,
    ) -> RenderResult:
        midi_path = self._sink.write(events, tempo_bpm=tempo_bpm, name=out_name)
        log.info("wrote %s", midi_path)
        audio_path: Path | None = None
        if render_audio:
            try:
                audio_path = self._backend.render(midi_path)
            except Exception as exc:  # noqa: BLE001 — backend is best-effort
                log.warning("audio render failed: %s", exc)
        played = False
        if play:
            try:
                self._player.play(midi_path)
                played = True
            except Exception as exc:  # noqa: BLE001
                log.warning("playback failed: %s", exc)
        return RenderResult(midi_path=midi_path, audio_path=audio_path, played=played)