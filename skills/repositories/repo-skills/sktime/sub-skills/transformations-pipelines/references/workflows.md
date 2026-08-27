# Transformations and Pipelines Workflows

## Series-to-features

```python
import pandas as pd
from sktime.transformations.series.summarize import SummaryTransformer

x = pd.Series([1.0, 2.0, 3.0, 5.0])
features = SummaryTransformer().fit_transform(x)
```

## Differencing and inverse transform

```python
from sktime.transformations.series.difference import Differencer

diff = Differencer(lags=1, na_handling="fill_zero")
xd = diff.fit_transform(x)
```

Check index and leading missing-value behavior before feeding the output into an
estimator.

## Forecasting pipeline split

Use `TransformedTargetForecaster` to transform `y`; use `ForecastingPipeline` to
transform exogenous `X`. Nest them only when both target and exogenous sides need
processing. Route horizon and scoring decisions back to `forecasting`.

## Optional feature extractors

`tsfresh`, `catch22`, `Rocket`/`MiniRocket`, holiday features, torch/TensorFlow,
and deep-learning transforms may require task extras or platform-specific wheels.
Use a core transformer smoke first, then install/verify the exact optional package.
