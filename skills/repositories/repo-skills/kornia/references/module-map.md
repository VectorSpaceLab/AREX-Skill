# Kornia module map

| Module family | Use for | Runtime route |
| --- | --- | --- |
| `kornia.io`, `kornia.image`, `kornia.color`, `kornia.filters`, `kornia.enhance`, `kornia.morphology` | File I/O, tensor conversion, color spaces, deterministic filters, enhancement, morphology, drawing. | `sub-skills/image-processing/SKILL.md` |
| `kornia.augmentation` | Random/deterministic augmentation modules, `AugmentationSequential`, `ImageSequential`, video/patch containers, synchronized targets. | `sub-skills/augmentation-pipelines/SKILL.md` |
| `kornia.geometry`, `kornia.tracking` | Resize/warp/crop, homography, camera projection, calibration, epipolar/pose, depth, point cloud, Lie groups, planar tracking. | `sub-skills/geometry-vision/SKILL.md` |
| `kornia.losses`, `kornia.metrics` | Differentiable objectives and evaluation metrics for image quality, segmentation, depth, disparity, pose, and classification. | `sub-skills/losses-and-metrics/SKILL.md` |
| `kornia.feature` | Local feature detectors/descriptors, LAFs, learned feature extractors, descriptor matching, LoFTR/LightGlue. | `sub-skills/features-and-matching/SKILL.md` |
| `kornia.models`, `kornia.contrib`, `kornia.onnx`, `kornia.transpiler` | Model builders, application wrappers, output conversion, ONNX chains, optional multi-framework transpilation. | `sub-skills/models-and-deployment/SKILL.md` |
| `kornia.core`, `kornia.config`, `kornia.constants` | Shared tensor wrappers, checks, base modules, constants and compatibility helpers. | Root plus nearest owning sub-skill. |

## Import-order note

Kornia imports `filters` and `geometry` before other top-level modules to avoid circular import problems. When modifying Kornia source, preserve this top-level import ordering unless you have a verified alternative.

## Cross-route examples

- Load and filter an image, then run augmentation: start with image-processing, then augmentation-pipelines.
- Match local features, then estimate a homography: start with features-and-matching, then geometry-vision.
- Train with Kornia losses on augmented tensors: augmentation-pipelines plus losses-and-metrics.
- Export a vision preprocessing/model chain: image-processing or augmentation-pipelines for preprocessing, then models-and-deployment for export limitations.
