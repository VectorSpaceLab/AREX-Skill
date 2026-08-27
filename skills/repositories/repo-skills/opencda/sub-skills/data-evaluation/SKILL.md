---
name: data-evaluation
description: "Use OpenCDA's dumped YAML vehicle records for offline trajectory
  augmentation, evaluation-output interpretation, plotting, and non-destructive
  debugging."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Data evaluation

Route offline work on OpenCDA data dumps, trajectory labels, evaluation outputs,
and debug plots here. This sub-skill is applicable when the input is a directory
of frame YAML files; it does not start a simulator or alter the source tree.

- Read [data-formats.md](references/data-formats.md) before interpreting vehicle
  records, trajectory tuples, or observation/prediction horizons.
- Read [evaluation-and-plotting.md](references/evaluation-and-plotting.md) for
  the evaluation lifecycle and saved debug artifacts.
- Read [troubleshooting.md](references/troubleshooting.md) when keys, horizons,
  output paths, or plotting backends fail.
- For safe augmentation, run
  [`scripts/generate_prediction_yaml.py`](scripts/generate_prediction_yaml.py)
  with explicit `--input-root` and `--output-root`. It writes YAML only to a
  separate output tree by default; use `--in-place` only when source mutation is
  explicitly approved.

## Boundaries and external limits

This skill covers deterministic, offline post-processing and inspection. It
requires Python with PyYAML for the bundled helper and optionally matplotlib
for plots. `EvaluationManager` also imports CARLA and consumes live/in-memory
vehicle-manager state; a CARLA 0.9.12 client import was checked, but no CARLA
server was verified. SUMO, ScenarioRunner, torch, and YOLOv5 runtimes are not
part of the verified environment. Do not infer a successful simulator,
co-simulation, detector, or model evaluation from an offline YAML check.
