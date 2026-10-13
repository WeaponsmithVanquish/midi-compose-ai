# Contributing to midi-compose-ai

Thanks for wanting to push on the generator. This repo is a desktop-first
Python app that turns text prompts / chord sketches / reference MIDI into
composed multi-track MIDI. Everything is service-oriented: thin handlers,
business services, data models, platform adapters.

## Dev setup

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -e ".[dev]"
pre-commit install
```

## Repo layout

- `src/midi_compose_ai/` — the package
  - `bootstrap/` — entry points, CLI, TUI shell, dependency container
  - `handlers/` — thin request handlers (parse, route, dispatch)
  - `services/` — the actual business logic (compose, harmonize, render)
  - `models/` — dataclasses, tokenizer, encoder/decoder
  - `adapters/` — platform adapters (WinMM, ASIO, FluidSynth, file I/O)
  - `utils/` — music theory helpers, logging, timing
- `tests/` — pytest suites
- `config/` — YAML profiles shipped with the app
- `tools/` — small dev utilities (dataset prep, MIDI scraping)

## Contribution rules

1. One service = one responsibility. If your PR makes `composer.py`
   import `renderer.py`, split it.
2. Handlers never contain business logic. They parse, validate, dispatch.
3. New adapters must implement the `MidiSink` protocol in
   `adapters/base.py`.
4. Every public function gets a docstring with type hints. No exceptions.
5. Tests: `pytest -q` must pass. New services need at least one test.
6. Commit style: `scope: short imperative`. e.g. `composer: add motif recurrence`.

## Reporting bugs

Open an issue with: prompt, seed, config profile, and the generated `.mid`
if it's small. Reproduce with `midi-compose generate --seed <n>`.