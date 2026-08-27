# Utilities Workflow Recipes

These recipes are safe to run without network access. They use synthetic data only and are meant to be copied into notebooks, scripts, or smoke checks.

## 1. Build a reproducible toy time series

```python
import numpy as np
import pandas as pd
from orbit.utils.simulation import make_trend, make_seasonality, make_regression

seed = 2024
n = 36
idx = pd.date_range("2024-01-01", periods=n, freq="D")
trend = make_trend(n, method="rw", rw_loc=0.01, rw_scale=0.05, seed=seed)
season = make_seasonality(n, seasonality=7, method="fourier", order=2, seed=seed)
x, reg, coefs = make_regression(
    n,
    coefs=[0.3, -0.2],
    scale=0.2,
    noise_scale=0.01,
    sparsity=0.0,
    relevance=1.0,
    seed=seed,
)

df = pd.DataFrame({
    "date": idx,
    "y": trend + season + reg,
    "x1": x[:, 0],
    "x2": x[:, 1],
})
```

Tips:
- Use `method="rw"` when you want reproducible smoke data.
- Keep `relevance=1.0` and `sparsity=0.0` if you need repeatable outputs.
- Avoid `method="arma"` for smoke checks in this version because the seed is not carried into the ARMA sampler.

## 2. Add Fourier and seasonal features

```python
from orbit.utils.features import (
    make_fourier_series_df,
    make_seasonal_dummies,
    make_seasonal_regressors,
)

fs_df, fs_cols = make_fourier_series_df(df[["date"]].copy(), period=7, order=2, prefix="weekly_")
df, wd_cols = make_seasonal_dummies(df.copy(), "date", freq="weekday", sparse=False)
reg_blocks = make_seasonal_regressors(
    n=len(df),
    periods=[7, 365.25],
    orders=[2, 1],
    labels=["weekly", "yearly"],
)
```

Notes:
- `make_fourier_series_df` appends the new columns and returns their names.
- `make_seasonal_dummies` works best with `weekday` or `month` on current pandas.
- `make_seasonal_regressors` is just a dictionary of Fourier blocks; the caller decides how to concatenate them.

## 3. Compute knot locations and round-trip them to dates

```python
import pandas as pd
from orbit.utils.knots import get_knot_idx, get_knot_dates

weekly = pd.date_range("2024-01-07", periods=12, freq="W-SUN")
knot_idx = get_knot_idx(num_of_obs=len(weekly), num_of_segments=3)
knot_dates = get_knot_dates(weekly[0], knot_idx, pd.infer_freq(weekly))
```

Notes:
- Use a sorted, evenly spaced `date_array` before asking for knot dates.
- If you already know the target dates, pass them through `get_knot_idx(date_array=..., knot_dates=...)` and then validate the round-trip.

## 4. Build a full-span multi-series dataframe

```python
import numpy as np
import pandas as pd
from orbit.utils.general import expand_grid, regenerate_base_df

panel = expand_grid({
    "series_id": ["north", "south"],
    "date": pd.date_range("2024-01-31", periods=4, freq="ME"),
})
panel = panel.assign(y=np.arange(len(panel), dtype=float))
panel_missing = panel.drop(index=[2]).reset_index(drop=True)
panel_full = regenerate_base_df(panel_missing, "date", "series_id", val_cols=["y"], fill_na=0.0)
```

Notes:
- `expand_grid` is the easiest way to create a canonical panel.
- `regenerate_base_df` only rebuilds the cross-product of keys and dates that still exist in the input.
- Use `freq="ME"` instead of the older `"M"` alias when writing smoke data on pandas 3.x.

## 5. Prepare a quick tuning grid

```python
from orbit.utils.params_tuning import generate_param_args_list, grid_search_orbit

param_grid = {
    "level_sm_input": [0.1, 0.2],
    "seasonality_sm_input": [0.3, 0.5],
}
space = generate_param_args_list(param_grid)
```

Notes:
- `grid_search_orbit` expects a fitted Orbit model object from the forecasting or KTR workflows.
- This utilities sub-skill owns the grid construction and validation shape, not the model fit itself.

## 6. Create EDA views

```python
from orbit.eda.eda_plot import correlation_heatmap, dual_axis_ts_plot, ts_heatmap, wrap_plot_ts

heatmap_ax, heatmap_df, heatmap_pivot = ts_heatmap(
    df=df.rename(columns={"y": "value"}),
    date_col="date",
    value_col="value",
    seasonal_interval=7,
    use_orbit_style=False,
)
corr_ax = correlation_heatmap(df, ["x1", "x2"], use_orbit_style=False)
dual_ax = dual_axis_ts_plot(df, "x1", "x2", "date", use_orbit_style=False)
facet = wrap_plot_ts(df, "date", ["date", "x1", "x2"], use_orbit_style=False)
```

Notes:
- Pass `use_orbit_style=False` if the default Orbit style triggers font warnings in your environment.
- Keep a copy of your dataframe if you do not want date columns converted in place.
- Include the date column in `var_list` for `wrap_plot_ts`.
