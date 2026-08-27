---
name: modin
description: "Guide Modin pandas-compatible, distributed dataframe, I/O, engine
  configuration, interoperability, and experimental extension workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Modin

Use this repo skill when a task asks to use Modin as a pandas replacement, scale DataFrame/Series work across local CPUs or a cluster, configure Ray/Dask/other execution engines, read or convert tabular data, or use Modin's experimental extensions.

## Install and inspect

Install only the execution variant and optional integrations the workflow needs:

```bash
python -m pip install "modin[ray]"       # Ray
python -m pip install "modin[dask]"      # Dask + distributed
python -m pip install "modin[mpi]"       # Unidist/MPI; requires system MPI
python -m pip install "modin[spreadsheet]"  # optional widget integration
```

The base package requires Python 3.9+, pandas `>=2.2,<2.4`, NumPy, fsspec, packaging, psutil, and typing extensions. Confirm the selected engine before the first Modin operation:

```bash
python -c "import modin; import modin.pandas as pd; print(modin.__version__)"
python -m modin --versions
```

Read [references/troubleshooting.md](references/troubleshooting.md) when installation, engine startup, dependency compatibility, or data behavior is unclear. Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this graph matches a changed Modin checkout.

## Route by task

- **Pandas migration, DataFrame/Series operations, `read_csv`, `concat`, `groupby`, `apply`, correctness checks:** read [sub-skills/core-pandas-api/SKILL.md](sub-skills/core-pandas-api/SKILL.md).
- **Ray/Dask/Python/Native selection, `MODIN_*` variables, resources, backend movement, logging, metrics, progress, or range partitioning:** read [sub-skills/engines-configuration/SKILL.md](sub-skills/engines-configuration/SKILL.md).
- **Parquet/JSON/SQL, multi-file glob I/O, custom text parsing, pandas/Arrow/Ray/Dask conversion, or direct partitions:** read [sub-skills/io-interoperability/SKILL.md](sub-skills/io-interoperability/SKILL.md).
- **Batch Pipeline, distributed XGBoost, spreadsheet, Modin NumPy/Polars, experimental sklearn, or PyTorch DataLoader:** read [sub-skills/advanced-extensions/SKILL.md](sub-skills/advanced-extensions/SKILL.md).

## Cross-cutting rules

1. Configure `MODIN_ENGINE`, `MODIN_BACKEND`, and resource variables before importing/initializing Modin. Do not set a backend together with conflicting engine/storage variables.
2. In executable Ray/Dask programs, put distributed work in `main()` under `if __name__ == "__main__":`; this avoids Python multiprocessing spawn failures.
3. Treat `defaulting to pandas` warnings as compatibility-preserving but potentially slow materialization. Validate correctness and measure warm operations separately from engine startup.
4. Materializing with `to_pandas()`, `to_numpy()`, or a third-party consumer can collect the whole object on the driver. Bound the sample or check schema/aggregates instead.
5. Treat `modin.experimental.*` APIs and optional frontends as version-sensitive. Verify imports and a tiny local fixture before applying them to large or remote data.
6. Keep credentials out of code and logs. Use secure runtime configuration for object stores, SQL connections, Ray clusters, and MPI.

## Bundled checks

- [scripts/check_modin_environment.py](scripts/check_modin_environment.py) prints package/backend metadata and runs a tiny DataFrame check under Python, Ray, Dask, or Native/Pandas execution without needing the source checkout.
- The focused sub-skills own workflow helpers for taxi-style pandas validation, backend smoke/config export, local glob I/O, interoperability, Batch Pipeline, and XGBoost.
