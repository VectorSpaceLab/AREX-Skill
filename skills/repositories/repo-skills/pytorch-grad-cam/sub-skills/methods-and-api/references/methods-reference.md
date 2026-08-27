# Method Catalog and Selection Guidance

## High-level method families

| Method | Best for | Notes |
| --- | --- | --- |
| `GradCAM` | default balanced CAM for CNNs | good starting point |
| `HiResCAM` | faithful CNN explanations | elementwise gradient × activation |
| `GradCAMPlusPlus` | multi-gradient CAM refinement | often strong default for image tasks |
| `ScoreCAM` | gradient-free saliency | slower because it uses many forward passes |
| `AblationCAM` | ablation-based importance | also slower; set batch size deliberately |
| `XGradCAM` | normalized gradient weighting | close to GradCAM with a different weight rule |
| `LayerCAM` | lower-layer spatial detail | emphasizes positive gradients spatially |
| `EigenCAM` | class-agnostic structure | no class discrimination; good for coarse attention |
| `EigenGradCAM` | class-aware EigenCAM variant | uses activation-gradient product before projection |
| `FullGrad` | gradient from biases and activations | broader attribution signal |
| `GradCAMElementWise` | elementwise gradient weighting | keeps more local detail |
| `KPCA_CAM` | nonlinear component projection | exposes `kernel` and `gamma` options |
| `ShapleyCAM` | Shapley-style importance | gradient + Hessian-vector product style behavior |
| `FinerCAM` | fine-grained class comparison | uses similarity-based comparison categories |
| `SegEigenCAM` | semantic segmentation attribution | gradient weighting + sign-corrected eigen projection |
| `RefineCAM` | multi-layer refinement | evaluate in `metrics-and-evaluation` |

## Choosing a method

- Need a simple default: start with `GradCAM` or `GradCAMPlusPlus`.
- Need more localization fidelity: try `HiResCAM` or `LayerCAM`.
- Need transformer compatibility with reshape transforms: `GradCAM`,
  `GradCAMPlusPlus`, or `LayerCAM` plus a good `reshape_transform`.
- Need class-agnostic structure: `EigenCAM` or `SegEigenCAM`.
- Need comparison between similar classes: `FinerCAM`.
- Need slower but stronger perturbation-style evidence: `ScoreCAM` or
  `AblationCAM`.
- Need method catalogs for advanced explainability research: combine this guide
  with `metrics-and-evaluation`.

## `cam.py`-style method keys

The package's example-style method keys are lower-case strings such as
`gradcam`, `scorecam`, `ablationcam`, `eigencam`, `eigengradcam`, `layercam`,
`fullgrad`, `gradcamelementwise`, `kpcacam`, `shapleycam`, `finercam`, and
`segeigencam`. Keep those keys consistent when building your own CLI or helper.
