---
name: time-series-library
description: "Use Time-Series-Library (TSLib) to configure, run, debug, and
  adapt deep time-series forecasting, imputation, anomaly detection,
  classification, zero-shot, and model-customization workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Time-Series-Library (TSLib)

Use this skill when the task names Time-Series-Library, TSLib, `run.py`, TimesNet, TimeXer, iTransformer, PatchTST, DLinear, M4, ETT, UEA, PSM/MSL/SMAP/SMD/SWAT, long-term forecasting, short-term forecasting, time-series imputation, anomaly detection, classification, zero-shot forecasting, or adapting a model/script inside a TSLib-style checkout.

## Start Here

1. Confirm the environment and source layout before running training-scale work. From this skill directory, pass the user's TSLib checkout as `--repo-root`:
   ```bash
   python scripts/check_tslib_environment.py --repo-root /path/to/Time-Series-Library --check-torch --check-core-imports
   ```
2. For command/data debugging, create a tiny local `custom` CSV in the user's checkout instead of downloading benchmark data:
   ```bash
   python scripts/create_tiny_tslib_dataset.py --output /path/to/Time-Series-Library/dataset/tiny-custom/tiny.csv
   ```
3. Use the route map below. TSLib has one unified CLI (`python run.py ...`), but each task has different data layouts, output files, metrics, and failure modes.
4. Prefer `--no_use_gpu`, tiny custom data, `--train_epochs 1`, and `--num_workers 0` for smoke checks. Treat upstream benchmark scripts as templates, not as safe default commands.

## Route by Task

- **Data layout, CLI flags, outputs, and preflight checks**: use `sub-skills/data-and-cli/SKILL.md` for `run.py` arguments, dataset names, local-vs-Hugging Face fallback behavior, GPU flags, result/checkpoint folders, and safe data validation.
- **Forecasting workflows**: use `sub-skills/forecasting/SKILL.md` for long-term forecasting, short-term/M4 forecasting, exogenous/TimeXer recipes, zero-shot forecast routing, metrics, M4 summary behavior, and forecast command construction.
- **Imputation, anomaly detection, and classification**: use `sub-skills/imputation-anomaly-classification/SKILL.md` for masked reconstruction, reconstruction-threshold anomaly detection, UEA classification, task metrics, and dataset-specific troubleshooting.
- **Model catalog, optional dependencies, and customization**: use `sub-skills/foundation-models-and-customization/SKILL.md` for dynamic model discovery, Mamba and large time-series model dependencies, augmentation flags, custom `models/<Name>.py` files, and contribution-style script additions.

## Core Mental Model

TSLib is a source-tree benchmark framework rather than a packaged library with console entry points. The normal flow is:

```text
choose a task and bash/script template -> run python run.py with explicit flags ->
run.py dispatches to exp/Exp_* -> data_provider builds datasets/loaders ->
models/<Name>.py is lazy-imported -> train/test writes checkpoints, metrics, and result files
```

Important consequences:

- `--task_name` selects the experiment class, not just reporting labels.
- `--data` selects a loader family; `--root_path` and `--data_path` must match that family.
- `--model` must match a Python file under `models/`; `Exp_Basic` scans that directory dynamically.
- Many upstream shell scripts export `CUDA_VISIBLE_DEVICES` and run full benchmark settings. Remove or change those exports for your machine and use smoke settings first.
- Several optional model families need extra packages or model downloads; do not assume a basic TSLib environment can import every file in `models/`.

## References

- `references/installation-and-environment.md` explains public installation choices, optional dependencies, and safe smoke checks.
- `references/cli-arguments.md` summarizes the unified `run.py` argument families and task dispatch.
- `references/data-formats.md` documents CSV, M4, anomaly, and UEA layouts plus local-vs-Hub behavior.
- `references/model-catalog.md` lists model families, dynamic discovery, and optional dependency surfaces.
- `references/troubleshooting.md` covers cross-cutting install/import, data, CLI, GPU, output, and source-tree issues.
- `references/repo-provenance.md` records the source revision and evidence baseline.

## Helpers

- `scripts/check_tslib_environment.py` checks Python imports, selected models, `run.py --help`, and optional torch CUDA status without training; pass `--repo-root` for the user's TSLib checkout.
- `scripts/create_tiny_tslib_dataset.py` creates a small local `custom` CSV with a `date` column and target column for smoke commands.

## Operating Rules

- Do not run benchmark-scale scripts or download large datasets/model weights unless the user explicitly wants that cost.
- Do not recommend a raw upstream `scripts/.../*.sh` command without checking its `CUDA_VISIBLE_DEVICES`, dataset path, epochs, model dependencies, and output folders.
- Use local tiny fixtures for CLI/data validation; use real benchmark data only for final experiment work.
- Treat Mamba/MambaSL and large time-series model files as optional dependency routes. First decide whether the user's task requires them; otherwise choose a core model such as DLinear, TimesNet, TimeXer, PatchTST, or Transformer for smoke checks.
- Keep generated commands generic and portable across TSLib checkouts; never rely on a particular local checkout path.
