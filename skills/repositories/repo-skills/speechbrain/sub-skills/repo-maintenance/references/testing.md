# Maintainer testing guide

SpeechBrain has several test layers. Choose the smallest layer that covers the change before running expensive suites.

## Focused commands

```bash
pytest tests/consistency
pytest tests/unittests
pytest --doctest-modules speechbrain
pytest tests/integration
```

For one module or behavior, run one file first:

```bash
pytest tests/unittests/test_core.py -q
pytest tests/unittests/test_audio_io.py -q
pytest tests/unittests/test_data_pipeline.py -q
pytest tests/unittests/test_checkpoints.py -q
```

## Broad shell wrappers

SpeechBrain includes wrappers for larger checks:

- `.run-linters.sh`
- `.run-doctests.sh`
- `.run-unittests.sh`
- `.run-load-yaml-tests.sh`
- `.run-recipe-tests.sh`
- `.run-HF-checks.sh`
- `.run-url-checks.sh`

These may be broad, slow, network-dependent, or GPU-dependent. Do not run them by default unless the task scope asks for repository-level verification.

## CI-style install pattern

The repository CI installs dependencies, a CPU Torch/Torchaudio pair, then the package editable without dependency reinstall. This pattern helps avoid unexpected backend changes:

```bash
pip install uv
uv pip install --system -r requirements.txt torch==2.6.0+cpu torchaudio==2.6.0+cpu --extra-index-url https://download.pytorch.org/whl/cpu
uv pip install --system --editable . --no-deps
```

Adapt this to an isolated environment instead of mutating a shared Python.

## Test selection by change type

| Change | Start with | Then consider |
| --- | --- | --- |
| `speechbrain.core`, `RunOptions`, `Brain` | `test_core.py`, doctests | integration recipes using `Brain` |
| Audio I/O | `test_audio_io.py` | augmentation/enhancement integration |
| Data pipeline/dataloader | `test_data_pipeline.py`, `test_dataset.py`, `test_dataloader.py` | recipe debug row |
| Inference interface | import/doctest check | one safe pretrained/local smoke if model artifact available |
| Decoder/metrics | `test_metrics.py`, `test_edit_distance.py`, decoder tests | ASR integration example |
| Recipe file | recipe-specific debug command | `tests/consistency/test_recipe.py` |
| Documentation | doctest/docs build | URL checks if links changed |

## PR review hints

For interface changes, ask whether all HyperPyYAML references still instantiate. For recipe changes, ask whether the debug flags and expected files still match. For legacy-breaking changes, require tests and docs that cover the old/new boundary intentionally.
