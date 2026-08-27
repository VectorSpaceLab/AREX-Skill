# Method Map

Use this when you know the method family and need the matching Lightly pieces.
For exact API shapes and signature details, see [API reference](api-reference.md).

| Method family | Recommended data / transform / collate | Heads / modules | Loss | Practical note |
|---|---|---|---|---|
| Two-view contrastive | `LightlyDataset` + `SimCLRCollateFunction` or `SimCLRTransform`; `MoCoCollateFunction` for MoCo-style batching | `SimCLRProjectionHead`, `MoCoProjectionHead`, `NNCLRProjectionHead`, `NNCLRPredictionHead`, `NNMemoryBankModule` | `NTXentLoss`, `DCLLoss`, or `DCLWLoss` | Best starting point for a synthetic smoke because the arity is always two views. |
| Asymmetric cosine | `BYOLTransform`, `SimSiamTransform`, `TiCoTransform` | `BYOLProjectionHead` / `BYOLPredictionHead`, `SimSiamProjectionHead` / `SimSiamPredictionHead` | `NegativeCosineSimilarity` or `SymNegCosineSimilarityLoss` | No memory bank; the predictor head is usually the source of shape mistakes. |
| Correlation / variance | `VICRegTransform`, `ImageCollateFunction`, or a custom two-view transform | `BarlowTwinsProjectionHead` or `ProjectionHead` | `BarlowTwinsLoss`, `VICRegLoss`, `FroSSLLoss`, or `WMSELoss` | Check finite outputs early; these methods are sensitive to width and normalization mistakes. |
| Multi-crop clustering | `DINOTransform` + `DINOCollateFunction`, `IBOTTransform`, `MSNTransform` + `MSNCollateFunction`, `SwaVTransform` + `SwaVCollateFunction` | `DINOProjectionHead`, `DINOv2ProjectionHead`, `SwaVProjectionHead`, `SwaVPrototypes`, `CAPIProjectionHead`, and optional TIMM predictor heads | `DINOLoss`, `IBOTPatchLoss`, `IBOTPlusPlusPatchLoss`, `MSNLoss`, `SwaVLoss`, `CAPILoss` | The main failure mode is arity mismatch: global views, local views, and prototypes must line up. |
| Masked / ViT-style | `MAETransform`, `IJEPAMaskCollator`, plus method-specific view helpers | `MAEBackbone`, `MAEEncoder`, `MAEDecoder`, `MaskedVisionTransformerTorchvision`, and optional TIMM ViT modules | `LeJEPALoss` for LeJEPA / I-JEPA-style setups | `lightly[timm]` and torchvision ViT support control which masked-vision modules exist. |
| Dense / local correspondence | `DenseCLTransform`, `DetConSTransform`, `VICRegLTransform`, `MMCRTransform`, `PIRLTransform`, `MultiCropCollateFunction`, `VICRegLCollateFunction`, `PIRLCollateFunction` | `DenseCLProjectionHead`, `MMCRProjectionHead`, and custom heads via `ProjectionHead` | `DetConSLoss`, `DetConBLoss`, `VICRegLLoss`, `MMCRLoss` | Local-grid and patch-level outputs are easy to mismatch; verify tensor rank and crop counts before debugging the loss. |
| Legacy wrappers | Any of the above component sets | `lightly.models.SimCLR`, `BYOL`, `MoCo`, `NNCLR`, `SimSiam`, `BarlowTwins` | Same family losses, but wrapped | Compatibility only. Prefer explicit low-level assembly for new work and for smoke scripts. |

## Quick selection rules

- If you need a fast compatibility check, start with the two-view contrastive row.
- If you need multiple crops, choose the multi-crop clustering row and check the returned list length first.
- If you need image reconstruction or masked-token behavior, use the masked / ViT-style row and guard optional dependencies.
- If you see a deprecated high-level wrapper, treat it as a migration bridge rather than the preferred API.

## Assembly heuristic

A valid Lightly component stack usually looks like this:

1. `LightlyDataset` or a tiny synthetic batch
2. A matching transform/collate family
3. A projection or prediction head whose input width matches the backbone output width
4. A loss whose view count and feature rank match the head output

When one of those steps is unclear, fall back to the smallest synthetic smoke that makes the mismatch obvious.
