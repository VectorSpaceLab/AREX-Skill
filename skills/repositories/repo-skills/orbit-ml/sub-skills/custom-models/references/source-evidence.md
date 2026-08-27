# Source evidence map

## Tutorial evidence
- `docs/tutorials/build_your_own_model.ipynb`
  - establishes the custom Pyro pattern: callable fitter + `ModelTemplate` subclass + `SVIForecaster`
  - shows `_fitter`, `_data_input_mapper = ['regressor']`, and `_supported_estimator_types = [PyroEstimatorSVI]`

## Template evidence
- `orbit/template/model_template.py`
  - minimal contract for custom models
- `orbit/template/ets.py`
  - baseline Stan-only forecasting template
- `orbit/template/lgt.py`
  - hybrid Stan / Pyro template
- `orbit/template/dlt.py`
  - Stan-only damped trend template
- `orbit/template/ktrlite.py`
  - Stan MAP-only knot model
- `orbit/template/ktr.py`
  - Pyro-only KTR template and known circular-import hotspot

## Forecaster evidence
- `orbit/forecaster/forecaster.py`
  - validates estimator compatibility
  - builds training / prediction meta
  - injects training data into the estimator
  - attaches extra public model helpers after fit
- `orbit/forecaster/map.py`
- `orbit/forecaster/full_bayes.py`
- `orbit/forecaster/svi.py`
  - show the post-fit binding pattern and the different prediction styles

## Estimator evidence
- `orbit/estimators/base_estimator.py`
- `orbit/estimators/stan_estimator.py`
- `orbit/estimators/pyro_estimator.py`
  - show the backend-specific fit signatures and returned keys

## Backend evidence
- `orbit/pyro/lgt.py`
- `orbit/pyro/ktr.py`
  - show the callable Pyro model shape and `T_STAR` usage
- `orbit/utils/stan.py`
  - shows bundled Stan compilation and custom-path handling
- `orbit/utils/set_cmdstan_path.py`
  - shows the repackaged CmdStan lookup
- `orbit/config.json`
  - pins `CMDSTAN_VERSION = 2.34.1`

## Test evidence
- `tests/orbit/estimators/test_stan_estimator.py`
- `tests/orbit/estimators/test_pyro_estimator.py`
- `tests/orbit/diagnostics/test_wbic.py`
  - confirm the estimator key contracts and the WBIC/BIC split

## Runtime facts captured in the snapshot
- direct import of `orbit.template.ktr` hits the circular-import path involving `orbit.models`
- `ModelTemplate`, forecaster, and estimator signatures are recorded in `architecture_snapshot.json`
- the custom Stan-path branch in `orbit/utils/stan.py` has an undefined `stan_file` reference
