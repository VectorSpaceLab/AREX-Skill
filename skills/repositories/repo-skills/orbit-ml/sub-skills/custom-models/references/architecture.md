# Orbit custom-model architecture

## One-line summary
Orbit separates **model template**, **forecaster**, **estimator**, and **backend**:

`ModelTemplate -> Forecaster -> Estimator -> Stan/Pyro backend`

## Base contract
`orbit.template.model_template.ModelTemplate` is the minimal interface.
Key methods / fields from the source snapshot:
- `__init__(self, **kwargs)`
- `predict(self, posterior_estimates, df, training_meta, prediction_meta, include_error=False, **kwargs)`
- `set_dynamic_attributes(self, df, training_meta)`
- `set_init_values(self)`
- `_data_input_mapper`, `_model_name`, `_fitter`, `_supported_estimator_types`

A custom model normally overrides:
- `_model_name` to match the backend file name or fitter lookup
- `_data_input_mapper` to tell `Forecaster` what to pass into the backend
- `_supported_estimator_types` to control admissible forecasters
- `set_dynamic_attributes()` to derive data-dependent arrays from the training frame
- `predict()` to turn posterior samples into predictions and decompositions

## Forecaster lifecycle
`orbit.forecaster.forecaster.Forecaster` handles the shared orchestration:
1. validate the input frame
2. build `training_meta`
3. call `model.set_dynamic_attributes(...)`
4. build `training_data_input`
5. call `model.set_init_values()`
6. invoke `estimator.fit(...)`

Important behaviors:
- `Forecaster` validates `estimator_type` against `model.get_supported_estimator_types()`.
- Any public callable on the model that is not in `COMMON_MODEL_CALLABLES` becomes an attached helper after fit via `load_extra_methods()` in the child forecasters.
- `set_forecaster_training_meta()` is the place where point/MCMC flags are injected into the training payload.

## Forecaster variants
- `MAPForecaster`: point estimate, then optional bootstrap for intervals
- `FullBayesianForecaster`: uses Stan MCMC and can compute WBIC when sampled at `log(n)` temperature
- `SVIForecaster`: Pyro VI variant with the same point-estimate bootstrap pattern

Common fit signatures from the source snapshot:
- `MAPForecaster.fit(self, df, **kwargs)`
- `FullBayesianForecaster.fit(self, df, point_method=None, keep_samples=True, sampling_temperature=1.0, **kwargs)`
- `SVIForecaster.fit(self, df, point_method=None, keep_samples=True, sampling_temperature=1.0, **kwargs)`

## Estimators
### Stan
- `StanEstimator.__init__(self, num_warmup=900, num_sample=100, chains=4, cores=8, algorithm=None, suppress_stan_log=True, **kwargs)`
- `StanEstimatorMCMC.fit(self, model_name, model_param_names, sampling_temperature, data_input, fitter=None, init_values=None)`
- `StanEstimatorMAP.fit(self, model_name, model_param_names, data_input, fitter=None, init_values=None)`

Stan path facts:
- module import calls `set_cmdstan_path()` immediately
- `get_compiled_stan_model()` looks up `orbit/stan/{model_name}.stan`
- Stan output always includes `loglk` alongside the requested model parameters

### Pyro
- `PyroEstimatorSVI.fit(self, model_name, model_param_names, data_input, sampling_temperature, fitter=None, init_values=None)`
- if `fitter` is not supplied, the estimator loads `orbit.pyro.{model_name}.Model`
- the custom fitter path is what the build-your-own-model notebook demonstrates

Pyro output facts:
- the estimator returns the named model parameters
- `training_metrics` include `loss_elbo`, `loglk`, and `sampling_temperature`

## Template family map
| Model template | Supported estimators | Notes |
| --- | --- | --- |
| `ETSModel` | `StanEstimatorMAP`, `StanEstimatorMCMC` | Pure Stan backend |
| `LGTModel` | `StanEstimatorMAP`, `StanEstimatorMCMC`, `PyroEstimatorSVI` | Hybrid Stan + Pyro |
| `DLTModel` | `StanEstimatorMAP`, `StanEstimatorMCMC` | Pure Stan backend |
| `KTRLiteModel` | `StanEstimatorMAP` | Stan MAP only |
| `KTRModel` | `PyroEstimatorSVI` | Pyro only; composes KTRLite internally |

## KTR composition detail
`KTRModel` is not just a standalone backend wrapper. Its `set` / `predict` flow reuses `KTRLite` to obtain level and seasonality structure, then layers the Pyro regression machinery on top. That makes KTR the clearest example of a multi-stage custom model in Orbit.

## Custom Pyro model pattern from the notebook
The tutorial’s minimal pattern is:
- a callable fitter class with `__init__(data)` and `__call__()`
- a `ModelTemplate` subclass with `_fitter = MyFitter`
- `_data_input_mapper = ['regressor']`
- `_supported_estimator_types = [PyroEstimatorSVI]`
- `set_dynamic_attributes()` that extracts the regressor matrix
- `predict()` that maps posterior samples back to a prediction array

That pattern is the quickest way to add a new build-your-own model.
