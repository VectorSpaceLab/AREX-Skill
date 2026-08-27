# Installation and Runtime Reference

Read this when a task starts with installing, importing, or sanity-checking NuPIC legacy before using OPF, Network API, swarming, or direct HTM algorithms.

## Runtime facts

- NuPIC legacy is a Python 2.7-era package. Treat Python 3 failures as expected unless the user is explicitly porting the package.
- The distribution is `nupic`; the import root is `nupic`.
- Core algorithm and Network workflows normally require the compiled `nupic.bindings` package plus NumPy in the legacy-compatible range.
- Cap'n Proto / `pycapnp` is required for some serialization paths and is also a declared dependency on Linux/Darwin-era installs.
- Swarming full runs require a MySQL-compatible service and NuPIC configuration in addition to the Python package.
- The optional visualization extra historically adds packages such as `networkx`, `matplotlib`, and `pygraphviz`; do not install it unless the task asks for visualization.

## Public install starting points

For a released package environment, start from a Python 2.7 environment and install the published package:

```bash
python -m pip install nupic
python -c "import nupic, nupic.bindings.math; print('nupic legacy import ok')"
```

For a local checkout of this repository, use the same Python 2.7-compatible environment and install from the checkout root:

```bash
python -m pip install .
python -m pip check
python -c "from nupic.algorithms.temporal_memory import TemporalMemory; print(TemporalMemory(columnDimensions=(8,), cellsPerColumn=2).numberOfCells())"
```

If a modern compiler fails while building `pycapnp`, prefer a compatible prebuilt package from the environment manager (for example, a Python-2.7 `pycapnp==0.6.3` package) over patching NuPIC source. Keep this as environment setup context; do not bake local build paths into user-facing code.

## Minimum smoke check

From the root generated skill directory, run:

```bash
python scripts/check_nupic_legacy_env.py
```

Expected success includes:

- Python version is 2.7 unless `--allow-python3` is explicitly used for a metadata-only check.
- Imports succeed for `nupic`, `numpy`, `capnp`, `nupic.bindings.math`, `nupic.algorithms.temporal_memory`, `nupic.algorithms.spatial_pooler`, `nupic.frameworks.opf.model_factory`, `nupic.engine`, and `nupic.swarming.permutations_runner`.
- Tiny API smoke constructs `TemporalMemory`, `SpatialPooler`, `ScalarEncoder`, `ModelFactory`, and an empty `Network`.

Use sub-skill-specific smokes when the package import check passes:

```bash
python sub-skills/htm-algorithms/scripts/algorithm_smoke.py --mode all --records 20
python sub-skills/network-api/scripts/network_smoke.py
python sub-skills/opf-prediction/scripts/opf_prediction_smoke.py
python sub-skills/swarming/scripts/swarm_config_lint.py sub-skills/swarming/references/swarm-search-def-template.json --summary
```

## Installation triage decision tree

1. **Wrong Python major version**: create/use a Python 2.7 environment. Do not spend time fixing Python 3 syntax errors unless the task is a port.
2. **`ImportError: No module named nupic`**: install `nupic` into the environment currently running the command; verify that shell/editor/kernel uses the same environment.
3. **`ImportError` for `nupic.bindings` or engine internals**: install the compiled `nupic.bindings` wheel/package matching Python 2.7 and platform. Pure source checkout imports are not enough for SP/TM/Network workflows.
4. **`ImportError: No module named capnp` or Cap'n Proto serialization failures**: install `pycapnp`/Cap'n Proto compatible with Python 2.7. If pip attempts to build old Cap'n Proto with a modern compiler and fails, prefer a prebuilt environment-manager package.
5. **`pip check` reports dependency conflicts**: repair the environment before running workflows; NuPIC legacy pins old dependencies and is fragile in mixed modern ML environments.
6. **Swarming DB failures**: after Python imports pass, route to the swarming troubleshooting reference for MySQL/service configuration.

## What not to include in user workflows

- Do not claim NuPIC legacy is Python 3-native.
- Do not install broad developer requirements, visualization extras, Docker/Vagrant tooling, or benchmarking/profiling dependencies for ordinary API use.
- Do not treat a pure `import nupic` as proof that compiled Network/SP/TM workflows work; run the root smoke and the relevant sub-skill smoke.
- Do not use full swarming hypersearch as an install smoke; it needs a service and can be expensive.
