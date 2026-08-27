---
name: forecasting
description: "Configure, run, and debug Time-Series-Library long-term,
  short-term/M4, exogenous/TimeXer, and zero-shot forecasting workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TSLib Forecasting

Use this sub-skill for TSLib forecasting tasks: long-term forecasting on ETT/custom/ECL/Traffic/Weather/Exchange/ILI-style CSVs, short-term M4 forecasting, TimeXer/exogenous variable recipes, zero-shot forecasting with large time-series models, and forecasting metric/output interpretation.

## Route Here

- Build or revise `python run.py --task_name long_term_forecast ...` commands.
- Configure `--seq_len`, `--label_len`, `--pred_len`, `--features`, `--target`, channel counts, and forecast model dimensions.
- Use TimeXer or `features MS` for exogenous/target-only forecast settings.
- Run or debug `short_term_forecast` with M4 seasonal patterns and SMAPE/OWA outputs.
- Understand zero-shot `--task_name zero_shot_forecast` and optional LTSM model dependencies.
- Interpret `metrics.npy`, `pred.npy`, `true.npy`, result text files, plot PDFs, and M4 forecast CSVs.

## Reroute

- Data file validation, UEA/anomaly layouts, generic CLI outputs, or CPU/GPU preflight: use `../data-and-cli/SKILL.md`.
- Imputation, anomaly detection, and classification: use `../imputation-anomaly-classification/SKILL.md`.
- Adding models, Mamba/LTSM dependency installation, and augmentation flags: use `../foundation-models-and-customization/SKILL.md`.

## Start Fast

Render a small command rather than copying a benchmark script verbatim:

```bash
python scripts/build_tslib_command.py long-term \
  --model DLinear --root-path ./dataset/tiny-custom/ --data-path tiny.csv \
  --model-id tiny_custom --features M --channels 3 \
  --seq-len 8 --label-len 4 --pred-len 4 --cpu-smoke
```

Then run the printed command from the TSLib checkout. Use real benchmark scripts only after paths, GPU, dependencies, and expected cost are clear.

## Forecasting Modes

- **Long-term forecast**: `--task_name long_term_forecast`; uses sliding windows and writes MAE/MSE/RMSE/MAPE/MSPE plus optional DTW.
- **Short-term/M4 forecast**: `--task_name short_term_forecast --data m4`; uses M4 seasonal patterns and losses such as SMAPE. Final averaged M4 metrics print after all six seasonal forecast CSVs exist.
- **Exogenous/TimeXer forecast**: still uses `long_term_forecast`; TimeXer recipes often set `--model TimeXer` and may use `features MS` when forecasting a target with exogenous inputs.
- **Zero-shot forecast**: `--task_name zero_shot_forecast --is_training 0`; model files such as Chronos, Moirai, TimesFM, TiRex, Sundial, and TimeMoE can require optional packages, model downloads, and CUDA assumptions.

## References and Helpers

- `references/forecasting-workflows.md` gives long-term, M4, TimeXer, and zero-shot recipes.
- `references/metrics-and-results.md` explains forecast metrics and result files.
- `references/troubleshooting.md` covers forecasting-specific data/window/channel/model errors.
- `scripts/build_tslib_command.py` renders safe starter commands for long-term, M4, TimeXer, and zero-shot workflows.
- `../../references/model-catalog.md` maps model names to optional dependency surfaces.

## Avoid

- Do not treat zero-shot LTSM source files as verified just because core TSLib imports work.
- Do not run M4 or long-horizon benchmark scripts as a smoke check; use tiny data and short windows first.
- Do not use `features MS` without confirming `--target` and output channel expectations.
