# NAVSIM cross-cutting troubleshooting

Read this before retrying a data-backed, GPU, Hydra, or submission command.

## Install and import

- `ModuleNotFoundError: navsim` means the distribution is not installed in the
  interpreter running the command. Check `python -c "import navsim"` and
  `python -m pip show navsim`; do not assume the shell's active environment is
  the one used by the runner.
- `ModuleNotFoundError: nuplan` or geospatial import failures mean the complete
  documented runtime is absent. Install the package requirements in an isolated
  environment and run `python -m pip check`; do not paper over missing nuPlan
  classes with a CPU-only import.
- NumPy/Torch/compiled geospatial ABI errors usually indicate a mixed or
  upgraded environment. Recreate a clean Python 3.9-compatible environment and
  preserve the repository's major pins before changing individual packages.

## Workspace and data

- Config interpolation errors for `NUPLAN_MAPS_ROOT`, `NAVSIM_EXP_ROOT`, or
  `OPENSCENE_DATA_ROOT` mean the variable is unset or points at the wrong root.
  Run the bundled workspace validator for the exact split and distinguish
  `navsim_logs`, original `sensor_blobs`, synthetic scene pickles, and maps.
- A missing map, log, sensor, or synthetic scene directory is a real setup
  failure. Do not create an empty placeholder: loaders need files referenced by
  metadata and map APIs need a readable nuPlan database.
- A filtered split is not an independent dataset. `navtrain` uses trainval
  logs; `navtest` and public two-stage views use test logs unless a private
  config says otherwise.

## Hydra and workflow selection

- Hydra override errors often come from the group name rather than the value:
  use the exact `train_test_split`, `agent`, `worker`, `metric_cache_path`,
  `synthetic_sensor_path`, and `synthetic_scenes_path` keys shown in the route
  references. Preserve the resolved config beside experiment outputs.
- Do not use a one-stage runner with a two-stage split without consciously
  choosing the reduced comparison. Two-stage runs need matching synthetic roots
  and a cache that covers the same token universe.
- `use_cache_without_dataset=true` requires a non-null cache path and
  `force_cache_computation=false`; the training runner asserts this before
  constructing the cache-only dataset.

## Backend and cost

- `torch.cuda.is_available() == False` is a backend failure for GPU claims, not
  permission to report TransFuser training as verified. Check the Torch build,
  driver visibility, device count, and a tiny CUDA allocation.
- CPU can validate imports, config parsing, and small rule-based/API fixtures;
  it is not a substitute for full camera/LiDAR model performance or large
  metric runs when those paths are GPU/data dependent.
- Stop before downloading multi-GB data, building full metric caches, training,
  or rendering a notebook unless the user has approved the concrete resource,
  storage, and time budget.

## Output and publication

- Evaluation output with failed tokens, missing/unused cache tokens, absent
  summary rows, or invalid pseudo-closed-loop aggregation is not accepted just
  because the process exited zero.
- A local `submission.pkl` basic-schema pass does not prove server coverage,
  score parity, or challenge eligibility. Validate required metadata and stage
  containers, then stop before login/upload/private-data operations unless
  explicitly authorized.
