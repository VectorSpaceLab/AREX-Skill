# Cross-Cutting Troubleshooting

## When to read

Read this when PyTorch Forecasting fails before a task clearly belongs to a
single workflow: installation/import, optional extras, backend selection, or
version mismatch. For workflow-specific failures, route to the nearest
sub-skill troubleshooting reference.

## Install and import failures

### `ModuleNotFoundError: No module named 'pytorch_forecasting'`

Likely causes:

- The environment where the agent is running does not have the package installed.
- The distribution name was confused with the import name.
- The package was installed in a different Python environment.

Recover:

```bash
python -m pip install pytorch-forecasting
python - <<'PY'
import pytorch_forecasting as pf
print(pf.__version__)
PY
```

Use `python -m pip show pytorch-forecasting` to query distribution metadata;
use `import pytorch_forecasting` in Python code.

### Torch or Lightning import failures

PyTorch Forecasting depends on both `torch` and `lightning`. If an import fails
inside either package, first verify the active Python and dependency versions:

```bash
python -m pip check
python - <<'PY'
import torch, lightning, pytorch_forecasting
print(torch.__version__, torch.version.cuda, torch.cuda.is_available())
print(lightning.__version__)
print(pytorch_forecasting.__version__)
PY
```

On Windows or special CUDA systems, install the `torch` wheel that matches the
machine before installing PyTorch Forecasting. On ordinary CPU-only systems, a
CPU torch wheel is sufficient for the data, metric, and tiny model workflows in
this skill.

### Version mismatch after repository changes

If public API names, model lists, v2 status, optional extras, or dependency
constraints differ from [repo-provenance.md](repo-provenance.md), refresh this
repo skill. Do not patch around stale guidance by guessing from older APIs.

## Optional dependency failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'cpflows'` when using `MQF2DistributionLoss` | Base install lacks MQF2 optional extra | Install `pytorch-forecasting[mqf2]` or choose a non-MQF2 loss. |
| `ModuleNotFoundError: No module named 'optuna'` or `optuna_integration` | Tuning extra not installed | Install `pytorch-forecasting[tuning]` for Optuna tuning workflows. |
| Plotting or interpretation fails with missing `matplotlib` | Plotting dependency absent | Install `matplotlib` or skip plot generation and use numeric outputs. |
| Lightning warns that TensorBoard is unavailable and uses CSV logging | TensorBoard package absent | Install `tensorboard`/`tensorboardX` only when TensorBoard logs are needed. |

Avoid installing `all_extras` by default. Choose the narrow extra that matches
the task so environment setup stays reproducible and fast.

## Backend and hardware issues

- PyTorch Forecasting can train on CPU or GPU through Lightning; a GPU is not a
  prerequisite for constructing datasets, checking metrics, or running tiny
  smoke tests.
- Do not claim CUDA verification just because the host has a GPU. Verify the
  active Python environment with `torch.cuda.is_available()` and a tiny CUDA
  tensor allocation when GPU behavior is required.
- If a user asks for multi-GPU or distributed training, route model/trainer setup
  to `sub-skills/forecasting-models/` and check Lightning strategy/device
  settings separately.
- If MPS, ROCm, or vendor accelerator support is requested, treat it as a
  backend-specific PyTorch/Lightning environment problem first; the package's
  core APIs remain the same once tensors/dataloaders are valid.

## Data/model boundary mistakes

Common cross-skill routing mistakes:

- If an error names missing or invalid DataFrame columns, group/time index,
  target NaNs, categorical encoders, or `allow_missing_timesteps`, use
  `sub-skills/data-pipeline/` first.
- If an error appears in `.from_dataset()`, `Trainer.fit()`, `predict()`,
  checkpoint loading, interpretation, or model-specific compatibility, use
  `sub-skills/forecasting-models/`.
- If an error names quantiles, `output_size`, distribution parameters,
  non-finite losses, MQF2, or Optuna, use `sub-skills/metrics-and-tuning/`.
- If the task mentions D1/D2/M/P layers, `TimeSeries`, `Base_pkg`,
  `datamodule_cfg`, `model_cfg`, or `return_info`, use
  `sub-skills/api-v2-workflows/` and preserve the beta warning.

## Safe diagnostic helper

Run the bundled environment checker when you need a quick read-only diagnosis:

```bash
python scripts/check_environment.py
python scripts/check_environment.py --json
python scripts/check_environment.py --require-extra mqf2
```

The helper performs imports, version checks, optional extra probes, and a tiny
CPU torch operation. It does not train models, download data, or require a
repository checkout.
