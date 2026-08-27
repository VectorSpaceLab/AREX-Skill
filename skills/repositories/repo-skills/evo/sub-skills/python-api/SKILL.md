---
name: python-api
description: "Routes evo programmatic usage, notebook workflows, plotting, and
  optional Rerun/contextily integration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# python-api

Use this sub-skill when the user wants to call evo from Python, build a notebook workflow, or embed evo plotting and visualization into their own script.

## Route here when the user asks for
- custom Python code built on evo's public APIs
- notebook or IPython-friendly usage of evo
- plotting with `PlotCollection`, `plot.traj`, `plot.error_array`, or `plot.traj_colormap`
- pandas round-tripping of trajectories or results
- optional Rerun or `contextily` integration
- examples like `examples/custom_app.py` or `examples/alignment_demo.py`

## Do not route here when the task is mainly about
- CLI-only APE/RPE workflows
- trajectory-file minutiae or converters
- saved-result comparison and tables
- package settings, logfile, or shell management

## Start with
1. [references/api-reference.md](references/api-reference.md)
2. [references/workflows.md](references/workflows.md)
3. [references/rerun-and-plotting.md](references/rerun-and-plotting.md)
4. [references/troubleshooting.md](references/troubleshooting.md)
5. [scripts/programmatic_api_smoke.py](scripts/programmatic_api_smoke.py)

## Rules of thumb
- `ape` and `rpe` mutate their trajectory inputs in place, so copy any object you need to keep unchanged.
- `plot.apply_settings()` respects IPython/Jupyter and will not force a backend change inside an interactive shell.
- If you need a headless session, prefer an Agg-style backend before importing plotting code.
- `rerun-sdk` is optional and must be installed separately when you want Rerun support.
- The source examples are good recipes, but the bundled references and smoke helper are the runtime entry points future agents should use.
