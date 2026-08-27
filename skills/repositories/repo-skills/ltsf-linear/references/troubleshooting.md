# Troubleshooting

## Purpose

Read this when a run fails for a cross-cutting reason before diving into a
sub-skill's deeper troubleshooting page.

## Missing or incompatible PyTorch CUDA build

### Symptoms

- `ImportError` when importing `torch`
- `torch.cuda.is_available() == False` on a GPU host
- CUDA forward smoke fails in `check_env.py`

### Likely causes

- CPU-only torch wheel
- CUDA wheel that does not match the driver or Python version
- GPU passthrough is unavailable in the current session

### Next step

Use the shared preflight script and make the torch build match the hardware:

```bash
python scripts/check_env.py --scope root --device cuda
```

If the hardware is not available, route the task to a CPU-safe path instead of
claiming CUDA support.

## `--use_gpu` behaves unexpectedly in the root launcher

### Symptoms

- `run_longExp.py` ignores a command-line value that was meant to disable GPU
- The launcher still behaves as if GPU mode were enabled

### Likely cause

`run_longExp.py` parses `--use_gpu` as a Python `bool`, so plain string values
are fragile.

### Next step

Use the bundled wrapper for the core forecasting route, or pass the intent
through a helper that normalizes the flag before launching the source CLI.

## `ModuleNotFoundError: No module named 'pmdarima'`

### Symptoms

- `run_stat.py --help` fails
- `Naive` or `GBRT` baseline runs fail before argument parsing

### Likely cause

The statistical baseline module imports `pmdarima` at module load time.

### Next step

Install the statistical-baseline extras and rerun the import check.

## FEDformer parser or Wavelets failures

### Symptoms

- `KeyError` or invalid model selection in `FEDformer/run.py`
- Wavelets runs fail with missing `sympy`, `einops`, or `scipy`
- GPU forward smoke fails in the FEDformer route

### Likely causes

- The default `--model` value is not a valid FEDformer family member
- Wavelets needs extra scientific dependencies beyond the root stack
- CUDA is unavailable or incompatible

### Next step

Use the FEDformer sub-skill and its CUDA smoke script after confirming the
package stack.

## Pyraformer shape or TVM issues

### Symptoms

- Mask shape mismatch errors in `Pyraformer/long_range_main.py`
- Optional TVM-related import or compile errors
- Preprocessing outputs are missing or have the wrong shape

### Likely causes

- The configured window sizes or sequence lengths do not match the model's
  expectations
- The optional TVM path is enabled without its backend support
- The preprocessing helper was pointed at the wrong raw data file

### Next step

Use the Pyraformer sub-skill, confirm the `Pyraformer/data/` layout, and leave
`-use_tvm` off until you specifically need that backend.

## CSV layout problems

### Symptoms

- `KeyError: 'date'`
- missing target column errors
- empty datasets or very small validation/test splits

### Likely causes

- The CSV lacks a `date` column
- `features=S` or `features=MS` was selected without a valid `--target`
- The custom CSV is too short for the chosen `seq_len` and `pred_len`

### Next step

Run the shared data-layout helper and fix the file shape before changing the
model.

```bash
python scripts/check_data_layout.py --kind root --data-root dataset --data-path exchange_rate.csv --target OT
```

## When to stop and switch routes

If the failure is specific to one workflow family, stop using the root router
and switch to the matching sub-skill. The sub-skill troubleshooting pages carry
more detailed failure maps and route-specific recovery steps.
