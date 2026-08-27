# Cross-Cutting Troubleshooting

## Purpose

Read this first when the problem is not clearly limited to datasets,
training/pipelines, or visualization. If the issue is clearly scoped, jump to
the relevant sub-skill troubleshooting page.

## Common failure families

### Install or import failures

- `open3d.ml` cannot be imported.
- `open3d.ml.torch` reports a version mismatch.
- NumPy or compiled extensions disagree on ABI compatibility.
- TensorFlow or CUDA is unavailable in the current build.

Use `install-and-inspect` for recovery.

### Dataset or layout failures

- Empty splits.
- Wrong `dataset_path`.
- Malformed `.npy` files.
- Label column mismatches.

Use `datasets-and-preprocessing` for recovery.

### Config or model-selection failures

- Registry lookup misses.
- Config path errors.
- CLI override precedence confusion.
- Checkpoint or model-name mismatches.

Use `training-and-pipelines` for recovery.

### Visualization or extension failures

- GUI/headless issues.
- Label LUT mismatches.
- TensorBoard schema mistakes.
- OpenVINO model/backend limitations.

Use `visualization-and-extensions` for recovery.

## Generic recovery steps

1. Confirm the exact task family and route to the owning sub-skill.
2. Run the bundled helper for that sub-skill when it exists.
3. Check the backend or optional dependency notes before mutating the
   environment.
4. Prefer a small fixture or smoke check over a full training or download step.

## When to stop

Stop and reassess if the task requires:

- a GPU/backend that is not available
- a large external dataset or checkpoint download
- a source build or environment mutation that may break a shared install
