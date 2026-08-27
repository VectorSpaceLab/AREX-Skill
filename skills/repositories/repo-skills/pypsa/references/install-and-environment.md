# Install and Environment Guidance

## Purpose

Read this before installing PyPSA, selecting optional extras, choosing solvers, or interpreting environment-variable options.

## Base installation

PyPSA supports Python 3.11 and newer. Use an isolated environment. Common install commands are:

```bash
pip install pypsa
conda install -c conda-forge pypsa
uv add pypsa
```

For a local checkout used by a maintainer, an editable install is useful:

```bash
python -m pip install -e .
```

A normal user workflow does not need an editable install.

## Minimal runtime check

After installation:

```bash
python - <<'PY'
import pypsa
n = pypsa.Network()
n.add("Carrier", "AC")
n.add("Bus", "bus", carrier="AC")
print(pypsa.__version__, len(n.buses))
PY
```

For a fuller check, run the bundled helper from this skill:

```bash
python scripts/check_pypsa_environment.py --optional
python scripts/pypsa_quickstart_smoke.py --solve
```

Run these commands from this skill directory or provide the path to the script.

## Default solver path

PyPSA uses Linopy for optimization. The base package includes the open-source HiGHS Python interface (`highspy`), and the default solver name is `"highs"`.

Baseline solve pattern:

```python
status, condition = n.optimize(
    solver_name="highs",
    log_to_console=False,
    include_objective_constant=False,
)
```

Set `include_objective_constant` explicitly to avoid version-dependent FutureWarnings and to document numerical intent.

## Optional solver backends

PyPSA can use additional solvers through Linopy, including GLPK, CBC, SCIP, Gurobi, CPLEX, FICO Xpress, MOSEK, and COPT when the corresponding solver binaries/APIs are installed and licensed.

Guidance:

- Use HiGHS first for small and medium open-source checks.
- Use commercial solvers for large MILPs, unit commitment, or difficult planning problems when licensed.
- Gurobi IIS infeasibility tracing requires the Gurobi Python API and a valid license.
- Missing optional solvers are not PyPSA import failures; they are solver-selection failures.

## Optional extras by feature

| Feature | Install | Before using |
|---|---|---|
| HDF5 I/O | `pip install "pypsa[hdf5]"` | Verify `import tables`. |
| Excel I/O | `pip install "pypsa[excel]"` | Verify `import openpyxl` and `import python_calamine`. |
| Cloud object storage | `pip install "pypsa[cloudpath]"` plus provider clients | Verify credentials and provider SDKs separately. |
| Cartopy maps | `pip install "pypsa[cartopy]"` | Verify `import cartopy`; use `geomap=False` as a fallback. |
| Gurobi API | `pip install "pypsa[gurobipy]"` | Verify license and `import gurobipy`. |
| `.env` options | `pip install "pypsa[dotenv]"` | Confirm `.env` priority and reproducibility risks. |
| Spatial clustering algorithms | `pip install scikit-learn` | Needed for k-means/HAC busmaps. |
| Temporal segmentation | `pip install tsam` | Needed for `n.cluster.temporal.segment(...)`. |
| External converters | `pip install pandapower pypower` as needed | Converters are partial and optional. |

Do not install all extras by default for ordinary modeling or optimization. Start with base + feature-specific extras.

## Options and environment variables

PyPSA options can be set in code:

```python
import pypsa

pypsa.options.params.optimize.solver_name = "gurobi"
with pypsa.option_context("params.optimize.solver_name", "highs"):
    n.optimize()
```

They can also be set through environment variables using `PYPSA_` and double underscores:

| Option path | Environment variable |
|---|---|
| `general.allow_network_requests` | `PYPSA_GENERAL__ALLOW_NETWORK_REQUESTS` |
| `params.optimize.solver_name` | `PYPSA_PARAMS__OPTIMIZE__SOLVER_NAME` |
| `params.statistics.round` | `PYPSA_PARAMS__STATISTICS__ROUND` |

Priority from low to high is default values, `.env` file if `python-dotenv` is installed, environment variables, runtime option assignment, and function arguments.

## Offline and network-limited environments

PyPSA's core modeling and solving tasks do not require network access. Example network helper functions may download data on cache miss unless network requests are disabled.

For restricted environments:

```python
pypsa.options.general.allow_network_requests = False
```

Then load local network files directly or build tiny networks in code.

## Headless plotting

For static plots on servers or CI, set an off-screen Matplotlib backend before plotting:

```python
import matplotlib
matplotlib.use("Agg", force=True)
```

The analysis sub-skill's smoke helper demonstrates headless statistics and map plotting without Cartopy.
