---
name: forecasting-experiments
description: "Construct and adapt TimeMixer forecasting experiment commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Forecasting Experiments

Use this sub-skill when the user wants to construct, adapt, audit, or explain TimeMixer commands for forecasting experiments. It covers long-term forecasting and short-term forecasting presets for ETT, electricity/ECL, Traffic, Weather, Solar, PEMS, and M4, plus custom forecasting command construction.

## Route here for

- Building a safe `run.py` command for a known forecast benchmark preset.
- Adapting a benchmark command to a custom CSV or changed forecast horizon.
- Explaining training, validation, testing, checkpoints, printed metrics, `test_results/`, and M4 forecast CSV outputs.
- Reducing epochs, batch size, GPU usage, or worker count before a user-approved expensive run.
- Debugging forecast-specific CLI, data-dimension, GPU, checkpoint, and M4 evaluation failures.

## Route elsewhere

- Raw dataset file layout, CSV columns, benchmark download placement, and deterministic data validation: use `data-preparation`.
- TimeMixer model internals, tensor shapes inside PDM/FMM, decomposition choices, and forward smoke checks: use `model-architecture`.
- Imputation, anomaly detection, or classification commands: use `universal-tasks`.

## Bundled operating assets

- `references/benchmark-recipes.md` lists source-script-derived forecasting presets and marks full benchmark execution as external-data/expensive.
- `references/workflows.md` explains command-building, training/test-only behavior, checkpoints, result locations, and custom adaptation.
- `references/troubleshooting.md` covers common forecast failures, including the `run.py --help` percent-format bug and CPU fallback.
- `scripts/build_timemixer_command.py` prints a `run.py` command or JSON plan; it never launches training.

## Safe default procedure

1. Identify the forecast family: long-term tabular/array data, PEMS traffic, Solar, or M4 seasonal short-term forecasting.
2. Use the bundled command builder to print, inspect, and adjust the command before any execution.
3. Confirm external data availability and user approval before running a full benchmark-scale training command.
4. For custom data, ensure `enc_in`, `dec_in`, and `c_out` match the selected feature mode and validated data dimensions.
5. Treat original benchmark shell scripts as distilled evidence only; do not invoke them from this skill.
