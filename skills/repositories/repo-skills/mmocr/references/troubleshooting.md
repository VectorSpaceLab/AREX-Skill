# MMOCR cross-cutting troubleshooting

Use this reference for install/import/runtime failures before routing to a focused sub-skill.

## Install and import failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: mmcv`, `mmengine`, or `mmdet` | OpenMMLab dependencies were not installed | Install through OpenMIM or a wheel set compatible with the Python/PyTorch backend. |
| `mmcv` import fails with missing ops or ABI errors | MMCV wheel does not match PyTorch/CUDA/Python ABI | Reinstall a matching MMCV wheel for the current PyTorch and backend; do not mix CPU and CUDA wheels accidentally. |
| NumPy/OpenCV/scikit-image errors after install | Version conflict in image/scientific stack | Run `pip check`, then pin compatible runtime dependencies rather than installing broad dev requirements. |
| `mmocr.apis` import fails | Missing core dependencies or incompatible OpenMMLab versions | Run `scripts/check_mmocr_environment.py`; inspect versions of `mmcv`, `mmengine`, `mmdet`, `torch`, and `mmocr`. |

## Backend and device failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| CUDA expected but `torch.cuda.is_available()` is false | CPU-only torch/MMCV build, container GPU passthrough missing, or driver mismatch | Verify torch CUDA version, driver, and MMCV wheel before running GPU workflows. |
| CPU run works but GPU run crashes | Operator/backend wheel mismatch or unsupported family/operator | Use CPU for config/API debugging; only claim GPU verification after a real CUDA smoke and native case pass. |
| Distributed run hangs or fails | Wrong GPU count, port conflict, NCCL/runtime issue | Choose a unique port, match visible devices, and verify the distributed backend before launching. |
| Slurm command fails | Not in a valid allocation or site-specific wrapper/partition mismatch | Ask for cluster policy, partition, allocation, and allowed submission shape. |

## Network, data, and checkpoint failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Pretrained alias triggers unexpected download | Alias has model-zoo weights but no local checkpoint was provided | Ask before using network/cache; prefer explicit local checkpoint paths for deterministic work. |
| Dataset preparation wants to download large archives | Dataset preparer owns download/extraction/config generation | Route to `data-preparation`; inspect metadata first and ask before network/storage-heavy actions. |
| Checkpoint/config mismatch | Family, dictionary, task, or class count differs | Use `training-evaluation-configs` model-zoo compatibility checks. |
| Annotation/data loader mismatch | Dataset config does not match actual storage or annotation schema | Use `data-preparation` preflight and troubleshooting. |

## Headless visualization and outputs

| Symptom | Likely cause | Recovery |
|---|---|---|
| `show=True` opens no window on a server | No GUI/display | Save visualizations to output directories instead of opening a window. |
| Prediction JSON and visualization files are confused | Inference and evaluation use separate output routes | In inference, distinguish prediction dumps from visualization outputs; in evaluation, use explicit work/output directories. |
| Font/rendering issues in visualizers | Missing fonts or headless rendering constraints | Save outputs, choose available fonts if exposed by the caller's visualizer config, and avoid GUI-only checks. |

## Route-specific next steps

- Inference API/CLI, saved predictions, model aliases, KIE chain issues: [`../sub-skills/ocr-inference/SKILL.md`](../sub-skills/ocr-inference/SKILL.md).
- Config, train/test/eval, model family, checkpoint/work_dir, AMP/distributed: [`../sub-skills/training-evaluation-configs/SKILL.md`](../sub-skills/training-evaluation-configs/SKILL.md).
- Dataset formats, dataset preparer, LMDB, annotation validation: [`../sub-skills/data-preparation/SKILL.md`](../sub-skills/data-preparation/SKILL.md).
- Registries, DataSamples, transforms, metrics, visualizers, project extensions: [`../sub-skills/model-api-components/SKILL.md`](../sub-skills/model-api-components/SKILL.md).

## Stop conditions

Stop and ask before:

- Installing or replacing CUDA/ROCm/vendor backend stacks.
- Downloading large checkpoints or datasets.
- Running long training/evaluation jobs.
- Submitting Slurm or multi-node jobs.
- Mutating user-provided environments or shared datasets.
