---
name: data-preparation
description: "Preprocess nuPlan scenarios into Diffusion Planner .npz records
  and a JSON filename manifest, and diagnose path, schema, feature-cap, and
  normalization failures. Use for nuPlan preprocessing, Diffusion Planner
  training data, scenario extraction, lane/route/agent feature preparation, or
  data schema debugging."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Diffusion Planner data preparation

Use this sub-skill when the Researcher needs to turn nuPlan scenarios into the
fixed-size records consumed by Diffusion Planner training. It covers raw
nuPlan data and map prerequisites, scenario filtering, ego/agent/static/map
feature extraction, `.npz` output, the JSON filename manifest, and
normalization compatibility. It does **not** cover distributed optimization,
checkpoint loading, closed-loop simulation, or guidance authoring.

## Fast route

1. Confirm that the active Python environment can import both the project
   package and the nuPlan devkit. A missing devkit is a hard stop; do not try to
   fabricate scenarios or replace the builder with a different data format.
2. Confirm separate readable directories for the nuPlan DB root and map root,
   and a writable processed-data directory. Use the bundled adapter's explicit
   `--log-names` and `--manifest-output` paths so the manifest is not tied to a
   working-directory convention.
3. Choose caps before processing. The training-compatible defaults are 32
   agents, 5 static objects, 70 lanes × 20 points, and 25 route lanes × 20
   points. The 2-second history and 8-second future are sampled at 10 Hz.
4. Run the safe validator in `scripts/validate_preprocessed_data.py` against a
   manifest, processed directory, and normalization file before launching a
   large extraction. It can create and validate a tiny synthetic fixture; it
   never imports nuPlan or touches raw data.
5. For real extraction, use the bundled path-explicit adapter
   `scripts/run_preprocessing.py` with `--data-path`, `--map-path`,
   `--save-path`, `--log-names`, `--manifest-output`, scenario-limit, shuffle,
   and feature-cap arguments. Start with a very small total limit, inspect one
   record and its manifest, then scale up. The source shell workflow is
   evidence only: it contains unsafe placeholders and an expensive million-
   scenario default.

See [workflow and CLI semantics](references/workflows.md),
[data formats and normalization](references/data-formats.md), and
[troubleshooting](references/troubleshooting.md). Once a valid dataset exists,
hand it to [model-training](../model-training/SKILL.md); for downstream runtime
use, see [closed-loop-planning](../closed-loop-planning/SKILL.md). The graph
entry point is [diffusion-planner](../../SKILL.md).

## Operating contract

### Inputs

- A nuPlan DB/data root and the matching map root for the same map version.
- The project preprocessing environment: Python 3.9-compatible dependencies,
  `diffusion_planner` 1.0.0, nuPlan-devkit 1.2.2, and compatible NumPy,
  Shapely, GeoPandas, Rasterio, and PyTorch installations.
- A JSON array of training log names. The standard project manifest contains
  13,180 log names; it is an input selector, not a list of processed `.npz`
  files.
- A writable output directory and a copy or path to the matching
  `normalization.json`.

### Outputs

Each successful scenario produces one `.npz` named from its map name and
scenario token. The generated JSON manifest is an array of those `.npz`
filenames. A usable output must have no missing manifest entries, no path
traversal or absolute names in the manifest, finite floating-point values, and
consistent fixed shapes. Treat an empty output directory or an empty manifest
as a failed preprocessing run, even if the process exited successfully.

### Safe boundaries

- Never start a full run until `--help`, path checks, a tiny scenario limit,
  and one-record schema validation have passed.
- Do not infer that a missing `.npz` means a valid zero-scenario result; inspect
  builder/filter logs and the manifest location.
- Do not change feature caps after generating data without regenerating or
  revalidating every record and the model/training configuration.
- Do not normalize raw global coordinates. The processor stores ego-centric
  coordinates; the training path converts future headings to cosine/sine and
  applies the normalizers at training time.
- Full preprocessing is I/O- and map-query-intensive and requires real nuPlan
  DBs/maps. A synthetic fixture proves parser and schema behavior only; it is
  not evidence of nuPlan extraction correctness.
