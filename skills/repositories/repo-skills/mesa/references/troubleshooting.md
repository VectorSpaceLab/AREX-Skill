# Mesa Troubleshooting

## When to read

Read this for cross-cutting Mesa install/version/extras issues before drilling into a sub-skill-specific troubleshooting guide.

## Version and import mismatches

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'mesa'` | Mesa is not installed in the active Python environment. | Install with `python -m pip install -U mesa`, then run `scripts/check_mesa_install.py`. |
| A workflow mentions `mesa.discrete_space` or Mesa 4 scheduling but imports fail or behavior looks older | The installed package is an older stable release while the task expects Mesa 4/pre-release APIs. | Check `mesa.__version__`; if appropriate for the task, install a Mesa pre-release with `python -m pip install -U --pre mesa`. |
| Import succeeds from one shell/notebook but fails in another | Different Python kernels/environments. | Run `python -c "import sys, mesa; print(sys.executable, mesa.__version__)"` in the same environment that will run the model. |
| Type annotations with bracketed generic classes fail on old Python | Mesa snapshot requires Python 3.12+. | Use Python 3.12 or newer. |

## Optional extras

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Network` layout fails because `networkx` is missing | Network space default layout needs NetworkX unless a layout is supplied. | Install `mesa[network]` or `mesa[rec]`, or pass an explicit layout mapping/callable. |
| `SolaraViz`, component builders, or visualization imports fail | Visualization optional dependencies are absent. | Install `mesa[viz]` or `mesa[rec]`; then run `sub-skills/visualization/scripts/check_visualization_stack.py --require-viz`. |
| Headless unit checks pass but a browser dashboard still fails | Browser/frontend runtime issue rather than core Mesa import issue. | First validate component imports and model constructor parameters; only then run browser/server checks in the user's project if they authorize it. |
| Parquet or SQL experimental recorders fail | Optional storage dependencies or filesystem/database permissions are missing. | Use in-memory/JSON recorders for small checks, or install the required storage dependency and validate the target path/service explicitly. |

## Workflow routing mistakes

| Task or error | Read next |
| --- | --- |
| `AttributeError` about assigning `model.agents`, unhashable agents, event in the past, activation order, or sequence indexing | [model-core troubleshooting](../sub-skills/model-core/references/troubleshooting.md) |
| Property layer shape/name errors, `CellFullException`, no empty cells, `HexGrid` torus dimensions, missing NetworkX, continuous-space bounds | [spaces troubleshooting](../sub-skills/spaces/references/troubleshooting.md) |
| DataCollector reporter validation, missing table columns, lambda pickling, scenario failure origins, action ownership/current action errors | [analysis-experiments troubleshooting](../sub-skills/analysis-experiments/references/troubleshooting.md) |
| `SolaraViz` constructor/model parameter mismatch, missing visualization extras, portrayal/style errors, empty plots | [visualization troubleshooting](../sub-skills/visualization/references/troubleshooting.md) |

## Safe first checks

Run these in the target runtime before debugging model logic:

```bash
python scripts/check_mesa_install.py --require-core
python scripts/check_mesa_install.py --require-network
python scripts/check_mesa_install.py --require-viz
```

Then run the nearest sub-skill smoke script for the failing surface.

## Stop conditions

Stop and ask for more context when the task depends on:

- A specific Mesa release different from the snapshot in `repo-provenance.md`.
- Browser automation, hosted services, or large example runs.
- A user's private model package, data files, images, or notebook state.
- Benchmark-scale runtime/performance claims.
