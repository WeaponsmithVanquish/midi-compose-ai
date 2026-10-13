"""Pydantic schema for composition profiles.

Mirrors config/default.yaml. Any field added here must also land in the
default profile or `ConfigLoader.default()` will fail validation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ModelSection(BaseModel):
    checkpoint: Path
    tokenizer: Path
    max_tokens: int = Field(ge=256, le=16384)
    temperature: float = Field(ge=0.0, le=2.0)
    top_p: float = Field(gt=0.0, le=1.0)
    top_k: int = Field(ge=0)


class TrackSpec(BaseModel):
    name: str
    program: int = Field(ge=0, le=127)
    channel: int = Field(ge=0, le=15)


class GenerationSection(BaseModel):
    bars: int = Field(ge=1, le=512)
    time_signature: tuple[int, int] = (4, 4)
    key: str
    mode: Literal["major", "minor", "dorian", "mixolydian", "lydian", "phrygian"]
    tempo_bpm: int = Field(ge=20, le=300)
    tracks: list[TrackSpec] = Field(min_length=1)

    @field_validator("time_signature")
    @classmethod
    def _ts_must_divide(cls, v: tuple[int, int]) -> tuple[int, int]:
        if v[0] <= 0 or v[1] <= 0:
            raise ValueError("time signature components must be positive")
        return v


class ConditioningSection(BaseModel):
    prompt: str | None = None
    chord_sketch: Path | None = None
    reference_midi: Path | None = None
    motif_recurrence: float = Field(default=0.3, ge=0.0, le=1.0)


class RenderSection(BaseModel):
    backend: Literal["fluidsynth", "null", "winmm"]
    soundfont: Path | None = None
    sample_rate: int = Field(default=44100, ge=8000, le=192000)


class CompositionProfile(BaseModel):
    profile: str
    seed: int
    model: ModelSection
    generation: GenerationSection
    conditioning: ConditioningSection
    render: RenderSection