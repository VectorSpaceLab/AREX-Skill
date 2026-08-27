# Runtime entry points

These helpers are bundled inside the generated skill so users can bootstrap and smoke-test Asteroid without depending on the original repository checkout.

## `scripts/install_runtime.py`

Use this helper to install the public runtime package plus the extra runtime dependencies that the inspection found to be necessary for the main public workflows. By default it installs the self-contained `scripts/runtime_requirements.txt` file bundled with this skill.

Typical usage:

```bash
python scripts/install_runtime.py
python scripts/install_runtime.py --with-tests
python scripts/install_runtime.py --extra-index-url https://download.pytorch.org/whl/cu128
```

What it does:

- installs `scripts/runtime_requirements.txt`
- installs `asteroid` from the public package index
- installs `requests` so pretrained-model and hub helpers work
- installs `librosa` so the full `asteroid.data` import surface works
- optionally installs `pytest` or extra `--package` specifiers
- verifies the resulting environment with `pip check` and a tiny import smoke

## `scripts/smoke_training.py`

Use this helper for a self-contained training sanity check that does not require the source repo's recipe tree. The focused sub-skill variant at `sub-skills/training-recipes/scripts/smoke_system_training.py` accepts the same `--device auto|cpu|cuda` flag.

Typical usage:

```bash
python scripts/smoke_training.py
python scripts/smoke_training.py --device cpu
python scripts/smoke_training.py --device cuda
```

What it does:

- builds a tiny synthetic waveform dataset
- creates a tiny model and PIT loss
- wraps them in `asteroid.engine.system.System`
- runs a one-step Lightning `fast_dev_run` fit

## `scripts/inspect_versions.py`

Use this helper to print the installed Asteroid, PyTorch, PyTorch-Lightning, and optional dependency versions before routing to a sub-skill.

Typical usage:

```bash
python scripts/inspect_versions.py
```

## Why these entry points matter

They give the generated skill a self-contained way to:

- bootstrap runtime dependencies
- validate the install
- smoke-test training flow
- inspect the active backend before choosing a workflow
