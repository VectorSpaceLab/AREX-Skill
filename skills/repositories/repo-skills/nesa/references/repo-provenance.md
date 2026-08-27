# Repository Provenance

Generated for the public Nesa repository skill.

## Source snapshot

- VCS: git
- Remote URL: `https://github.com/nesaorg/nesa.git`
- Branch: `main`
- Commit: `c48412c660a700ae54ff63c1e10db063d2b87889`
- Exact tag: none detected
- Package/distribution version: not declared as an installable Python distribution
- Runtime version hint from Nesa settings: `0.0.1`
- Working tree state at generation: dirty because untracked construction output/log directories were present.
  - Dirty paths: `logs/`, `skills/`

The commit plus dirty-state summary is the refresh baseline. If a future Nesa
checkout changes code, docs, model names, requirements, settings, or backend
protocol structs, refresh this skill before relying on exact signatures or
startup guidance.

## Evidence paths used

Core docs and public context:

- `README.md`
- `CONTEST.md`
- `Attack_Paper.pdf`
- `docs/ee.png`
- `docs/tokenizer.png`

Minimal local demo:

- `demo-basic/README.md`
- `demo-basic/demo.py`
- `demo-basic/distilbert-sentiment-encrypted/README.md`
- `demo-basic/distilbert-sentiment-encrypted/config.json`
- tokenizer metadata under `demo-basic/distilbert-sentiment-encrypted/`

Web UI and runtime:

- `demo/readme.md`
- `demo/server.py`
- `demo/one_click.py`
- `demo/start_linux.sh`
- `demo/start_macos.sh`
- `demo/start_windows.bat`
- `demo/CMD_FLAGS.txt`
- `demo/settings-template.yaml`
- `demo/requirements/requirements*.txt`
- `demo/nesa/run.sh`
- `demo/nesa/env_setup.py`
- `demo/nesa/download.py`
- selected Nesa integration points under `demo/modules/`

Backend protocol and model handlers:

- `demo/nesa/settings.py`
- `demo/nesa/backend/protocol.py`
- `demo/nesa/backend/registry.py`
- `demo/nesa/backend/utils.py`
- `demo/nesa/backend/llms.py`
- `demo/nesa/backend/hf_models.py`

## Verification baseline

A private CPU inspection environment imported the Nesa source modules from the
`demo/` package root and verified selected third-party dependencies. It did not
run model downloads, a full web UI launch, remote Nesa stream calls, or final
native examples during skill creation.

Public generated skill files intentionally do not include local environment
paths, activation commands, source checkout paths, downloaded model weights, or
private setup logs.
