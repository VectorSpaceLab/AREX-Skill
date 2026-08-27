# Vaex Installation and Package Split

Use this reference when deciding what to install, diagnosing imports, or explaining the difference between the Vaex meta package and component packages.

## Ordinary installs

For most users, install the meta package:

```bash
python -m pip install vaex
# or
conda install -c conda-forge vaex
```

Then verify:

```bash
python - <<'PY'
import vaex
print(vaex.__version__)
df = vaex.from_arrays(x=[1, 2, 3])
print(df.sum('x'))
PY
```

Prefer conda-forge when the environment is already conda-based or when compiled dependencies need consistent binary packages.

## Component packages

The `vaex` distribution is a meta package. Install components when a narrower environment is preferable:

| Distribution | Import surface | Use |
| --- | --- | --- |
| `vaex-core` | `import vaex` | Core DataFrame, lazy expressions, aggregation, Arrow/CSV openers, CLI dispatcher, settings. |
| `vaex-hdf5` | `import vaex.hdf5` | HDF5 open/export support and HDF5 opener entry points. |
| `vaex-viz` | `import vaex.viz` | Matplotlib plotting accessors such as `df.viz.histogram` and `df.viz.heatmap`. |
| `vaex-ml` | `import vaex.ml` | Transformers, pipelines, sklearn wrappers, KMeans/PCA, optional estimator wrappers. |
| `vaex-server` | `import vaex.server` | FastAPI/Tornado server, REST/WebSocket remote DataFrame support. |
| `vaex-jupyter` | `import vaex.jupyter` | Jupyter widgets and notebook frontend integration. |
| `vaex-astro` | `import vaex.astro` | FITS/VOTable/TAP/astro transforms and openers. |
| `vaex-graphql` | `import vaex.graphql` | Optional GraphQL accessor; dependency stack can be version-sensitive. |

The source snapshot used for this skill reported versions around Vaex `4.19.0`, with `vaex-core` `4.19.0`, `vaex-ml` `0.19.0`, `vaex-server` `0.10.0`, `vaex-hdf5` `0.15.0`, `vaex-viz` `0.6.0`, `vaex-jupyter` `0.9.0`, and `vaex-astro` `0.10.0`.

## Minimum environment by workflow

| Workflow | Minimum likely packages | Notes |
| --- | --- | --- |
| Core DataFrame and expressions | `vaex-core` | Includes core dependencies such as NumPy, Pandas, PyArrow, Dask, Pydantic, Rich, YAML, and compiled Vaex wheels. |
| HDF5/Arrow/Parquet/CSV roundtrips | `vaex-core vaex-hdf5` | Arrow/Parquet/CSV rely on PyArrow/Pandas paths; HDF5 needs `h5py` and the HDF5 plugin. |
| Plotting | `vaex-core vaex-viz matplotlib pillow` | Use Matplotlib Agg for noninteractive scripts. |
| ML pipelines | `vaex-core vaex-ml scikit-learn numba traitlets` | `vaex-ml` also depends on several estimator packages in the observed metadata. TensorFlow is an extra. |
| Server/REST | `vaex-core vaex-server fastapi uvicorn tornado cachetools` | Some FastAPI/TestClient stacks require `httpx2` for in-process route tests. |
| Jupyter widgets | `vaex-core vaex-viz vaex-jupyter` plus notebook frontend packages | Frontend rendering depends on JupyterLab/notebook extension state. |
| Astro/local FITS/VOTable | `vaex-core vaex-astro astropy` | Network TAP/cloud paths need additional trust/credential decisions. |

Avoid installing every optional extra just to inspect a core DataFrame or CLI task. Add optional packages only when the requested workflow needs them.

## Optional surfaces

- **GraphQL**: `vaex-graphql` depends on an older GraphQL/Tornado stack and can be version-sensitive. Use REST endpoints when possible.
- **TensorFlow**: `vaex-ml` exposes TensorFlow helpers behind an `all` extra in the observed metadata. Treat TensorFlow as optional and verify separately.
- **Cloud filesystems**: S3/GCS support can need `s3fs`, `gcsfs`, `fsspec`, credentials, region/endpoint settings, and cache planning.
- **Jupyter frontends**: widget imports are not proof that a browser frontend renders. Verify in the target notebook/JupyterLab environment.
- **GUI/Desktop**: PyQt/OpenGL desktop UI was excluded from this skill's selected operating graph.
- **Benchmarks**: benchmark scripts and ASV-like workflows are maintainer/expensive and not ordinary health checks.

## Source development and builds

Do not build from source for ordinary package use. Source development is materially different:

- Clone recursively so vendored submodules are present.
- Install PCRE development libraries/headers and compatible compilers.
- Use a Python version supported by the source metadata. The observed `vaex-core` metadata supported Python `>=3.9,<3.13`.
- Build extensions against compatible NumPy and C++ toolchains.
- Prefer conda-forge for compiled dependencies when possible.

A typical source-development preparation is conceptually:

```bash
git clone --recursive https://github.com/vaexio/vaex
cd vaex
# install a compatible Python plus PCRE/build tools through the chosen package manager
python -m pip install -e .
```

Ask before installing host-level compilers, PCRE libraries, or mutating a user-owned environment.

## Import checks

Use root [scripts/check_vaex_environment.py](../scripts/check_vaex_environment.py) for a cross-package installed-environment summary. Use sub-skill smoke scripts for focused checks:

- `sub-skills/dataframe-core/scripts/dataframe_smoke.py`
- `sub-skills/io-conversion/scripts/io_roundtrip_smoke.py`
- `sub-skills/expressions-analytics/scripts/analytics_smoke.py`
- `sub-skills/ml-pipelines/scripts/ml_pipeline_smoke.py`
- `sub-skills/visualization-jupyter/scripts/plot_smoke.py`
- `sub-skills/serving-remote/scripts/server_smoke.py`
- `sub-skills/cli-settings/scripts/vaex_cli_smoke.py`

Run each script with `--help` first.
