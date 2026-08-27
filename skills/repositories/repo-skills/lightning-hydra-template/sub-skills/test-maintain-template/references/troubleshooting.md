# Testing and Maintenance Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `pytest -k "not slow"` downloads MNIST | `test_train_fast_dev_run` is not marked slow. | For offline CI, run `pytest tests/test_configs.py -q` or mock/pre-cache data before training tests. |
| `GlobalHydra is already initialized` | A test composed Hydra configs without clearing global state. | Use the template fixture pattern and call `GlobalHydra.instance().clear()` after function-scoped config tests. |
| `Unknown pytest.mark.<name>` under strict markers | `pyproject.toml` registers only `slow`. | Add the marker to `tool.pytest.ini_options.markers` or avoid custom markers. |
| Sweep tests skipped | `sh` missing, Windows platform, or optional logger package unavailable. | Install `sh` on Linux/macOS if needed; keep Windows skips; use profile selection script. |
| GPU tests skipped | `torch.cuda.device_count() < min_gpus`. | Treat as optional unless the user requires GPU verification; run on GPU hardware with compatible torch. |
| Logger tests fail with credentials | Online logger config enabled without package/token/account. | Use `logger=null`/`logger=csv` in CI; test online loggers in a credentialed environment only. |
| Coverage path is empty after package rename | CI still runs `pytest --cov src`. | Update coverage target to the new import package. |
| Console scripts still import old package | Editable install metadata is stale or `setup.py` entry points not updated. | Update `setup.py`, reinstall with `pip install -e .`, and inspect entry points. |
| Pre-commit changes many generated outputs | Runtime logs, notebooks, caches, or generated files included by mistake. | Clean generated artifacts; keep `.gitignore` and pre-commit hooks aligned. |

## Maintenance stop conditions

Ask for user intent before deleting logs/data, rewriting package names across a derived project, installing optional online logger packages, or changing CI to require hardware/service credentials.
