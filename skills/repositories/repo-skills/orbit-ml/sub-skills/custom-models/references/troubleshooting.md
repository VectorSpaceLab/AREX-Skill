# Troubleshooting custom-model internals

## 1) Estimator compatibility mismatch
Symptom: `ForecasterException` says the model is incompatible with the estimator.

Why it happens:
- `Forecaster` checks `model.get_supported_estimator_types()` before fit starts.
- The supported class list is concrete classes, not strings.

Examples from the source snapshot:
- `ETSModel` -> Stan MAP / MCMC only
- `KTRLiteModel` -> Stan MAP only
- `KTRModel` -> Pyro SVI only
- `LGTModel` -> Stan MAP / MCMC / Pyro SVI

Fix:
- choose the matching forecaster / estimator pair
- if you are writing a new model, make `_supported_estimator_types` explicit and narrow

## 2) Missing `cmdstanpy` or missing CmdStan path
Symptom: imports fail early, or Stan compilation fails before sampling.

Why it happens:
- `orbit/estimators/stan_estimator.py` imports `set_cmdstan_path()` at module import time
- `orbit/utils/set_cmdstan_path.py` only auto-points to a local repackaged path when `orbit/stan_compiled/cmdstan-<version>` exists
- otherwise it logs and falls back to the default CmdStan search path

Fix:
- install `cmdstanpy`
- ensure a working CmdStan installation exists in the default location or set it explicitly before the Stan estimator imports
- check `orbit/config.json` for the expected CmdStan version

## 3) Import-order and circular-import issues
Symptom: `ImportError: cannot import name 'KTRModel' from partially initialized module 'orbit.template.ktr'`

Why it happens:
- `orbit/template/ktr.py` imports `from ..models import KTRLite`
- `orbit/models/__init__.py` imports `KTR`
- that re-enters `orbit.template.ktr` while the module is still being built

Fix:
- treat direct import of `orbit.template.ktr` as a known hazard
- prefer importing the wrapper path `orbit.models.ktr.KTR` when you want the public factory
- if you are editing the source, break the cycle by moving the cross-package import into a narrower function boundary

## 4) Stan / Pyro backend mismatch
Symptom: the custom model loads, but the backend never finds your custom fitter or backend file.

Why it happens:
- `StanEstimator.fit()` ignores `fitter` and always resolves `orbit/stan/{model_name}.stan`
- `PyroEstimatorSVI.fit()` uses `fitter` when supplied, otherwise it imports `orbit.pyro.{model_name}.Model`

Fix:
- for custom Pyro models, provide `_fitter` and keep `_model_name` consistent
- for custom Stan models, you currently need a custom estimator or a different integration path; the stock estimator path is filename-driven, not callable-driven

## 5) Compiled-model path problems
Symptom: a Stan model compiles once, then later runs still use stale output or fail to locate the executable.

Why it happens:
- `orbit/utils/stan.py` prefers bundled `orbit/stan/{model_name}.stan`
- the timestamp-based stale-binary check is commented out
- the `stan_file_path` / `exe_file_path` branch currently references `stan_file` before assignment, so the custom-path branch is broken as written

Fix:
- use the bundled path when possible
- if you need a fresh compile, pass `force_compile=True` or remove the old executable
- if you are extending the helper, fix the undefined `stan_file` branch before relying on custom path injection

## 6) Custom model input mapping errors
Symptom: `ForecasterException` says a field is missing from data input.

Why it happens:
- `Forecaster.set_training_data_input()` expects either an Enum mapper or a list of attribute names
- list entries are lowercased and looked up on the model instance

Fix:
- make the model attribute names match the mapper keys exactly
- populate the attributes in `set_dynamic_attributes()` or `__init__()` before fitting
