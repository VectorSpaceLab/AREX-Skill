# Troubleshooting

## 1) Acceleration never turns on

**Symptoms**
- `cuml.accel.enabled()` is `False`
- `is_proxy()` is `False` for imported estimators
- no GPU or fallback logs appear

**Likely causes**
- `sklearn`, `umap`, or `hdbscan` was imported before activation
- the notebook loaded `sklearn` before `%load_ext cuml.accel`
- the accelerator package is missing or not importable

**Fix**
- restart the process or notebook kernel
- activate first, then import the accelerated libraries
- use `python -m cuml.accel ...` or `%load_ext cuml.accel` as the first accelerator step

## 2) The model is a proxy but still falls back

**Symptoms**
- `is_proxy()` is `True`
- logs or profiler output show CPU execution

**Likely causes**
- the estimator family is only partially accelerated
- the estimator parameters are unsupported
- the input is sparse, has NaNs, or otherwise violates GPU constraints
- a dependency version is outside the tested window

**Fix**
- check `references/compatibility-and-profiling.md` for the relevant fallback triggers
- simplify the estimator parameters first, then reintroduce options one by one
- compare `profile()` output before and after the change

## 3) CLI / notebook command issues

**Symptoms**
- `python -m cuml.accel` runs, but the target code does not accelerate
- `--line-profile` errors when combined with `-m`
- the target script sees unexpected `sys.argv`

**Likely causes**
- activation happens after imports in the target script
- `--line-profile` was used with a module target
- the user expected CLI arguments to be consumed instead of forwarded

**Fix**
- move activation ahead of imports
- use a script, `-c`, or stdin when you need `--line-profile`
- remember that arguments after the script/module/cmd are forwarded to the target

## 4) Logging and profiling are too quiet

**Symptoms**
- no accelerator logs appear
- the profiler report is empty or incomplete

**Likely causes**
- log level is still at `warn`
- no accelerated call happened inside the profile context
- line profiling was used on code that did not reach the accelerated method

**Fix**
- use `-v`, `-vv`, `CUML_ACCEL_LOG_LEVEL=info`, or `cuml.accel.install(log_level="info")`
- keep the accelerated fit/predict/transform inside the profiling context
- confirm the estimator is actually on a supported path

## 5) Performance regressed instead of improving

**Symptoms**
- the accelerator is active, but the workload is slower

**Likely causes**
- the dataset is too small for transfer and dispatch overhead to pay off
- UVM / managed memory is oversubscribed
- the workload is switching back and forth between CPU and GPU
- the first call paid kernel compilation overhead

**Fix**
- compare against a larger batch or a larger dataset
- try `--disable-uvm`
- inspect the profiler report for mixed GPU/CPU execution
- warm up once before timing

## 6) Version warnings or dependency drift

**Symptoms**
- a runtime warning says the package version is outside the tested range
- UMAP or HDBSCAN behavior changes unexpectedly after an upgrade

**Likely causes**
- `scikit-learn`, `umap-learn`, or `hdbscan` moved outside the validated window
- `numba` changed to a version with known UMAP compatibility issues

**Fix**
- pin back to the tested ranges in the compatibility reference
- validate the exact workflow again after any upgrade
- for UMAP stability, prefer `numba<0.62`

## 7) How to interpret a fallback report

A CPU fallback is not automatically a failure. It usually means one of three things:

1. the estimator path is unsupported on GPU
2. the chosen parameters or inputs force a CPU path
3. the accelerator is active, but the best supported implementation for that call is still CPU

Use the profiler and logs together:

- logs answer *why* a call fell back
- the profiler answers *which* calls were on GPU or CPU
- `is_proxy()` answers *whether* the estimator class was accelerated at all

## 8) When to hand off elsewhere

- Need direct GPU control, different output types, or a custom cuML workflow? Hand off to `../python-estimators/SKILL.md`.
- Need multi-GPU or distributed execution? Hand off to `../distributed-dask/SKILL.md`.
- Need general package import or CUDA sanity checks before debugging accel? Use the root `cuml` troubleshooting path first.
