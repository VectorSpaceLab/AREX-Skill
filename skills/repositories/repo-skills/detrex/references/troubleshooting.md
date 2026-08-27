# detrex troubleshooting map

Start here for cross-cutting failures, then route to the owning sub-skill for workflow-specific details.

## Triage sequence

1. Run `scripts/check_environment.py --strict` for package import evidence.
2. Add `--check-config common/train.py` if config loading fails.
3. Add `--check-cuda-extension` if the model uses deformable attention or DINO/Deformable-DETR operator paths.
4. Use sub-skill command builders before running train/demo/tool workflows.
5. If checkpoint keys or model shapes fail, route to model-zoo/converters before changing code.

## Common cross-cutting issues

| Symptom | Likely cause | Route / recovery |
|---|---|---|
| `ModuleNotFoundError: detectron2` | Detectron2 is not installed in the active environment. | Install compatible Detectron2 for the PyTorch/torchvision stack; rerun environment check. |
| `ModuleNotFoundError: pkg_resources` | setuptools/pkg_resources compatibility issue with detrex config helper. | Install a setuptools build that provides `pkg_resources`; then test `from detrex.config import get_config`. |
| `ImportError: Cannot import detrex._C` | detrex extension was not built, CUDA toolkit was absent, or PyTorch/CUDA ABI mismatched. | Use environment install guidance; avoid compiled-op workflows until `--check-cuda-extension` passes. |
| DINO/Deformable-DETR fails at runtime on CPU | selected config expects CUDA/operator path or GPU-sized workflow. | Use a CPU-compatible model/config only when documented, or move to a CUDA environment. |
| CUDA extension smoke or deformable-attention gradcheck hits out-of-memory | the visible default GPU is busy or the native check allocates large Jacobians. | Select an idle GPU with `CUDA_VISIBLE_DEVICES=<index>` and rerun the small check; do not interpret OOM alone as a missing extension. |
| Config path is not found by `get_config()` | `get_config` only loads packaged resources. | Use `get_config('common/train.py')` for packaged fragments and Detectron2 `LazyConfig.load()` for user files. |
| Dataset or metadata lookup fails | Detectron2 dataset registration or dataset root is missing. | Set `DETECTRON2_DATASETS`, register the dataset, and verify metadata/class mapping. |
| Checkpoint loads with many missing/unexpected keys | checkpoint family/config/backbone/class head mismatch. | Use model-zoo/converter inspect mode before loading or converting. |
| Training command starts the wrong loop | a project-specific trainer is required. | Route to training configs and model-zoo project guide; use DINO/CO-MOT/project trainer when documented. |
| Demo labels or visualization mismatch | wrong metadata dataset or category mapping. | Register/select the matching metadata and inspect prediction JSON schema. |
| WandB starts unexpectedly | `train.wandb.enabled=True` or writer instantiated. | Disable WandB for smoke/debug runs unless explicitly requested. |

## Backend decision rule

- CPU imports are enough for API/config/tutorial work.
- CUDA extension import is required before claiming Deformable-DETR/DINO multi-scale attention readiness.
- Full COCO training/evaluation and real demos require user-provided local data/checkpoints and explicit runtime approval.

## When to ask the user

Ask for user input before installing host-level CUDA/toolchains, downloading large model/data files, running long multi-GPU jobs, using Slurm/account resources, changing datasets, or accepting a checkpoint conversion whose family cannot be inferred safely.
