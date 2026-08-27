# Testing and CI Reference

## Test classifications

| Test/cmd | Safety | What it validates | Notes |
| --- | --- | --- | --- |
| `pytest tests/test_configs.py -q` | Required offline-safe smoke | Hydra config fixtures compose and instantiate data/model/trainer. | No MNIST download or training. |
| `pytest tests/test_train.py::test_train_fast_dev_run -q` | Optional network/cache | One train/val/test fast-dev run on CPU. | Not marked slow; can download MNIST. |
| `pytest tests/test_datamodules.py -q` | Optional network/cache | MNIST prepare/setup/dataloaders/dtypes. | Downloads MNIST unless cached. |
| `pytest tests/test_eval.py::test_train_eval -q` | Optional slow/network | Train one epoch, checkpoint, evaluate last checkpoint. | Requires data/cache and more time. |
| `pytest tests/test_train.py::test_train_fast_dev_run_gpu -q` | Optional GPU/network | Fast-dev run on GPU. | Guarded by `RunIf(min_gpus=1)`. |
| `pytest tests/test_train.py::test_train_epoch_gpu_amp -q` | Optional GPU/slow | One epoch GPU mixed precision. | Marked slow and GPU-gated. |
| `pytest tests/test_sweeps.py -q` | Optional shell/network/slow | Hydra multirun and Optuna sweeps. | Requires `sh` on non-Windows; may download data. |

## Fixtures

`tests/conftest.py` composes train/eval configs and then adjusts them for safer tests:

- `paths.root_dir` points to the project root.
- `trainer.max_epochs=1`.
- batch limits reduce train/val/test workload.
- `trainer.accelerator=cpu`, `devices=1`.
- `data.num_workers=0`, `pin_memory=False`.
- `extras.print_config=False`, `extras.enforce_tags=False`.
- `logger=None`.
- function-scoped fixtures set temporary output/log directories and clear `GlobalHydra` after use.

Follow this pattern when adding tests that compose configs.

## Makefile targets

- `make train`: `python src/train.py`.
- `make test`: `pytest -k "not slow"`.
- `make test-full`: `pytest`.
- `make format`: `pre-commit run -a`.
- `make clean` and `make clean-logs`: remove generated artifacts.

`make test` is quick but not guaranteed offline-safe because one non-slow train test may download data.

## CI evidence

The test workflow installs `requirements.txt`, `pytest`, and `sh` on Ubuntu/macOS, but omits `sh` on Windows. It runs `pytest -v` across Python 3.8, 3.9, and 3.10. Coverage uses `pytest --cov src` and must be updated if the import package is renamed.

Code-quality workflows run pre-commit on main and pull requests. Keep `.pre-commit-config.yaml` aligned with code style expectations when changing files.

## Recommended command profiles

```bash
# Offline/config-only
pytest tests/test_configs.py -q

# Quick but may download MNIST
pytest -k "not slow" -q

# Full local suite with data/cache/network accepted
pytest -q

# GPU-specific subset
pytest tests/test_train.py::test_train_fast_dev_run_gpu -q

# Sweep subset when sh is installed and data/cache is ready
pytest tests/test_sweeps.py -q
```
