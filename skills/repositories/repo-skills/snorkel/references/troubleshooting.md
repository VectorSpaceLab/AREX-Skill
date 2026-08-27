# Cross-cutting troubleshooting

Use this root guide first for install/import/backend symptoms, then route workflow-specific problems to the nearest sub-skill troubleshooting file.

## Install and import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: snorkel` | Snorkel is not installed in the active Python environment. | Install with `pip install snorkel` or `conda install snorkel -c conda-forge`, then run `python scripts/check_snorkel_install.py`. |
| Snorkel imports from an unexpected location | Current directory or `PYTHONPATH` is shadowing the installed package. | Run from outside the checkout, inspect `import snorkel; print(snorkel.__file__)`, and remove stale path entries. |
| Install fails on Python 3.10 or older | Current package metadata requires Python `>=3.11`. | Create a Python 3.11+ environment and reinstall. |
| `pip check` reports conflicts after optional installs | Optional dependency versions are inconsistent with the base environment. | Recreate a clean environment, install base Snorkel first, then add only the optional stack needed for the workflow. |
| `torch` imports but GPU is unavailable | Snorkel workflows selected here are CPU-valid; CUDA is optional for PyTorch itself. | Use `device=-1` or `device="cpu"` in Snorkel configs unless the user explicitly needs CUDA. Do not treat CUDA absence as a Snorkel failure. |

## Optional dependency and backend checks

| Optional path | Symptom | Recovery |
| --- | --- | --- |
| Dask appliers | `ModuleNotFoundError: dask` or scheduler failures | Install `dask[dataframe]` and `distributed`; use `PandasLFApplier`/`PandasSFApplier` for small single-process jobs. |
| spaCy helpers | `Can't find model 'en_core_web_sm'` | Install a model with `python -m spacy download en_core_web_sm` or pass an installed model name to `language`. |
| Spark appliers/wrappers | Java gateway or hostname errors | Install Java and `pyspark==3.4.1`; for local containers set `SPARK_LOCAL_HOSTNAME=localhost`; run `python scripts/check_snorkel_install.py --check-spark`. |
| TensorBoard logging | Log directory exists but TensorBoard is empty | Confirm the classification `Trainer` is configured with `logging=True`, `log_writer="tensorboard"`, and a writable `log_writer_config.log_dir`. |

## Data and shape symptoms

| Symptom | Route | First check |
| --- | --- | --- |
| LF matrix has all `-1` rows, conflicts, or wrong cardinality | `sub-skills/labeling/references/troubleshooting.md` | Inspect `LFAnalysis(L).lf_summary()` before training `LabelModel`. |
| Mapper/preprocessor appears to mutate or drop rows | `sub-skills/data-transforms/references/troubleshooting.md` | Snorkel copies data points before transforms; `None` drops transformed copies. |
| Trainer refuses a dataloader or metric key | `sub-skills/classification/references/troubleshooting.md` | Check `DictDataset.Y_dict` tensor types, split names, and `task/dataset/split/metric:mode` format. |
| Slice scoring gives unexpected rows or missing labels | `sub-skills/slicing/references/troubleshooting.md` | Compare `S.dtype.names`, `S.shape`, and the dataset row order. |

## Safe verification sequence

1. Run `scripts/check_snorkel_install.py` for core imports.
2. Add `--check-spacy-model` or `--check-spark` only when those optional paths are needed.
3. Run the nearest sub-skill smoke script for the target workflow.
4. If a smoke fails, use that sub-skill's troubleshooting guide before changing the environment.

## Escalation boundaries

- Do not debug general Spark cluster deployment in this skill; only local Spark readiness and Snorkel Spark wrappers are covered.
- Do not debug generic PyTorch model architecture issues unless they involve Snorkel `Task`, `Operation`, `MultitaskClassifier`, or `Trainer` abstractions.
- Do not route cleanlab-style label-quality audits here unless the task specifically uses Snorkel weak supervision or label models.
- Do not rely on the original repository checkout for runtime help; use the bundled references and scripts in this skill tree.
