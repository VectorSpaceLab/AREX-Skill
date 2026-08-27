---
name: operations-and-migration
description: "Operate NeuralProphet installs, CLI/version checks, logging,
  seeding, plotting, save/load, accelerator settings, and TorchProphet
  migration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Operations and migration

Use this sub-skill when the task is about NeuralProphet operational behavior rather than forecast design: install/version diagnostics, the `python -m neuralprophet --version` CLI, logging and reproducibility controls, plotting backends, optional plotting extras, model serialization, CPU/GPU loading, PyTorch Lightning trainer options, or migrating Prophet-style code through `TorchProphet`.

## Load this when the user asks to

- Check that `neuralprophet` is importable or identify the installed version.
- Save a fitted `NeuralProphet` model, load it again on CPU, or smoke-test serialization.
- Suppress or raise NeuralProphet logs, set random seeds, or make a fit run deterministic.
- Choose `matplotlib`, `plotly`, `plotly-static`, or `plotly-resampler` plotting backends.
- Diagnose optional plotting extras such as `plotly-resampler` or static export support.
- Pass accelerator or `trainer_config` settings without assuming CUDA is available.
- Convert Prophet-style code to `TorchProphet` and explain unsupported Prophet arguments.

## Reference map

- Start with [operations.md](references/operations.md) for task workflows and copyable snippets.
- Use [api-reference.md](references/api-reference.md) for distilled signatures, backend choices, and migration mappings.
- Use [troubleshooting.md](references/troubleshooting.md) when imports, plotting, serialization, compatibility pins, accelerator selection, or Prophet wrapper warnings fail.
- Run [scripts/save_load_smoke.py](scripts/save_load_smoke.py) to prove tiny CPU fit → save → CPU load → predict without persistent output unless `--output-path` is explicitly supplied.

## Boundaries

- For end-to-end training and forecasting recipes, route to `../core-forecasting/`.
- For seasonality, regressors, events, holidays, and component configuration details, route to `../components-and-exogenous/`.
- For conformal prediction, uncertainty evaluation, interval plots, and uncertainty result interpretation, route to `../evaluation-and-uncertainty/`.

Do not ask future agents to reopen upstream source files, tests, notebooks, or external documentation. The operational facts needed for this scope are distilled in this sub-skill's references and script.
