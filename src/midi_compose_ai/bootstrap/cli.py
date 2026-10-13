"""Click-based CLI entry point.

Thin: parse args, resolve profile, hand to handlers. No business logic.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console

from midi_compose_ai.bootstrap.container import Container
from midi_compose_ai.handlers.generate import GenerateHandler
from midi_compose_ai.handlers.import_midi import ImportMidiHandler
from midi_compose_ai.handlers.render import RenderHandler

console = Console()


@click.group()
@click.version_option(package_name="midi-compose-ai")
def main() -> None:
    """midi-compose-ai — AI MIDI composition generator."""


@main.command()
@click.option("--prompt", "-p", default=None, help="Text prompt conditioning.")
@click.option("--profile", type=click.Path(path_type=Path), default=None)
@click.option("--bars", type=int, default=None)
@click.option("--seed", type=int, default=None)
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=None)
def generate(prompt: str | None, profile: Path | None, bars: int | None, seed: int | None, out_path: Path | None) -> None:
    """Generate a multi-track MIDI file."""
    container = Container()
    handler = GenerateHandler(container)
    result = handler.handle(prompt=prompt, profile=profile, bars=bars, seed=seed, out_path=out_path)
    console.print(f"[green]wrote[/green] {result.midi_path} ({result.tokens} tokens, {result.bars} bars)")


@main.command(name="import-midi")
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=None)
def import_midi(source: Path, out_path: Path | None) -> None:
    """Import an existing MIDI file as a reference sketch."""
    handler = ImportMidiHandler(Container())
    result = handler.handle(source=source, out_path=out_path)
    console.print(f"[green]imported[/green] {source.name} -> {result.sketch_path}")


@main.command()
@click.argument("midi_path", type=click.Path(exists=True, path_type=Path))
@click.option("--play/--no-play", default=True)
def render(midi_path: Path, play: bool) -> None:
    """Render MIDI to audio and optionally play it."""
    handler = RenderHandler(Container())
    result = handler.handle(midi_path=midi_path, play=play)
    console.print(f"[green]rendered[/green] {result.audio_path}")


if __name__ == "__main__":
    sys.exit(main())