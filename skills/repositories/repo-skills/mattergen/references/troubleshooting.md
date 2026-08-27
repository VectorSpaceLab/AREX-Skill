# Cross-cutting troubleshooting

Read this before retrying an installation, asset acquisition, or workflow that failed.

## Import and dependency failures

- **`ModuleNotFoundError` for `torch_scatter`, `torch_sparse`, or `torch_cluster`:** the PyG extension wheel does not match the installed torch/Python/CUDA ABI. Recreate or repair an isolated environment using the repository's documented torch family and matching PyG wheel index; do not hide the error by switching to CPU for a CUDA-required workflow.
- **NumPy ABI errors or warnings:** MatterGen pins NumPy below 2.0. Check `python -m pip check` and the actual torch/PyG versions before rerunning.
- **`pkg_resources` deprecation or Hydra `_self_` warnings:** these are warnings observed during the verified help probes, not proof of workflow failure. Record them, but investigate any nonzero exit separately.
- **Package imports but console command is missing:** inspect package installation metadata and run `python -m pip show mattergen`; reinstall the distribution in the intended environment without mutating a shared/base environment.

## Backend and resource failures

- **CUDA is unavailable:** run `python -c "import torch; print(torch.cuda.is_available(), torch.version.cuda)"`. If the selected task is import/config/data-only, use CPU explicitly. If it is full generation or MatterSim relaxation, stop and report the missing required backend instead of claiming success.
- **CUDA out of memory at a trivial operation or model load:** the device may be occupied by another process. Inspect the scheduler/device allocation, select a free visible device, or lower the workload. Do not repeatedly launch into a full device or infer model quality from a failed load.
- **Apple Silicon fallback errors:** set `PYTORCH_ENABLE_MPS_FALLBACK=1` and use the training route's MPS strategy override. MPS remains experimental and is not equivalent to the verified Linux CUDA path.
- **CPU run is unexpectedly slow:** generation and relaxation are GPU-oriented. Use CPU for preflight and lightweight tests only, or obtain the required CUDA resources.

## Checkpoint, data, and reference assets

- **Git-LFS pointer passed as a model/archive:** inspect the file contents and size; hydrate the exact requested asset with explicit approval, or use a named Hub model. The skill never auto-downloads.
- **Local checkpoint missing `config.yaml` or `.ckpt`:** stop before constructing `MatterGenCheckpointInfo`; choose a complete model directory and verify `best`/`last`/epoch selection.
- **Reference/correction mismatch:** MP2020 and TRI2024 reference datasets must be paired with their corresponding correction scheme. A metric change after switching schemes is expected and is not a direct regression.
- **MatterSim vs DFT discrepancy:** MatterSim is an ML force field used for fast evaluation, not a replacement for a final DFT claim. Preserve the potential version and confirm important results independently.

## CLI, configuration, and output failures

- **Fire mapping parse error:** quote the complete mapping and avoid whitespace around key/value separators. Use the generation validator before `--run`.
- **Hydra override mismatch:** property names must appear both in `data_module.properties` and the matching adapter property-embedding overrides. Run the no-launch Hydra validator and inspect every warning/error.
- **Missing data split/property config:** validate CSV schema and cache arrays before training. A syntactically valid property column that is not registered/configured will not become a trainable condition.
- **Evaluation energy count mismatch:** structure loading order is part of the contract. For `relax=False`, provide one finite total energy per loaded structure in exactly that order.
- **Partial outputs after interruption:** preserve the run directory, inspect resolved config and artifact counts, and retry into a fresh directory after correcting the cause. Do not overwrite evidence or treat partial metrics as complete.

## External systems and stop conditions

Network, Hub, Git LFS, W&B credentials, large archives, GPU scheduling, and
MatterSim potential downloads are explicit external boundaries. Ask for or
confirm authorization and resources before crossing them. If a required
backend/asset remains unavailable, keep the task blocked and state the exact
missing item, rather than silently narrowing the scientific claim.
