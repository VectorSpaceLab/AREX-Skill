# Configuration Reference

This reference distills the verified `Config()` defaults and the knobs future agents are expected to edit.

## Verified defaults

| Field | Default | Notes |
|---|---:|---|
| `task` | `DIS5K` | Built-in task switch. |
| `testsets` | `DIS-VD` | Comma-separated testset list for the active task. |
| `training_set` | `DIS-TR` | Training split for `DIS5K`. |
| `size` | `1024 x 1024` | `General-2K` uses `2560 x 1440`. |
| `dynamic_size` | `None` | Batch-wide random size is enabled only when set. |
| `background_color_synthesis` | `False` | Training-only alpha/background synthesis. |
| `load_all` | `False` | Preloading is memory-heavy and disabled by default. |
| `auxiliary_classification` | `False` | Only intended for DIS5K-style class labels. |
| `mixed_precision` | `bf16` | Used by the training path. |
| `compile` | `True` | Torch compilation is enabled in the checked default. |
| `SDPA_enabled` | `True` | Swin attention path prefers SDPA when available. |
| `bb` | `swin_v1_l` | Default backbone choice. |
| `model` | `BiRefNet` | Only model name currently selected in `Config`. |
| `device` | `0` | GPU index form, not a device string. |
| `optimizer` | `AdamW` | Default optimizer family. |
| `batch_size` | `8` | Training batch size. |
| `batch_size_valid` | `1` | Validation batch size. |
| `num_workers` | `max(4, batch_size)` | Reduced to `min(num_workers, batch_size)` in loaders. |
| `rand_seed` | `7` | Seed helper uses this value when non-zero. |
| `lambdas_cls.ce` | `5.0` | Only used when auxiliary classification is enabled. |

## Task profiles

| Task | Default testsets | Default training-set rule | Default size | Loss family note |
|---|---|---|---|---|
| `DIS5K` | `DIS-VD` | `DIS-TR` | `1024 x 1024` | Segmentation losses with BCE, IoU, and SSIM active. |
| `COD` | `CHAMELEON`, `NC4K`, `TE-CAMO`, `TE-COD10K` | `TR-COD10K+TR-CAMO` | `1024 x 1024` | Segmentation-style loss mix. |
| `HRSOD` | `DAVIS-S`, `TE-HRSOD`, `TE-UHRSD`, `DUT-OMRON`, `TE-DUTS` | `TR-DUTS+TR-HRSOD+TR-UHRSD` | `1024 x 1024` | Segmentation-style loss mix. |
| `General` | `DIS-VD`, `TE-P3M-500-NP` | Auto-discovered from `<data-root>/General` excluding testsets | `1024 x 1024` | Segmentation-style loss mix with MAE enabled. |
| `General-2K` | `DIS-VD`, `TE-P3M-500-NP` | Auto-discovered from `<data-root>/General-2K` excluding testsets | `2560 x 1440` | Same as `General`, but higher-resolution default. |
| `Matting` | `TE-P3M-500-NP`, `TE-AM-2k` | Auto-discovered from `<data-root>/Matting` excluding testsets | `1024 x 1024` | Matting-style loss mix with BCE, MAE, and SSIM active. |

## Loss families

| Task family | Active `lambdas_pix_last` |
|---|---|
| `DIS5K`, `COD`, `HRSOD` | `bce=30`, `iou=0.5`, `ssim=10`; other pixel losses are off. |
| `General`, `General-2K` | `bce=30`, `iou=0.5`, `mae=100`, `ssim=10`; other pixel losses are off. |
| `Matting` | `bce=30`, `mae=100`, `ssim=10`; IoU and the other pixel losses are off. |

## Backbone choices

Supported backbone ids in the checked snapshot:

- CNNs: `vgg16`, `vgg16bn`, `resnet50`
- Swin v1: `swin_v1_l`, `swin_v1_b`, `swin_v1_s`, `swin_v1_t`
- PVT v2: `pvt_v2_b5`, `pvt_v2_b2`, `pvt_v2_b1`, `pvt_v2_b0`
- DINOv3: `dino_v3_7b`, `dino_v3_h_plus`, `dino_v3_l`, `dino_v3_b`, `dino_v3_s_plus`, `dino_v3_s`

Notes:
- `freeze_bb` becomes true when the selected backbone name contains `dino_v3`.
- The model-architecture sub-skill owns the detailed backbone behavior and weight-loading consequences.

## Training schedule hints from `train.sh`

| Task | Epochs | `val_last` | `step` |
|---|---:|---:|---:|
| `DIS5K` | 500 | 50 | 5 |
| `COD` | 150 | 50 | 5 |
| `HRSOD` | 150 | 50 | 5 |
| `General` | 200 | 50 | 5 |
| `General-2K` | 250 | 30 | 2 |
| `Matting` | 150 | 50 | 5 |

## Safe override checklist

1. Set `task` first, then align `testsets` and `training_set`.
2. Ensure `<data-root>/<task>/<dataset>/{im,gt}` exists before building `MyData` for general-style tasks.
3. Use `dynamic_size` only when every sampled batch size can be floor-rounded to a multiple of 32.
4. Revisit `lambdas_pix_last` when switching between segmentation and matting.
5. Enable `auxiliary_classification` only when labels follow the DIS filename convention.
6. If you rely on automatic checkpoint schedule fields, keep a nearby `train.sh` visible to `Config`.
