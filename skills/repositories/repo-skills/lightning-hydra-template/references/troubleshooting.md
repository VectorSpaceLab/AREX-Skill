# Cross-cutting Troubleshooting

## Install or import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'lightning'` or `hydra` | Requirements were not installed in the active environment. | Install `requirements.txt`, then run `python -c "import lightning, hydra"`. |
| `ModuleNotFoundError: No module named 'src'` | Project was not installed/editable, current directory is not on `PYTHONPATH`, or the project renamed the default package. | Run `pip install -e .`; if renamed, update imports, console scripts, and `_target_` strings to the new package. |
| Console script missing: `train_command: command not found` | Editable package was not installed or `setup.py` entry points changed. | Run `pip install -e .`; inspect console scripts with `python -c "from importlib.metadata import entry_points; print([e for e in entry_points(group='console_scripts') if 'command' in e.name])"`. |
| `rootutils` cannot find `.project-root` or `PROJECT_ROOT` is missing | Entry file moved, marker removed, or root setup was changed. | Keep `.project-root` at the project root or update `rootutils.setup_root(..., indicator=...)` and `configs/paths/default.yaml`. |

## Hydra config failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `MissingConfigException` for a config group | Wrong group option, moved YAML, or defaults list not updated. | Use `python <this-skill>/sub-skills/configure-experiments/scripts/render_config_summary.py --repo-root . --config-name train.yaml --list-groups` and then fix the defaults entry or CLI override. |
| `Error locating target 'src....'` | `_target_` points to a stale import path, often after package rename. | Run `python <this-skill>/sub-skills/customize-data-model/scripts/check_hydra_targets.py --repo-root .`; update the YAML `_target_` strings. |
| Interpolation error for `${paths.root_dir}` | `PROJECT_ROOT` was not set because rootutils did not run or a test composed configs directly. | In scripts/tests, set `cfg.paths.root_dir` after compose or initialize from an entry point that calls rootutils. |
| Tag prompt blocks automation | `extras.enforce_tags=True` and tags are empty. | For smoke tests or CI, set `extras.enforce_tags=false` or provide `tags=[...]`. |

## Training, data, and checkpoint failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Training tries to download MNIST during a smoke test | `MNISTDataModule.prepare_data()` downloads data by design. | Use config composition tests for no-network smoke; otherwise pre-populate data or allow network explicitly. |
| `Batch size (...) is not divisible by the number of devices` | `MNISTDataModule.setup()` divides `batch_size` by `trainer.world_size`. | Set `data.batch_size` divisible by `trainer.devices * trainer.num_nodes`. |
| `Metric value not found` for `optimized_metric` | `optimized_metric` does not match a logged metric key. | For the default module use `val/acc_best` for hparam search; ensure custom modules log the chosen metric. |
| Eval fails immediately with missing checkpoint | `configs/eval.yaml` has `ckpt_path: ???`, and `evaluate()` asserts it. | Pass `ckpt_path=/path/to/last.ckpt` or a matching checkpoint URL/path. |
| `ModelCheckpoint` cannot find monitor metric | Callback monitor does not match model logs. | Default callback monitors `val/acc`; update callback config if the model logs different metrics. |

## Optional dependencies, services, and backends

- W&B, Neptune, Comet, MLflow, and Aim configs require their packages and often credentials or running services. For smoke tests use `logger=null` or `logger=csv`.
- GPU/MPS/TPU trainer configs only prove syntax until run on matching hardware with a compatible PyTorch build. Use CPU config/API checks as portable verification, and treat hardware runs as optional unless the user explicitly requires them.
- DDP is documented as potentially problematic in this template. For local process-mechanics smoke, prefer `trainer=ddp_sim` and small batch limits; for real multi-GPU runs, verify data/cache, batch divisibility, and logger behavior first.

## Test and CI surprises

- `make test` runs `pytest -k "not slow"`; this is not guaranteed no-network because `test_train_fast_dev_run` is not marked slow and can download MNIST.
- `tests/test_sweeps.py` uses the optional `sh` package and is skipped when `sh` is absent or on Windows.
- If a new test composes Hydra configs, clear `GlobalHydra` between tests or follow the fixture pattern in the template.
- `pyproject.toml` registers only the `slow` marker. Add any new custom marker to the marker list to avoid strict-marker failures.
