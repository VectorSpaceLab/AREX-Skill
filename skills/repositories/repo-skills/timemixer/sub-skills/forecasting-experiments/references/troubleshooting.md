# Forecasting Troubleshooting

## `run.py --help` fails before showing help

Symptoms may include a formatting error such as `unsupported format character ')'` while argparse is rendering help.

Cause: one CLI help string contains a literal percent sign for the anomaly ratio option. Argparse help text uses percent-format interpolation, so a bare `%` can break `--help` rendering. The command builder in this sub-skill has independent help and does not import `run.py`.

Workarounds:

- Use the bundled command builder for forecast command construction.
- Inspect the CLI reference or source parser text instead of relying on `python run.py --help`.
- If editing a private checkout for diagnostics, escape the percent sign as `%%` in the affected help string; do not treat that local edit as part of a benchmark result.

`run.py --help` can also fail during imports if optional dependencies for non-forecast tasks are missing, because all experiment modules are imported before argparse parses arguments.

## Required CLI arguments despite defaults

The CLI marks these options required even though defaults are defined:

- `--task_name`
- `--is_training`
- `--model_id`
- `--model`
- `--data`

Always include them in generated commands. The bundled builder emits them automatically for presets and requires them for generic commands.

## Data dimensions do not match model dimensions

Common symptoms:

- loss shape mismatch between model outputs and `batch_y`;
- reshape errors inside the forecasting head;
- convolution input-channel errors;
- PEMS inverse transform errors.

Checks:

1. Count value channels after the loader rules, not raw file columns. Custom CSV with `features=M` uses all columns except `date`; `features=S` uses only `target`; `features=MS` uses all value columns but compares only the last/target output channel.
2. Set `enc_in`, `dec_in`, and `c_out` consistently:
   - `features=M`: normally all equal the value-channel count.
   - `features=S`: all equal `1`.
   - `features=MS`: `enc_in` and `dec_in` equal the multivariate input count; normally `c_out=1`.
3. For PEMS presets, match the `.npz` file to the expected sensor count: PEMS03 `358`, PEMS04 `307`, PEMS07 `883`, PEMS08 `170`.
4. For Solar, match `solar_AL.txt` to `137` numeric columns for the benchmark preset.
5. Route raw data validation to `data-preparation` before changing model dimensions.

## PEMS and Solar ignore calendar time marks

PEMS and Solar dataset classes create zero placeholder marks, and the long-term forecast experiment passes `None` time marks to the model for these data flags. Consequences:

- Changing `--freq` does not add calendar features for `data=PEMS` or `data=Solar`.
- Missing `date` columns are expected for Solar text and PEMS `.npz`; do not try to force custom-CSV date logic onto these loaders.
- `use_future_temporal_feature=1` is not useful unless future time marks are actually passed.

## M4 single-season run does not print averaged M4 metrics

M4 test writes one seasonal forecast CSV at a time under `m4_results/TimeMixer/<Season>_forecast.csv`. The summary evaluator prints averaged sMAPE, MAPE, MASE, and OWA only after all six seasonal files exist: Yearly, Quarterly, Monthly, Weekly, Daily, and Hourly.

If only one season has run, the expected message is that averaged indices can be calculated after all six tasks are finished. This is not an error unless the user expected full M4 evaluation from a single command.

Additional M4 checks:

- `seasonal_patterns` must be one of `Yearly`, `Quarterly`, `Monthly`, `Weekly`, `Daily`, `Hourly`.
- `pred_len`, `seq_len`, and `label_len` are derived from the seasonal pattern in the short-term experiment setup.
- M4 losses use the N-BEATS-style `SMAPE`, `MAPE`, or `MASE` call signature with insample windows, frequency, forecast, target, and mask. The benchmark preset uses `SMAPE`.
- The M4 evaluator expects the root M4 files including metadata, cached train/test arrays, and the Naive2 submission file.

## CPU fallback and GPU flags

The CLI defaults to `use_gpu=True`, then disables GPU only when PyTorch reports CUDA unavailable. However, `--use_gpu` is parsed as `type=bool`; strings such as `False` are truthy in Python's `bool()` conversion. Therefore `--use_gpu False` may still behave as true.

Reliable CPU fallback:

```bash
CUDA_VISIBLE_DEVICES='' python -u run.py ...
```

The bundled command builder emits this prefix when called with `--no-use-gpu`.

GPU guidance:

- Use `--gpu 0` for a single visible GPU when needed.
- For multi-GPU raw commands, also use `--use_multi_gpu --devices 0,1`; verify memory and batch size first.
- `--use_amp` only affects long-term forecasting paths that check AMP; do not assume it works for every short-term/M4 path.
- CUDA availability is optional for command construction; full benchmark runtime can be much slower on CPU.

## Checkpoint not found in test-only mode

Training saves the best model under the chosen checkpoint root, usually `checkpoints/<setting>/checkpoint.pth`. Test-only mode rebuilds the setting string and loads from `./checkpoints/<setting>/checkpoint.pth` in the forecast experiment code.

If test-only mode cannot find the checkpoint:

1. Confirm `model_id`, `comment`, `model`, `data`, `seq_len`, `pred_len`, `d_model`, `n_heads`, `e_layers`, `d_layers`, `d_ff`, `factor`, `embed`, `distil`, `des`, and iteration index match the training command.
2. If training used a custom `--checkpoints` directory, either copy the checkpoint into `./checkpoints/<setting>/checkpoint.pth` or patch the local test loader path.
3. Do not change model dimensions between training and test-only loading.

## Full benchmark commands are too slow or run out of memory

Likely causes:

- high channel counts such as Traffic `862`, PEMS07 `883`, or Solar `137` with `d_model=512`;
- long M4 all-season training;
- large `batch_size` from a benchmark preset;
- CPU fallback used for a GPU-sized preset.

Mitigations for debugging only:

- reduce `--train-epochs`, `--batch-size`, and `--num-workers`;
- use a shorter `pred_len` when the task permits;
- keep `down_sampling_layers` and `down_sampling_window` source-derived unless diagnosing shape issues;
- clearly label any reduced command as a smoke/debug run, not a reproduced benchmark.

## Unexpected metric behavior

- Long-term non-PEMS validation uses MSE loss; final test prints MSE and MAE.
- PEMS validation chooses L1/MAE and inverse-transforms predictions and targets before metrics.
- M4 benchmark training commonly uses SMAPE loss and final summary computes sMAPE, MAPE, MASE, and OWA after all six seasons.
- Current forecast experiment code primarily prints metrics and writes plots/CSV examples rather than saving a standard `results/` array for every forecast benchmark.
