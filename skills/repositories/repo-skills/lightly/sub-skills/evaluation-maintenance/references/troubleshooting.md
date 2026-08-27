# Troubleshooting evaluation and maintenance

Use this table to diagnose common LightlySSL evaluation and repository-maintenance failures. Keep fixes scoped and route to sibling sub-skills when the root cause belongs to training, CLI/data, or low-level SSL components.

## Evaluation utilities

| Symptom | Likely cause | Fix |
|---|---|---|
| `knn_predict` raises a top-k or shape error | `knn_k` is larger than the feature-bank size, feature dimensions do not align, or feature labels do not match bank columns. | Check `features.shape == (B, D)`, `feature_bank.shape == (D, N)`, `feature_labels.shape == (N,)`, and `knn_k <= N`. Normalize features if cosine-style matching is intended. |
| KNN top-1 accuracy is unexpectedly poor | Features are unnormalized, labels are not integer class ids, train/validation dataloaders are reversed, or the wrong dataloader index is used. | Normalize features, verify label range, pass `[train_loader, val_loader]`, and set `train_dataloader_idx=0`, `val_dataloader_idx=1`. |
| `KNNClassifier` metrics are missing | The validation dataloader ran before the feature-bank dataloader or multiple-dataloader metric suffixes were not considered. | Use two validation dataloaders in the intended order; inspect names such as `val_knn_top1/dataloader_idx_1`. |
| `LinearClassifier` fails in the classification head | `feature_dim` does not match `model(images).flatten(start_dim=1)`. | Run one no-grad batch through the feature model, inspect the flattened dimension, and pass it as `feature_dim`. |
| Linear evaluation changes backbone weights or batch norm stats | Finetune behavior was selected or the model was updated outside `LinearClassifier`. | Use `LinearClassifier` for frozen representation evaluation. Use `FinetuneClassifier` only when updating the backbone is intended. |
| Online classifier loss does not update the encoder | `OnlineLinearClassifier` detaches features internally. | Treat it as a monitoring head. If supervised gradients must update the encoder, add a separate supervised loss path. |
| `MetricCallback` misses a metric | The metric is non-scalar, logged only during Lightning sanity checking, or never appears in `trainer.callback_metrics`. | Log scalar metrics with `self.log` or `self.log_dict`; check after real train/validation epochs rather than during sanity checks. |

## Repository setup and dependencies

| Symptom | Likely cause | Fix |
|---|---|---|
| `ruff`, `mypy`, `pytest`, `jupytext`, or docs commands are missing | Development dependencies were not installed. | Create/activate a development environment and run `make install-dev`. For stale environments, run `make reset-venv`, reactivate, then reinstall. |
| Package imports work but optional TIMM modules fail | `lightly[timm]` is not installed. | Install `lightly[timm]` only if the task needs TIMM / MAE / ViT-style optional modules; otherwise route to `ssl-building-blocks` for non-TIMM alternatives. |
| Video dataset support fails with PyAV/import errors | `lightly[video]` or PyAV system compatibility is missing. | Install `lightly[video]` only for video workflows. If PyAV system libraries are unavailable, document the optional dependency block and route data-layout work to `cli-data-embedding`. |
| Torch or torchvision cannot install on Python 3.13 | Compatible PyTorch wheels may be unavailable. | Use a supported Python version from the project's CI range rather than Python 3.13 unless the user has already validated the stack. |
| Minimal or pinned dependency checks mutate the environment | CI-parity install targets reinstall package dependencies. | Run `make install-minimal`, `make install-minimal-extras`, `make install-pinned`, or `make install-latest` only in disposable environments. |

## Tests and static checks

| Symptom | Likely cause | Fix |
|---|---|---|
| Slow tests were skipped unexpectedly | The command did not pass `--runslow`. | Use `make test` or `python -m pytest tests --runslow` when slow tests are required. `make test-fast` intentionally skips them. |
| DDP tests are skipped or hang | The shared gloo test pool was not enabled, or bare `pytest` was used. | Run `USE_PYTEST_POOL=1 python -m pytest tests --runslow -m DDP`. Keep DDP checks separate from ordinary unit smoke tests. |
| DDP spawned workers cannot import tests | `python -m pytest` was not used for spawn/importlib behavior. | Use the exact DDP command above; do not simplify it to bare `pytest`. |
| `make type-check` reports many unrelated modules skipped or excluded | The repository mypy config intentionally excludes several legacy or dynamic modules. | Treat configured excludes as project policy. Focus on new errors in touched files or public APIs. |
| Ruff formatting fails in CI after local edits | Imports or formatting were not regenerated. | Run `make format`, inspect diffs, then rerun `make format-check` or `make static-checks`. |
| A targeted pytest command passes but CI still fails | The change crossed examples, docs, dependency variants, slow tests, or Python-version boundaries. | Use `scripts/check_repo_dev_commands.py --ci-parity <changed paths>` to plan escalation; run the additional scoped commands in a disposable dev environment. |

## Docs and notebooks

| Symptom | Likely cause | Fix |
|---|---|---|
| Notebook CI reports changed notebooks | Example scripts changed without regenerating tracked notebooks. | Run `make generate-example-notebooks` and include the generated notebook diffs. Do not hand-edit generated notebooks as the primary source of truth. |
| Notebook generation fails because `jupytext` or `nbformat` is missing | Notebook/dev dependencies are not installed. | Run `make install-dev` or the notebook-specific pinned install target in a disposable environment. |
| Docs build command is missing Sphinx packages | Dev/docs dependencies were not installed. | Install the development dependency set, then run `cd docs && make html-noplot`. |
| Cached docs build hides warnings | Sphinx cache reused previous state. | Run `cd docs && make clean-html-noplot` for a clean no-plot build. |
| Full docs build is slow or starts running tutorial code | The full plotting/tutorial build was selected. | Prefer `cd docs && make html-noplot` for ordinary PR validation; run full docs only with explicit runtime and dependency budget. |

## Benchmarks and large-scale evaluation

| Symptom | Likely cause | Fix |
|---|---|---|
| Benchmark command requires ImageNet or large datasets | Benchmark-scale scripts are data- and time-dependent. | Do not run full benchmarks as a smoke test. Ask for dataset paths, hardware, runtime budget, output policy, and target metrics first. |
| Benchmark run writes large logs/checkpoints | Full benchmark workflows are artifact-producing experiments. | Confirm output directories and cleanup policy before execution. Use focused unit tests or synthetic evaluation snippets for helper validation. |
| GPU/distributed benchmark behavior differs from CPU smoke | Accelerator and multi-process behavior is only partial CPU-substitutable. | Treat GPU/DDP checks as optional or alternative unless the user explicitly requires them. Record skipped accelerator checks clearly. |

## Release and credentialed operations

PyPI publishing, release notifications, deployment commands, and cloud/secret-backed maintainer tasks are not part of this sub-skill's operating workflow. If asked to release the package, stop and request explicit maintainer-owned release instructions; do not infer credentials, upload artifacts, or run publishing commands from routine maintenance guidance.
