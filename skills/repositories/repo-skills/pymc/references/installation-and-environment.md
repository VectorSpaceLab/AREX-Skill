# PyMC installation and environment reference

Read this when a task begins with installing PyMC, checking optional backends, or deciding which optional sampler/storage packages are needed.

## Base install

PyMC supports Python 3.12 and newer in this source snapshot.

```bash
python -m pip install pymc
python -c "import pymc as pm; print(pm.__version__)"
```

For local editable package development, install from a PyMC checkout with:

```bash
python -m pip install -e .
```

Minimal import check:

```bash
python - <<'PY'
import pymc as pm
import pytensor
print("pymc", pm.__version__)
print("pytensor", pytensor.__version__)
PY
```

Run the bundled environment checker when you need a safer package-level smoke:

```bash
python scripts/check_pymc_env.py --run-smoke
```

## Optional integrations

| Need | Package(s) | Notes |
| --- | --- | --- |
| Fast Rust NUTS and current PyMC auto-selection when compatible | `python -m pip install "pymc[nutpie]"` or `python -m pip install nutpie` | PyMC 6.3.0 requires `nutpie>=0.16.10`. Pin `nuts_sampler="pymc"` when callbacks/custom traces are needed. |
| NumPyro NUTS through JAX | `python -m pip install numpyro jax jaxlib` | CPU JAX is enough for portable package checks; GPU JAX requires a compatible CUDA/JAX stack. |
| BlackJAX NUTS through JAX | `python -m pip install "blackjax>=1.5,<1.6" jax jaxlib` | Version cap mirrors this source snapshot. |
| Zarr trace storage | `python -m pip install zarr` | Optional persistent/chunked trace path. |
| `mcbackend` trace integration | `python -m pip install mcbackend` | Optional and not required for ordinary inference. |
| Graphviz visualization | Python `graphviz` package plus Graphviz system binaries | Optional; textual model registries are the fallback. |
| ODE examples/tests that pull plotting indirectly | `python -m pip install matplotlib` | Not needed for ordinary PyMC modeling, but some test/progress paths import it. |

## Conda notes

Conda is useful when users need compiled scientific dependencies, BLAS control, or Graphviz/system packages:

```bash
conda create -c conda-forge -n pymc-env "pymc>=6"
conda activate pymc-env
conda install -c conda-forge nutpie
```

Prefer a fresh environment and avoid broad dev/docs/benchmark dependencies unless the user is maintaining the repository.

## Backend policy for this skill

The selected PyMC skill scope is CPU-required and GPU-optional. Core modeling, logp, MCMC, predictive sampling, GP, ODE, VI, DataTree/backends, and optional CPU JAX sampler guidance can be verified with CPU execution. CUDA/JAX GPU support is required only when a user explicitly asks for GPU JAX or a GPU-specific route. Do not claim GPU verification from a CPU-only JAX install.

## Bundled validation commands

```bash
python scripts/check_pymc_env.py --run-smoke --json
python scripts/pymc_quick_smoke.py --draws 10 --tune 10 --json
python sub-skills/inference-predictive/scripts/inference_smoke.py --draws 5 --tune 5 --json
```

Tiny draw counts validate API wiring and output shapes only. Increase draws, tune, chains, and diagnostics for real inference quality.
