# ClassSR troubleshooting

## 1) Package import or dependency failure

**Symptoms**
- `import physo` fails
- `torch`, `numpy`, `sympy`, `pandas`, `matplotlib`, or `scikit-learn` is missing

**Check**
- make sure the CPU runtime is installed and importable
- confirm the environment has the package dependencies used by the quick-start helper

**Fix**
- reinstall the missing package(s)
- rerun the smoke helper only after imports succeed

## 2) List / tensor shape mismatch across realizations

**Symptoms**
- `multi_X` and `multi_y` do not have the same length
- one realization has the wrong `n_dim`
- one `X_i` / `y_i` pair has mismatched sample counts

**Check**
- `len(multi_X) == len(multi_y)`
- every `multi_X[i].shape[1] == multi_y[i].shape[0]`
- every `multi_X[i].shape[0]` matches the same shared `n_dim`

**Fix**
- keep one list entry per realization
- allow different realization lengths only when each pair is internally consistent

## 3) Inconsistent realization lengths

**Symptoms**
- one realization is shorter than the others and the run fails anyway
- free-constant initialization for spe constants does not match the number of realizations

**Check**
- shorter realizations are valid
- `spe_free_consts_init_val` vectors must still match the full `n_realizations`

**Fix**
- keep the short realization, but align all spe-constant vectors and weight arrays with the realization count
- if you want the same initialization for every realization, use a scalar and let the package broadcast it

## 4) Wrong `multi_y_weights` length or shape

**Symptoms**
- assertion error from dataset preparation
- per-point weight arrays are one element too short or too long

**Check**
- `len(multi_y_weights) == len(multi_y)` when weights are list-like
- each per-point weight array matches the corresponding `y_i` length

**Fix**
- if you only need per-realization weighting, pass scalars instead of per-point arrays
- if you need per-point weighting, rebuild each weight vector to match the target length exactly

## 5) Missing or malformed free-constant units or init values

**Symptoms**
- assertion error when building the library config
- class and spe constant names do not line up with the unit lists
- passing a name-keyed mapping of init values to the `ClassSR` wrapper triggers a `KeyError`

**Check**
- the number of names matches the number of unit vectors
- all unit vectors are numeric and consistent with the rest of the run

**Fix**
- repair the class/spe constant lists before calling `ClassSR`
- pass init values as list-like / array-like sequences aligned with the constant-name order when using the `ClassSR` wrapper
- if the problem is dimensionless, use zero vectors or omit the units arguments for those constants

## 6) CPU versus CUDA or `parallel_mode` confusion

**Symptoms**
- the run behaves differently on another machine
- a user expects GPU verification that was never performed

**Check**
- keep the smoke helper on `device='cpu'`
- set `parallel_mode=False` for the bundled helper

**Fix**
- use the CPU helper as the baseline
- only move to a GPU or parallel setup after the CPU path is stable
- if the installed torch build is CUDA-capable, ignore the parallel-mode warning spam during the CPU smoke run unless it becomes a hard failure

## 7) Missing LaTeX or display extras

**Symptoms**
- LaTeX warnings during import or pretty-printing
- plotting or expression rendering falls back to plain text

**Check**
- this is usually an optional display dependency issue, not a ClassSR core failure

**Fix**
- use `get_infix_pretty()` or `get_infix_sympy()` for verification
- treat LaTeX rendering as optional unless you explicitly need publication-quality output

## 8) Log and Pareto inspection

**Symptoms**
- a saved run has no obvious result file
- the Pareto front seems missing after the run

**Check**
- make sure the logger was created with saving enabled if you want a `_pareto.pkl` file
- inspect the in-memory logger first with `run_logger.get_pareto_front()`

**Fix**
- use `run_logger.get_pareto_front()` during the run
- reload the saved `_pareto.pkl` with `physo.read_pareto_pkl(...)` if a file was written

## Quick diagnostic sequence

1. Confirm the input is a list of realizations, not a single SR dataset.
2. Check each `X_i`, `y_i`, and weight vector length.
3. Check class/spe constant name and unit counts.
4. Keep the run on CPU with the smoke helper.
5. Inspect the Pareto front before debugging expression content.
