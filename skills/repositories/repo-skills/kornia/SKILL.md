---
name: kornia
description: "Use Kornia for differentiable computer vision, image processing,
  augmentation, geometry, features, models, losses, metrics, and deployment
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Kornia repo skill

Kornia is a PyTorch-based differentiable computer vision library. Use this root router when a task names Kornia or asks for differentiable image operators, tensor-native augmentation, geometric vision, local features, model/application builders, or vision deployment utilities.

## First checks

- Install for normal use with `pip install kornia`.
- For a source checkout, use `pip install -e .` after choosing the correct Python environment.
- Kornia requires Python 3.11+ in this snapshot and depends on PyTorch, NumPy, packaging, and `kornia-rs`.
- Minimal import check:

```bash
python -c "import kornia, torch; print(kornia.__version__, torch.__version__)"
```

- For a broader environment check, run `scripts/kornia_environment_probe.py`.
- For a cross-module tensor smoke, run `scripts/kornia_api_smoke.py --device auto`.

## Route by task

| Task signal | Read |
| --- | --- |
| Image I/O, CHW/BCHW layout, RGB/BGR/HSV/Lab/YUV, filters, Canny/Sobel, enhancement, morphology, drawing | `sub-skills/image-processing/SKILL.md` |
| Random or deterministic augmentation pipelines, masks/boxes/keypoints/classes, transform matrices, inverse, video/patch augmentation | `sub-skills/augmentation-pipelines/SKILL.md` |
| Warps, resize, affine/perspective transforms, homography, camera projection, calibration, epipolar/pose, depth, point clouds, tracking | `sub-skills/geometry-vision/SKILL.md` |
| SSIM/PSNR, Dice/Focal/Tversky/Lovasz, Hausdorff, IoU, disparity, pose, target encoding, reductions, gradient checks | `sub-skills/losses-and-metrics/SKILL.md` |
| SIFT/HardNet/DISK/DeDoDe/ALIKED/XFeat, LAFs, descriptor matching, LoFTR, LightGlue, correspondence outputs | `sub-skills/features-and-matching/SKILL.md` |
| SAM, RT-DETR, YuNet, DexiNed, ViT/MobileViT/TinyViT/EfficientViT, model configs, output saving, ONNX, Ivy transpilation | `sub-skills/models-and-deployment/SKILL.md` |

## Shared references

- `references/module-map.md` maps package modules to task families and sibling sub-skills.
- `references/environment-and-installation.md` covers install modes, optional dependency groups, backend probes, and native test commands.
- `references/troubleshooting.md` covers cross-cutting import, backend, dtype/range, optional dependency, and source-checkout failures.
- `references/compile-and-performance.md` covers Kornia's torch.compile/performance workflow and benchmark interpretation.
- `references/repo-provenance.md` records the source snapshot used to generate this skill.

## Operating defaults

1. Treat Kornia tensors as PyTorch tensors first. Most image workflows use CHW for one image and BCHW for batches.
2. Assume float image tensors are in `[0, 1]` unless an API explicitly documents another range.
3. Use CPU for correctness first; CUDA/MPS/half precision are backend-specific accelerators that need their own verification.
4. Prefer public `kornia.*` APIs over private helpers. If a task modifies Kornia source, preserve public API stability and docs/test obligations.
5. Do not trigger pretrained weight downloads, ONNX runtime sessions, or Ivy transpilation unless the user selected that workflow or supplied the required artifacts/dependencies.
6. When a task spans routes, normalize data with the first route, then hand off explicitly. Example: image I/O → augmentation → feature matching → geometry estimation.

## Quick validation habits

- Use the root smoke scripts first when you only need to know whether the installed Kornia runtime is healthy.
- Prefer the smallest sub-skill that can answer the user's question without forcing unrelated routes to load.
- Keep optional backends and pretrained paths explicit so a no-download task does not accidentally become a model-download task.
- Preserve the original tensor layout and dtype until a sub-skill says to convert it.

## If you are unsure

- Start with the narrowest route that matches the user request.
- If the request combines preprocessing and a model, do preprocessing first and then hand off to the model route.
- If the request combines correspondences and geometry, extract or normalize correspondences first and then hand off to geometry.
- If a task needs pretrained weights, say so explicitly before choosing a builder or matcher that can download.
- If a task asks for speed or compile behavior, read the performance reference before changing code.
- If a task mentions a failure, check `references/troubleshooting.md` before guessing at the fix.

## Common handoff order

1. Image-processing or augmentation prepares tensors and layout.
2. Features or models produce descriptors, detections, or predictions.
3. Geometry converts those outputs into spatial estimates or warps.
4. Losses and metrics score the outputs.
5. Deployment or ONNX converts the finalized PyTorch path when requested.

## Verification anchors

Representative native verification targets include import-warning tests, public API surface tests, focused image/augmentation/geometry/feature/loss/model-base tests, and no-download smoke scripts. Slow, network, pretrained-weight, full benchmark, ONNX-runtime, and optional backend cases should remain explicitly optional unless the user's task requires them.
