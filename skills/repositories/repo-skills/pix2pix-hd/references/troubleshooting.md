# pix2pixHD Troubleshooting

## Purpose

Read this when a pix2pixHD workflow fails before you know which sub-skill owns the problem.

## Cross-cutting failure map

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Imports for `torch`, `torchvision`, `dominate`, or `scikit-learn` fail | The environment is missing a required runtime dependency. | Install the dependency in the private inspection or user environment, then rerun the shared smoke check. |
| The repo cannot be imported from the helper scripts | The checkout was not exposed through `--repo-root` or a temporary path entry. | Re-run the helper with an explicit `--repo-root` so it can add the checkout to `sys.path`. |
| Training or inference complains about missing CUDA | The published workflows are CUDA-first and call `.cuda()` in multiple places. | Use a CUDA-capable torch stack on a GPU host. CPU-only execution is only suitable for setup and smoke checks. |
| `AttributeError: module 'fractions' has no attribute 'gcd'` | `train.py` still uses `fractions.gcd()` in `lcm()`, which is gone on Python 3.13+. | Use a compatible interpreter or patch the helper to `math.gcd`. |
| `AttributeError: module 'torchvision.transforms' has no attribute 'Scale'` | The legacy `resize_and_crop` branch still depends on a removed torchvision API. | Prefer `scale_width`, `scale_width_and_crop`, `crop`, or `none`, or patch `data/base_dataset.py` to `torchvision.transforms.Resize`. |
| VGG downloads during the first training run | `VGGLoss` instantiates `torchvision.models.vgg19(pretrained=True)`. | Use `--no_vgg_loss` for smoke tests or allow the download when you want the full loss term. |
| FP16 recipes fail immediately | The checked-in FP16 path expects NVIDIA Apex. | Install Apex or drop `--fp16` and run the full-precision recipe. |
| Multi-GPU training behaves unexpectedly | The repo uses `DataParallel` and the README warns the multi-GPU path was not fully tested. | Stick to the published `batchSize` and `gpu_ids` recipe first; keep `pool_size=0` for multi-GPU runs. |
| A checkpoint, cluster cache, or HTML page is not where you expect | The experiment name, epoch, or output root was changed. | Check `checkpoints/<name>/`, `results/<name>/<phase>_<epoch>/`, and the sub-skill helper for the exact path mapping. |
| TensorRT or pycuda imports fail | The optional accelerated path is not installed. | Treat the vendor path as unavailable and fall back to standard PyTorch inference. |

## Where to look next

- Dataset / parser issues: [setup-and-data](../sub-skills/setup-and-data/SKILL.md)
- Training recipes and memory planning: [training](../sub-skills/training/SKILL.md)
- Inference checkpoints and HTML output: [inference](../sub-skills/inference/SKILL.md)
- Feature caches and clustering: [instance-features](../sub-skills/instance-features/SKILL.md)

## Recovery order

1. Confirm the workflow and sub-skill.
2. Check the output path recipe.
3. Check the backend requirement and missing dependency.
4. Only then look at deeper model behavior.
