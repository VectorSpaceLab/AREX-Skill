# Model Zoo and Config Selection

Use this guide to choose an MMYOLO config family and baseline pattern before editing a child config. For field-level editing rules, see [configuration editing](configuration.md).

## How MMYOLO organizes model choices

MMYOLO exposes a root `model-index.yml` that imports family-level `metafile.yml` files. The imported families in v0.6.0 are:

- YOLOv5
- YOLOv6
- YOLOv7
- YOLOv8
- YOLOX
- RTMDet
- PPYOLOE / PPYOLOE+

Each family metafile lists model names, config filenames, checkpoint URLs, and metrics. Treat these fields as selection signals, not as commands to download or run anything from this sub-skill.

The model zoo table reports signals such as:

| Signal | How to use it |
| --- | --- |
| Architecture/size | Choose tiny/n/s/m/l/x or P5/P6 according to latency, memory, and accuracy needs. |
| Input size | P5 configs are usually 640-scale; P6 configs are usually 1280-scale and cost more memory. |
| Batch/epoch schedule | Encoded in config names such as `8xb16-300e`; adapt if the user's hardware differs. |
| SyncBN / BN | SyncBN is common for multi-GPU training; convert to BN when a single-device workflow cannot support SyncBN. |
| AMP | Indicates whether mixed precision was part of the reference recipe; training workflow owns the actual flag/use. |
| Memory | Use as a rough family/size filter before training. |
| Params and FLOPs | Estimate model size and compute cost; FLOP scripts belong to model/API or training-analysis workflows. |
| Box AP and TTA Box AP | Compare expected accuracy; if TTA AP is listed, the selected config still must contain `tta_model` and `tta_pipeline`. |
| TensorRT latency | Deployment-oriented signal only; route export/backend work to `deployment-conversion`. |

## Family selection matrix

| Family | Typical config patterns | Strengths | Customization notes |
| --- | --- | --- | --- |
| YOLOv5 | `yolov5_{n,s,m,l,x}-v61_syncbn_fast_8xb16-300e_coco.py`, P6 `*-p6-v62*`, one-class cat variants | Broad baseline, anchor-based, many size variants, good first choice for simple fine-tunes | Update head `num_classes`; for custom objects often update anchors; update optimizer batch-size scaling. |
| YOLOv6 | `yolov6_{n,t,s,m,l}_syncbn_fast_8xb32-*e_coco.py`, `yolov6_v3_*`, one-class cat variant | Efficient YOLOv6 family, later version-id configs included | Update head `num_classes`, plus initial/final assigner `num_classes`; keep last-stage switch hooks aligned with `max_epochs`. |
| YOLOv7 | `yolov7_tiny/l/x*_syncbn_fast_8x16b-300e_coco.py`, P6 variants, one-class cat variant | YOLOv7-style models including P6 large-input variants | Anchor-based; update head classes and anchors if anchors are dataset-specific. Preserve `8x16b` naming used by this family. |
| YOLOv8 | `yolov8_{n,s,m,l,x}_syncbn_fast_8xb16-500e_coco.py`, mask-refine variants, one-class cat variant | Strong modern baseline; model zoo includes TTA AP for several sizes | Update head `num_classes` and assigner `num_classes`; adjust close-mosaic hook when shortening epochs. |
| YOLOX | `yolox_{tiny,s,m,l,x}_fast_8xb8-300e_coco.py`, RTMDet-hyp variants, one-class cat variant | YOLOX baselines and RTMDet-hyperparameter variants | Update head `num_classes`; keep mode-switch hooks and scheduler stages consistent with `num_last_epochs`. |
| RTMDet | `rtmdet_{tiny,s,m,l,x}_syncbn_fast_8xb32-300e_coco.py`, distillation and instance variants, one-class cat variant | Strong accuracy/latency tradeoff, CSPNeXt backbone, RTMDet family recipes | Update head and assigner classes; stage-2 hooks/schedulers must move when `max_epochs` changes. |
| PPYOLOE / PPYOLOE+ | `ppyoloe_plus_{s,m,l,x}_fast_8xb8-80e_coco.py`, other PPYOLOE schedules, one-class cat variant | PPYOLOE+ recipes with Object365-pretrained weights and shorter COCO fine-tune schedule | Update head, initial assigner, and assigner classes; memory can be high even for small variants. |
| Deploy configs | ONNXRuntime, TensorRT, RKNN, static/dynamic/int8/fp16 patterns | Export/backend configuration | Cross-link only: deployment export and backend validation belong to `deployment-conversion`, not this sub-skill. |

## Reading config filenames

MMYOLO names encode the main recipe. A typical filename follows:

```text
{algorithm}_{components-or-size}[-version]_[norm]_[preprocessor]_{gpu x batch}-{schedule}_{train-dataset}[_test-dataset].py
```

Examples:

- `yolov5_s-v61_syncbn_fast_8xb16-300e_coco.py`
  - YOLOv5 small, v6.1 style, SyncBN, fast data preprocessor, 8 GPUs x 16 images per GPU, 300 epochs, COCO.
- `yolov8_s_fast_1xb12-40e_cat.py`
  - YOLOv8 small, fast preprocessor, 1 device x 12 images per device, 40 epochs, cat dataset.
- `rtmdet_tiny_syncbn_fast_8xb32-300e_coco.py`
  - RTMDet tiny, SyncBN, fast preprocessor, 8 x 32 batch recipe, 300 epochs, COCO.
- `yolox_s_fast_8xb32-300e-rtmdet-hyp_coco.py`
  - YOLOX small using RTMDet-style hyperparameters.

Do not rely on the name alone. Always inspect the expanded config because variables such as `max_epochs`, `batch_shapes_cfg`, `param_scheduler`, hooks, and `num_classes` may be inherited or overridden.

## Choosing a baseline for a user request

### Start from the least-surprising family

1. If the user names a family, use that family and choose the closest size/schedule.
2. If the user wants a simple one-class or few-class COCO fine-tune, start from a provided cat-style child config pattern in the target family when available.
3. If the user wants a speed/edge baseline but not deployment export, choose tiny/n/s variants and avoid deploy configs until export is explicitly requested.
4. If the user wants high accuracy and has enough memory, consider l/x or P6 variants, but flag the larger input/memory cost.
5. If the user mentions TTA, prefer configs that already define `tta_model` and `tta_pipeline`, or create a child config that imports/adds the TTA base pattern.

### Use model-index/metafile evidence this way

A future agent may inspect model metadata, but the decision logic is:

- Prefer models with published weights when fine-tuning from a pretrained checkpoint is requested.
- Prefer configs with the same dataset family when possible; otherwise adapt COCO-style detection fields carefully.
- Use AP/TTA AP to compare accuracy only among models with comparable input sizes and recipes.
- Use memory/params/FLOPs to rule out models before sending to training.
- Use TensorRT latency only as a deployment planning hint, not as proof that export will work in the user's environment.

## Family-specific baseline notes

### YOLOv5

- Anchor-based P5 and P6 configs are present.
- Common custom fields: `anchors`, `model.bbox_head.head_module.num_classes`, `model.bbox_head.prior_generator.base_sizes`, dataloader metadata and paths, optimizer batch-size scaling.
- `batch_shapes_cfg` may be enabled in validation/test dataset configs. TTA will disable it.
- Single-class fine-tunes can emit a normal YOLOv5 warning that classification loss is zero.

### YOLOv6

- Both older YOLOv6 names and `yolov6_v3_*` names are present.
- Custom class count is needed in the head module and train assigners.
- Short runs should update `num_last_epochs`, scheduler intervals, and mode-switch hook fields together.

### YOLOv7

- Anchor-based configs include tiny, l/x, and P6 w/e/d/e2e patterns.
- File names may use `8x16b` notation rather than `8xb16`.
- The loss classification weight can depend on `num_classes / 80`, so inspect inherited loss fields after changing classes.

### YOLOv8

- COCO configs use 500 epochs by default.
- Mask-refine variants are available; choose them only if the user wants the mask-refine recipe and supporting data assumptions.
- Custom fine-tune needs `model.bbox_head.head_module.num_classes` and `model.train_cfg.assigner.num_classes`.
- Close-mosaic custom hook switch epoch must be moved when shortening `max_epochs`.

### YOLOX

- Original YOLOX-style and RTMDet-hyperparameter variants are present.
- Custom fine-tune sets head classes and usually updates scheduler stages and the YOLOX mode-switch hook.
- The RTMDet-hyp variants are useful when the user wants stronger optimized training settings but should still be treated as YOLOX configs.

### RTMDet

- Tiny/s/m/l/x detection configs are present, along with distillation and instance-related variants.
- Strong default choice when the user asks for an OpenMMLab-native fast detector and has no strict YOLO-family preference.
- Custom fine-tune sets head and assigner classes; `num_epochs_stage2` and related hooks/schedulers must match shortened schedules.

### PPYOLOE / PPYOLOE+

- PPYOLOE+ model zoo entries commonly use an 80-epoch COCO recipe with Object365-pretrained weights.
- Custom fine-tune needs class updates in head, initial assigner, and assigner.
- Treat memory notes seriously; even small PPYOLOE+ variants can be heavier than similarly named YOLOv5/YOLOv8 variants.

## Selection handoff template

When handing a config choice to another workflow, include:

```text
Selected family: <family>
Baseline pattern: <config name or user-provided config path>
Reason: <speed/accuracy/resource/dataset/pretrained/TTA signal>
Customization required: <classes, dataloaders, evaluator, hooks, schedulers, TTA>
Validation status: <summary helper output reviewed / issues found>
Route next: <training-evaluation | inference-visualization | deployment-conversion | data-tools | model-api>
```
