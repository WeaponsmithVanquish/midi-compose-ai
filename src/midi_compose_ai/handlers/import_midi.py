"""ImportMidiHandler — load a reference MIDI into an internal sketch."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from midi_compose_ai.adapters.midi_io import MidiFileReader
from midi_compose_ai.bootstrap.container import Container


@dataclass(slots=True)
class ImportResult:
    sketch_path: Path
    note_count: int


class ImportMidiHandler:
    """Reads a .mid, tokenizes it, dumps the token stream as a sketch JSON.

    Sketches are consumed by the composer as a chord/motif conditioning
    source when `conditioning.reference_midi` points at them.
    """

    def __init__(self, container: Container) -> None:
        self._c = container
        self._reader = MidiFileReader()

    def handle(self, source: Path, out_path: Path | None) -> ImportResult:
        notes = self._reader.read(source)
        tokens = self._notes_to_tokens(notes)
        dest = out_path or Path("output") / f"{source.stem}.sketch.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(
            json.dumps({"source": str(source), "tokens": tokens}, indent=2),
            encoding="utf-8",
        )
        return ImportResult(sketch_path=dest, note_count=len(notes))

    @staticmethod