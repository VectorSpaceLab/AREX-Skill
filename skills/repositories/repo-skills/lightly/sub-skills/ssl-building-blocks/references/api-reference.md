# API Reference

This sub-skill stays below full training and focuses on component assembly.
When a choice is ambiguous, prefer the smallest synthetic check that proves the interface is wired correctly.

## Public install and import surface

- Install: `pip install lightly`
- Core imports: `lightly.data`, `lightly.transforms`, `lightly.loss`, `lightly.models.modules`
- Optional branches:
  - TIMM-backed modules appear only when `lightly.utils.dependency.timm_vit_available()` is true.
  - Video-folder support appears only when `lightly[video]` and its video backend are installed.
- Compatibility note: `lightly.models.SimCLR`, `BYOL`, `MoCo`, `NNCLR`, `SimSiam`, and `BarlowTwins` are legacy convenience wrappers. Prefer the low-level pieces below for new assembly.

## Data ingress

| API | Verified signature / contract | Usage notes |
|---|---|---|
| `LightlyDataset` | `LightlyDataset(input_dir: Optional[str], transform=None, index_to_filename=None, filenames=None, tqdm_args=None, num_workers_video_frame_counting=0)` | Returns `(sample, target, fname)`. Auto-detects image folders, ImageNet-style subfolders, and video folders. `input_dir=None` is only for wrapping an existing torch dataset. |
| `LightlyDataset.from_torch_dataset` | `from_torch_dataset(dataset, transform=None, index_to_filename=None)` | Wraps a `torchvision`/torch dataset without downloads. |
| `LightlyDataset.get_filenames` | `get_filenames() -> List[str]` | Returns relative file names or synthetic indices for wrapped datasets. |
| `LightlyDataset.dump` | `dump(output_dir, filenames=None, format=None)` | Refuses transformed datasets; copies image folders when possible and otherwise re-saves samples. |
| `BaseCollateFunction` | `BaseCollateFunction(transform)` | Returns two augmented batches plus labels and filenames. |
| `ImageCollateFunction` / `SimCLRCollateFunction` / `MoCoCollateFunction` | `(... input_size ..., normalize=...)` | Two-view collates with SimCLR-style augmentations. |
| `MultiCropCollateFunction` | `MultiCropCollateFunction(crop_sizes, crop_counts, crop_min_scales, crop_max_scales, transforms)` | Returns a list of crops; length equals `sum(crop_counts)`. |
| `DINOCollateFunction`, `MSNCollateFunction`, `SwaVCollateFunction`, `VICRegLCollateFunction` | exported collates with multi-crop defaults | Use these when the method expects asymmetric global/local crops. |
| `IJEPAMaskCollator` | `IJEPAMaskCollator(input_size=(224, 224), patch_size=16, ...)` | Produces masks for masked-image prediction style methods. |

Lower-level helper: `lightly.data.multi_view_collate.MultiViewCollate()` stacks a precomputed list of views into batch tensors. It is useful when a transform already returns multiple views and you want a single collate step to regroup them.

Video note: if a folder contains videos but the optional video backend is missing, `LightlyDataset` raises an error instead of treating the files as images.

## Transform families

| Family | Representative signatures | Output contract | Typical use |
|---|---|---|---|
| Two-view defaults | `SimCLRTransform`, `BYOLTransform`, `SimSiamTransform`, `MoCoV1Transform`, `MoCoV2Transform`, `VICRegTransform`, `TiCoTransform` | Two augmented views | Contrastive and cosine-similarity methods that need paired crops. |
| Multi-view / multi-crop | `DINOTransform`, `SwaVTransform`, `MSNTransform`, `IBOTTransform` | A list of global and local views | Teacher/student or clustering methods that consume multiple crops per image. |
| Single-view / view helpers | `SimCLRViewTransform`, `BYOLView1Transform`, `BYOLView2Transform`, `DINOViewTransform`, `SwaVViewTransform`, `MSNViewTransform`, `VICRegViewTransform`, `IBOTViewTransform` | One tensor per view helper | Fine-grained checks and custom view composition. |
| Masked / reconstruction | `MAETransform`, `AIMTransform`, `FDATransform`, `CAPITransform` | Single-view or paired view transforms, depending on method | Masked-image and frequency/domain-aware methods. |
| Dense / local correspondence | `DenseCLTransform`, `DetConSTransform`, `VICRegLTransform`, `PIRLTransform`, `MMCRTransform`, `WMSETransform`, `SMoGTransform` | Local/global or grid-aware views | Methods that match patches, regions, or multiple crops. |

Supporting helpers such as `GaussianBlur`, `RandomSolarization`, `AddGridTransform`, `AmplitudeRescaleTransform`, `PhaseShiftTransform`, `IRFFT2DTransform`, `RFFT2DTransform`, `RandomFrequencyMaskTransform`, `Jigsaw`, `MultiViewTransform`, and `MultiViewTransformV2` are useful when a method needs one extra primitive rather than a full preset transform.

Rule of thumb: if a transform returns a list, check the list length before wiring the loss. Most assembly mistakes come from confusing two-view, multi-view, and single-view outputs.

## Losses

| Loss | Verified signature / contract | Typical use |
|---|---|---|
| `NTXentLoss` | `NTXentLoss(temperature=0.5, memory_bank_size=0, gather_distributed=False)` | SimCLR, MoCo, and NNCLR-style contrastive setups. |
| `NegativeCosineSimilarity` / `SymNegCosineSimilarityLoss` | `NegativeCosineSimilarity(dim=1, eps=1e-8)` and `SymNegCosineSimilarityLoss()` | BYOL, SimSiam, and TiCo-style cosine objectives. |
| `BarlowTwinsLoss` | `BarlowTwinsLoss(lambda_param=0.005, gather_distributed=False)` | Correlation-based Barlow Twins setups. |
| `VICRegLoss` | `VICRegLoss(lambda_param=25.0, mu_param=25.0, nu_param=1.0, gather_distributed=False, eps=1e-4)` | Variance/invariance/covariance regularization. |
| `DINOLoss` | `DINOLoss(output_dim=65536, warmup_teacher_temp=0.04, teacher_temp=0.04, warmup_teacher_temp_epochs=30, student_temp=0.1, center_momentum=0.9, center_mode="mean")` | Teacher/student multi-crop clustering. |
| `SwaVLoss` | `SwaVLoss(temperature=0.1, sinkhorn_iterations=3, sinkhorn_epsilon=0.05, sinkhorn_gather_distributed=False)` | SwaV multi-crop clustering. |
| `MSNLoss` | `MSNLoss(temperature=0.1, sinkhorn_iterations=3, regularization_weight=1.0, me_max_weight=None, gather_distributed=False)` | MSN clustering. |
| Specialized losses | `DCLLoss`, `DCLWLoss`, `FroSSLLoss`, `MMCRLoss`, `LeJEPALoss`, `DetConSLoss`, `DetConBLoss`, `IBOTPatchLoss`, `IBOTPlusPlusPatchLoss`, `CAPILoss`, `WMSELoss` | Use the family-specific loss that matches the method family and view layout. |

Loss guidance:
- `gather_distributed=True` only makes sense after `torch.distributed` is initialized.
- Losses that use a memory bank are easier to debug when the bank size is explicit, e.g. `(num_entries, feature_dim)`.
- Start with the default temperature and a tiny synthetic batch before changing schedules or bank sizes.

## Projection, prediction, and memory modules

| Module | Verified signature / contract | Usage notes |
|---|---|---|
| `ProjectionHead` | `ProjectionHead(blocks)` | Custom MLP builder when the preset head does not match your backbone. |
| `SimCLRProjectionHead` | `SimCLRProjectionHead(input_dim=2048, hidden_dim=2048, output_dim=128, num_layers=2, batch_norm=True)` | Good default smoke head for low-dimensional synthetic inputs. |
| `BYOLProjectionHead` / `BYOLPredictionHead` | `(... input_dim=2048, hidden_dim=4096, output_dim=256)` | BYOL and related asymmetric methods. |
| `SimSiamProjectionHead` / `SimSiamPredictionHead` | `(... input_dim=2048, hidden_dim=2048 or 512, output_dim=2048)` | SimSiam-style asymmetric heads. |
| `MoCoProjectionHead` | `MoCoProjectionHead(input_dim=2048, hidden_dim=2048, output_dim=128, num_layers=2, batch_norm=False)` | Useful for MoCo v2/v3-style configurations. |
| `NNCLRProjectionHead` / `NNCLRPredictionHead` | `(... input_dim=2048, hidden_dim=2048 or 4096, output_dim=256)` | NNCLR projection and prediction stack. |
| `DINOProjectionHead` / `DINOv2ProjectionHead` | `(... input_dim=2048, hidden_dim=2048, bottleneck_dim=256, output_dim=65536, batch_norm=False)` | Teacher/student projection heads. |
| `SwaVProjectionHead` / `SwaVPrototypes` | `(... input_dim=2048, hidden_dim=2048, output_dim=128)` and prototype heads | Clustering head plus prototype layer. |
| `DenseCLProjectionHead`, `MMCRProjectionHead`, `LeJEPAProjectionHead`, `CAPIProjectionHead` | family-specific low-level heads | Use when the method expects a nonstandard embedding width or token layout. |
| `NNMemoryBankModule` | `NNMemoryBankModule(size=65536)` | Nearest-neighbour wrapper around the generic memory bank. |
| `lightly.models.modules.memory_bank.MemoryBankModule` | `MemoryBankModule(size=65536, gather_distributed=False, feature_dim_first=True)` | Generic memory bank base class for custom losses and wrappers. |

Optional module availability:
- `MAEBackbone`, `MAEEncoder`, `MAEDecoder`, and `MaskedVisionTransformerTorchvision` require torchvision ViT support.
- `CAPIPredictorTIMM`, `AIMPredictionHead`, `IJEPAPredictorTIMM`, `MAEDecoderTIMM`, `PixioDecoderTIMM`, `MaskedCausalVisionTransformer`, `MaskedVisionTransformerDecoderTIMM`, and `MaskedVisionTransformerTIMM` appear only when TIMM ViT support is available.

Feature tensors should always be treated as `batch × feature_dim`. If the backbone output width does not match the head input width, adjust the head rather than forcing the loss to absorb the mismatch.

## Minimal assembly pattern

```python
from lightly.data import LightlyDataset
from lightly.loss import NTXentLoss
from lightly.models.modules import SimCLRProjectionHead
from lightly.transforms import SimCLRTransform

# 1. Load or synthesize a tiny batch.
# 2. Make the transform and collate arity match the method family.
# 3. Match backbone output width to the head input width.
# 4. Check that the loss is finite on synthetic tensors.
```

For quick checks, the bundled smoke script exercises the same pattern with synthetic images, a two-view collate, a projection head, a contrastive loss, and a memory bank.
