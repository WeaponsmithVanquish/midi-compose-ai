# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.6.x   | yes       |
| 0.5.x   | yes       |
| < 0.5   | no        |

## Scope

midi-compose-ai runs locally. It does not phone home. The only network
surface is the optional model-weight download in
`services/weights_service.py`, which fetches from explicit HTTPS URLs and
verifies SHA-256 against `config/weights.lock`.

## Reporting a vulnerability

Email `security@midi-compose-ai.dev` or open a private security advisory
on GitHub. Do not file public issues for:

- Arbitrary file write via crafted MIDI import (`adapters/midi_io.py`)
- Path traversal in `--output` / `--config` flags
- Model deserialization issues in the safetensors loader
- Command injection in the FluidSynth adapter's subprocess call

We aim to respond within 72 hours. Credit given in release notes unless
you ask otherwise.

## Out of scope

- Generated music being "bad" is not a security issue.
- Prompt injection in the text-to-MIDI frontend is a model-quality issue,
  not a memory-safety issue. Still, report it.