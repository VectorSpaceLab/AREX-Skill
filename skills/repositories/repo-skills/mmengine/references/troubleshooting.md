# Cross-Cutting Troubleshooting

Use this reference when the failure spans multiple MMEngine layers or when the right sub-skill is unclear.

## Import and Installation

| Symptom | Likely cause | Fix path |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'mmengine'` | Package is not installed in the active Python environment. | Install `mmengine`, then run `python scripts/mmengine_import_check.py --json` from this skill directory. |
| `ModuleNotFoundError: No module named 'torch'` while using runner/model APIs | PyTorch is not installed, or the active Python is not the project environment. | Install a PyTorch build compatible with the project CPU/GPU target before using `Runner`, `BaseModel`, TTA, or analysis APIs. |
| Importing runner/hooks fails on `cv2` | Visualization hooks import OpenCV-backed utilities. | Install `opencv-python-headless` for non-GUI automation, or install the project-approved OpenCV package. |
| NumPy/PyTorch ABI warnings | A package upgraded NumPy beyond what the installed PyTorch or binary extensions expect. | Pin NumPy to a compatible version for the PyTorch/binary stack, then rerun import checks. |
| Optional backend import fails | WandB, MLflow, ClearML, Aim, DVCLive, Neptune, DeepSpeed, ColossalAI, or other optional packages are absent. | Use local/core fallbacks first; install optional packages only when the workflow explicitly needs them. |

## Config to Runtime Boundary

| Symptom | Likely layer | Next step |
| --- | --- | --- |
| Missing `type`, unregistered class, wrong scope, `custom_imports` failure | Config/registry | Read `sub-skills/configuration-and-registry/SKILL.md`. |
| Config parses but `Runner.from_cfg` complains about missing dataloader, loop, optimizer, evaluator, or hook keys | Runner config placement | Read `sub-skills/runner-and-training/SKILL.md`. |
| Dataloader builds but batches have unexpected list/tensor/data element shapes | Dataset/collate/data element | Read `sub-skills/data-structures-and-io/SKILL.md`. |
| Training starts but model returns wrong values for `loss`, `predict`, or `tensor` mode | Model contract | Read `sub-skills/models-metrics-and-inference/SKILL.md`. |
| Validation runs but checkpoint `save_best` never updates | Evaluator metric key and runner hook interaction | Read `models-metrics-and-inference` for metric keys, then `runner-and-training` for checkpoint hook rules. |
| Logs or visual outputs are missing, duplicated, or sent to the wrong backend | Runtime visualization/logging | Read `sub-skills/runtime-utilities-and-visualization/SKILL.md`. |

## Safe Debugging Order

1. Run the root import check for package/submodule availability.
2. Parse and inspect configs without building user objects.
3. Validate dataset/sample contracts with tiny records.
4. Validate model/metric contracts with tiny tensors and CPU outputs.
5. Validate runner config shape before training.
6. Add optional services, distributed launch, and GPU/large-model strategies only after the local path works.

## Optional Dependencies and Hardware

MMEngine can coordinate workflows that require GPUs, launchers, or third-party strategy/service packages, but core package importability does not prove those paths are ready. Treat these as separately verified capabilities:

- CUDA/FSDP/DeepSpeed/ColossalAI: verify hardware, PyTorch build, launcher environment, and strategy package imports.
- TensorBoard/WandB/MLflow/ClearML/Aim/DVCLive/Neptune: verify package import and credentials/service availability; prefer `LocalVisBackend` when not available.
- Remote/cloud file backends: verify the backend package, URI scheme, credentials, and read/write permissions with a tiny non-destructive file.
- Distributed helpers: outside a launched process group, most helpers should degrade to rank 0/world size 1 behavior; do not assume multi-process collection was tested.
