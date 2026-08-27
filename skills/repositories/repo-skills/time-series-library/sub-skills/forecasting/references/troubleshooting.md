# Forecasting Troubleshooting

## Forecast command starts a Hub download

Use `../data-and-cli/SKILL.md` to validate local CSV or M4 files first. For a custom CSV, `os.path.join(root_path, data_path)` must exist; otherwise TSLib tries a Hub config based on the filename.

## Window lengths produce empty datasets

Symptoms:

- DataLoader length is zero.
- Training exits before useful batches.
- Validation/test split has no windows.

Fixes:

- Reduce `--seq_len` and `--pred_len` for small custom data.
- Add more rows to the CSV.
- Remember `custom` splits chronologically; each split needs enough rows for the requested windows.

## Channel or target mismatch

Symptoms:

- Tensor shape mismatch in loss or model head.
- TimeXer `features MS` appears to return only one channel.

Fixes:

- Count non-date CSV columns and set `--enc_in`, `--dec_in`, and `--c_out` to match the model recipe.
- For `features S` or `MS`, set `--target` and expect target-channel slicing in evaluation.
- For TimeXer `features MS`, target-only output is expected.

## M4 averaged metrics never print

`M4Summary` evaluates only after all six seasonal forecast CSVs exist in `m4_results/<model>/`: Yearly, Quarterly, Monthly, Weekly, Daily, and Hourly. A single `Monthly` run writes a forecast CSV but only prints a reminder.

## Zero-shot model import or download fails

Common causes:

- Missing package: `chronos`, `timesfm`, `uni2ts`, `tirex`, or `transformers`.
- Model cache/network access unavailable.
- Source file hard-codes CUDA or uses a CUDA device map while the environment is CPU-only.

Fixes:

- Decide whether the task truly requires zero-shot LTSM execution. If not, use core forecasting models.
- Install only the selected model family's package and validate import before `run.py`.
- Check model file device assumptions and available GPU before trying CPU.

## Copied benchmark script is too expensive

Start with `scripts/build_tslib_command.py` and tiny data. Then progressively restore horizons, model width, batch size, GPU, and all benchmark datasets.

## Forecast metrics contain `inf` or `nan`

MAPE/MSPE divide by the true values and can be unstable around zeros. Check MAE/MSE/RMSE first, inspect the data scale, and avoid using tiny synthetic data for metric claims.
