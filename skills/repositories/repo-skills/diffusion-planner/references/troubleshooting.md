# Cross-cutting troubleshooting

Read this before changing dependencies, launching workers, or interpreting a
late traceback. Fix the first failed contract and record the observed command
and environment facts.

## Install and import

- **`ModuleNotFoundError` for `torch`, `timm`, `mmengine`, `wandb`, or nuPlan**:
  install only the requirements for the selected workflow, then rerun the
  environment probe. The repository's CUDA requirements are version-sensitive;
  do not repair a CUDA workflow with an arbitrary CPU wheel.
- **NumPy ABI warning or compiled-extension import failure**: keep NumPy
  compatible with the pinned PyTorch/nuPlan stack (the verified baseline used
  NumPy 1.23.4). Re-run `pip check` and the probe after changing it; do not
  treat a successful metadata query as import success.
- **`shapely`, `geopandas`, `rasterio`, `rtree`, or map import failure**: these
  are nuPlan map/data dependencies. Repair the environment before running
  `data_process.py` or scenario simulation; model-only tensor checks can stay
  separate from map verification.
- **Import succeeds only from a checkout**: verify editable-install/source
  precedence and run from a neutral directory. Do not publish a skill that
  relies on an uninstalled local path.

## Backend and resources

- **CUDA unavailable or `invalid device ordinal`**: query visible devices,
  match `CUDA_VISIBLE_DEVICES` to the process count, and run a one-device probe.
  CPU parser checks are not evidence for CUDA training or simulation.
- **NCCL hang, address in use, or stale ranks**: stop only the failed run's
  workers, clear stale rank variables, choose a free single-node port, and
  retry with a matching process/device count. See the model-training DDP route.
- **CUDA library such as `libnvrtc.so` or cuDNN missing**: distinguish a
  framework import pass from a device-kernel pass. Repair the runtime/library
  path or record the CUDA smoke as blocked; do not claim full backend coverage.
- **Out-of-memory or long-running worker startup**: stop before broadening
  resources. Reduce the bounded smoke or selected data, not the declared model
  contract, and preserve the original failure.

## Data, config, and artifacts

- **Missing manifest entry, `.npz` key, shape, or normalization statistic**:
  run the data-preparation validator and then the model-training contract
  checker. Regenerate the producer output rather than silently zero-filling a
  required feature.
- **`args.json`/checkpoint mismatch**: compare architecture dimensions,
  `future_len`, neighbor count, diffusion type, and normalizer contents before
  loading. A bare state dict or missing EMA may be a warm start, not a faithful
  resume.
- **Hydra cannot resolve planner/config/filter**: verify package installation,
  `hydra.searchpath`, planner target, and the scenario-builder/filter pairing.
  Validate a configuration without starting Ray where possible.
- **Empty or malformed simulation output**: verify experiment-root write
  permissions, selected split, checkpoint loading, and scenario count before
  opening NuBoard. Visualization cannot repair a failed simulation.

## External prerequisites and safety

Full preprocessing and closed-loop/guided simulation require a separately
prepared nuPlan dataset, map database, experiment root, compatible devkit, and
usually a checkpoint. Their absence is an explicit blocked prerequisite, not a
package smoke failure. Checkpoint acquisition may require network access and
should be performed only when the user approves the source and storage.

Do not use `sudo`, private interpreter paths, unreviewed shell templates, or
large downloads as a diagnostic shortcut. Use the active environment and the
smallest safe helper first. If a required backend or external artifact remains
unavailable, leave the verification handoff blocked and state the exact next
input needed.
