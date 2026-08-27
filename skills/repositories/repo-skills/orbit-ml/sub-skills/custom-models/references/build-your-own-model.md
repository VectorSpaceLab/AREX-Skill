# Build-your-own-model evidence

Source anchor: bundled build-your-own-model tutorial evidence

## What the tutorial proves
The notebook shows that Orbit custom models are built by combining:
- a **callable fitter** for the backend math
- a **`ModelTemplate` subclass** for Orbit wiring
- a compatible **forecaster / estimator pair**

## Minimal custom Pyro shape
The tutorial’s working example follows this structure:

- `MyFitter`
  - accepts `data` in `__init__`
  - lowercases keys and stores tensors on the instance
  - implements `__call__()`
  - samples parameters with Pyro and returns `extra_out` containing at least `log_prob`

- `BayesLinearRegression(ModelTemplate)`
  - `_fitter = MyFitter`
  - `_data_input_mapper = ['regressor']`
  - `_supported_estimator_types = [PyroEstimatorSVI]`
  - sets `_model_param_names = ['bias', 'weight', 'obs_sigma']`
  - `set_dynamic_attributes()` pulls the regressor matrix from the DataFrame
  - `predict()` turns posterior draws into prediction arrays

## Forecaster usage in the tutorial
The notebook instantiates:
- `SVIForecaster(model=model, response_col='y', date_col='week', estimator_type=PyroEstimatorSVI, ...)`

Then it runs:
- `fit(train_df)`
- `get_posterior_samples()` to inspect coefficients
- `predict(df)` for forecasting

## Practical lesson
If you are extending Orbit with a custom Pyro model, the model object must expose:
- the exact input names the estimator needs
- a callable backend fitter
- a `predict()` method that understands posterior sample shapes

If you are extending Orbit with a Stan-backed model, the current repo path is different: the built-in estimators resolve compiled Stan files by model name rather than by custom callable fitter.
