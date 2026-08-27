# Installation And Compatibility

## Baseline Package

Featuretools 1.31.0 supports Python 3.9 through 3.12.

Install the base package:

```bash
python -m pip install featuretools
```

Conda-forge install:

```bash
conda install -c conda-forge featuretools
```

## Base Dependencies

The package metadata requires:

- `cloudpickle >= 1.5.0`
- `holidays >= 0.17`
- `numpy >= 1.25.0, < 2.0.0`
- `packaging >= 20.0`
- `pandas >= 2.0.0`
- `psutil >= 5.7.0`
- `scipy >= 1.10.0`
- `tqdm >= 4.66.3`
- `woodwork >= 0.28.0`

## Optional Extras

Use extras only when the workflow needs them:

- `featuretools[dask]` for `n_jobs > 1` and Dask-backed feature calculation.
- `featuretools[premium]` for premium primitives.
- `featuretools[nlp]` for NLP primitives.
- `featuretools[sql]` for the external SQL add-on.
- `featuretools[sklearn]` for the external sklearn transformer add-on.
- `featuretools[autonormalize]` for external autonormalize support.
- `featuretools[complete]` for the bundled convenience set (`premium`, `nlp`, `dask`).

The `docs` and `dev` extras are maintainer-oriented and are not required for ordinary skill use.

## Visualization Requirements

`EntitySet.plot` and `featuretools.graph_feature` need:

1. The Python `graphviz` package.
2. The Graphviz system executable (`dot`).

If either one is missing, keep the workflow on the non-graph path and use the textual references instead.

## Parquet Requirement

`EntitySet.to_parquet` is optional and requires `pyarrow` in the runtime environment.

If parquet support is unavailable, fall back to `to_pickle` or `to_csv`.

## Sanity Checks

A minimal verification sequence is:

1. `import featuretools as ft`
2. `ft.__version__ == '1.31.0'`
3. `ft.demo.load_mock_customer(return_entityset=True)` returns an `EntitySet`
4. `ft.dfs(...)` returns a non-empty feature matrix for the mock customer data

## Compatibility Notes

- `load_retail`, `load_flight`, and `load_weather` are demo loaders but may fetch data or depend on external downloads.
- `pkg_resources` deprecation warnings from Woodwork or related packages are expected in some environments and do not by themselves indicate failure.
- Use a clean environment for verification if optional extras or older dependency pins conflict with the base package.
