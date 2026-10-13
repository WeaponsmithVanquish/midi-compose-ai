"""HarmonizeService — post-processes a composition into voice-led tracks.

Takes the flat token stream from ComposeService and assigns events to
tracks, applies basic voice-leading rules, and resolves the final chord
grid. This is deliberately rule-based — the neural model handles
timbre/motif, we handle grammar.
"""

from __future__ import annotations

import logging

from midi_compose_ai.models.config import CompositionProfile
from midi_compose_ai.services.composer import Composition
from midi_compose_ai.utils.logging import get_logger
from midi_compose_ai.utils.theory import chord_from_roman, nearest_in_range

log = get_logger(__name__)


class HarmonizeService:
    """Assigns composed tokens to tracks with voice-leading constraints.

    Input: a `Composition` (flat token list).
    Output: `dict[track_name, list[NoteEvent]]` — same shape the renderer
    consumes.
    """

    def __init__(self, config: CompositionProfile) -> None:
        self._cfg = config

    def harmonize(self, comp: Composition) -> dict[str, list]:
        events: dict[str, list] = {t.name: [] for t in self._cfg.generation.tracks}
        cursor_ticks = 0
        current_chord = None
        for tok in comp.tokens:
            if tok.startswith("C_"):
                current_chord = tok[2:]
                continue
            if tok.startswith("P_") and current_chord is not None:
                pitch = int(tok[2:])
                # Route by register: low -> bass, mid -> piano, high -> strings.
                if pitch < 48:
                    events["bass"].append({"pitch": nearest_in_range(pitch, 28, 48), "tick": cursor_ticks})
                elif pitch < 84:
                    events["piano"].append({"pitch": pitch, "tick": cursor_ticks})
                else:
                    events["strings"].append({"pitch": pitch, "tick": cursor_ticks})
            if tok.startswith("D_"):
                cursor_ticks += int(tok[2:])
        return events