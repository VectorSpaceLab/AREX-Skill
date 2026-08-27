# D-FINE data and configuration guide

This reference distills D-FINE's dataset YAMLs, model-size YAMLs, config merge behavior, and safe custom-dataset setup. It is self-contained operating guidance: do not require the user to inspect the original evidence files unless they are editing a live D-FINE checkout.

## Configuration mental model

D-FINE training/evaluation/inference starts from one YAML config passed with `-c`/`--config`. The D-FINE loader:

1. Reads `__include__` entries recursively.
2. Resolves relative includes from the YAML file that contains them.
3. Merges included dictionaries first.
4. Merges the final file over the included values; nested dictionaries are merged recursively and scalar/list values are replaced.
5. Applies CLI `-u`/`--update` dot-path overrides after YAML loading, using YAML scalar parsing for values.

A typical final detection config includes five layers:

```yaml
__include__: [
  '../dataset/coco_detection.yml',
  '../runtime.yml',
  './include/dataloader.yml',
  './include/optimizer.yml',
  './include/dfine_hgnetv2.yml',
]
```

The dataset file owns `task`, evaluator type, `num_classes`, `remap_mscoco_category`, and raw train/val dataset paths. The dataloader include owns common transforms, `total_batch_size`, `num_workers`, and the collate function. The architecture include owns `model: DFINE`, `eval_spatial_size`, HGNetv2/encoder/decoder defaults, criterion, and postprocessor. The model-size file owns size-specific overrides such as HGNetv2 variant, feature channels, depth, optimizer LR, epochs, and stop epochs.

A verified configuration load for `configs/dfine/dfine_hgnetv2_n_coco.yml` resolves to detection task, model `DFINE`, and `num_classes: 80`.

## Dataset YAML catalog

| Dataset YAML | Dataset type | Classes | `remap_mscoco_category` | Main fields |
|---|---:|---:|---:|---|
| `configs/dataset/coco_detection.yml` | `CocoDetection` | 80 | `True` | COCO train/val `img_folder`, `ann_file`, `return_masks: False`, `CocoEvaluator` |
| `configs/dataset/obj365_detection.yml` | `CocoDetection` | 366 | `False` | Objects365 train/val roots and preprocessed `new_zhiyuan_objv2_*_resized.json` annotations |
| `configs/dataset/custom_detection.yml` | `CocoDetection` | placeholder | `False` | User train/val image roots, user COCO JSONs, class count to edit |
| `configs/dataset/crowdhuman_detection.yml` | `CocoDetection` | 1 | `False` | CrowdHuman COCO-format train/val paths |
| `configs/dataset/voc_detection.yml` | `VOCDetection` | 20 | not used | VOC root, train/val split txt files, label file |

### Model-size and workflow config families

Use `{model}` as one of `n`, `s`, `m`, `l`, `x` unless noted.

| Workflow | Config pattern | Notes |
|---|---|---|
| COCO train/test/tune | `configs/dfine/dfine_hgnetv2_{model}_coco.yml` | Includes COCO dataset YAML with 80 classes and MS COCO remapping. |
| Objects365 train | `configs/dfine/objects365/dfine_hgnetv2_{model}_obj365.yml` | Includes Objects365 dataset YAML with 366 classes; expects preprocessed Object365 annotations. |
| Objects365-to-COCO fine-tune | `configs/dfine/objects365/dfine_hgnetv2_{model}_obj2coco.yml` | Includes COCO dataset YAML but uses shorter fine-tune schedule and warmup changes for Objects365 checkpoint tuning. |
| Custom COCO-format train/test | `configs/dfine/custom/dfine_hgnetv2_{model}_custom.yml` | Includes custom dataset YAML; edit `num_classes`, paths, and remap policy before use. |
| Objects365-to-custom fine-tune | `configs/dfine/custom/objects365/dfine_hgnetv2_{model}_obj2custom.yml` | Provided for `s`, `m`, `l`, and `x`; includes custom dataset YAML and fine-tune schedule. |
| CrowdHuman | `configs/dfine/crowdhuman/dfine_hgnetv2_{model}_ch.yml` | One-class CrowdHuman COCO-format detection. |
| VOC | dataset YAML only | Use `VOCDetection` fields if creating a VOC-focused final config; the standard D-FINE final config catalog is COCO-family focused. |

## Dataloader fields that matter

A D-FINE detection dataloader has this shape after includes merge:

```yaml
train_dataloader:
  type: DataLoader
  dataset:
    type: CocoDetection
    img_folder: /path/to/images
    ann_file: /path/to/instances.json
    return_masks: False
    transforms:
      type: Compose
      ops: ...
  shuffle: True
  total_batch_size: 32
  num_workers: 4
  drop_last: True
  collate_fn:
    type: BatchImageCollateFunction
```

Important fields:

- `dataset.type`: `CocoDetection` for COCO-format JSON, `VOCDetection` for VOC txt/XML layout.
- `img_folder` and `ann_file`: only for `CocoDetection`; `file_name` values in JSON are joined under `img_folder`.
- `root`, `ann_file`, and `label_file`: VOC uses a root plus split/label files instead of COCO JSON.
- `return_masks`: usually `False`; mask training is not the normal D-FINE detection path.
- `shuffle`, `drop_last`, `num_workers`: PyTorch dataloader controls.
- `total_batch_size`: global batch size across all distributed ranks; D-FINE computes per-rank `batch_size` from it.
- `collate_fn`: `BatchImageCollateFunction` concatenates batch images and may apply multi-scale resizing before its `stop_epoch`.

D-FINE requires exactly one of `total_batch_size` or `batch_size` in each dataloader config. If `total_batch_size` is present, it must be divisible by the world size used by distributed training.

## Transform and input-size policies

The common train transform sequence is:

1. `RandomPhotometricDistort`
2. `RandomZoomOut`
3. `RandomIoUCrop`
4. `SanitizeBoundingBoxes`
5. `RandomHorizontalFlip`
6. `Resize` to `[640, 640]` by default
7. `SanitizeBoundingBoxes`
8. `ConvertPILImage` to float tensor, scaled to `[0, 1]`
9. `ConvertBoxes` to normalized `cxcywh`

The train transform policy uses `name: stop_epoch`; after the configured epoch it stops the heavy early augmentations listed in `ops`. The train collate function can also stop multi-scale resizing after its own `stop_epoch`.

The validation transform sequence is simple and deterministic: fixed `Resize` then `ConvertPILImage`.

To change input size consistently:

```yaml
train_dataloader:
  dataset:
    transforms:
      ops:
        - {type: Resize, size: [320, 320]}
  collate_fn:
    base_size: 320
val_dataloader:
  dataset:
    transforms:
      ops:
        - {type: Resize, size: [320, 320]}
eval_spatial_size: [320, 320]
```

Keep train resize, val resize, collate `base_size`, and architecture `eval_spatial_size` aligned. If a model/inference/export question depends on `eval_spatial_size`, route to [../../architecture-api/SKILL.md](../../architecture-api/SKILL.md) or [../../inference-export/SKILL.md](../../inference-export/SKILL.md).

## Category and remap rules

D-FINE's COCO dataset loader has two label modes:

- `remap_mscoco_category: True`: use only for standard MS COCO category IDs. COCO sparse category IDs such as 1, 2, 3, ..., 90 are mapped to contiguous labels 0-79.
- `remap_mscoco_category: False`: use for custom, Objects365, CrowdHuman, and non-COCO class sets. Annotation `category_id` values become training labels directly, so they must fit the model head range.

For a custom COCO-format dataset:

- Set `num_classes` to the number of object classes.
- Set `remap_mscoco_category: False`.
- Prefer contiguous category IDs `0..num_classes-1`; at minimum, every annotation `category_id` must be `>= 0` and `< num_classes`.
- Keep train and validation category ID/name mappings identical.
- Do not use standard COCO sparse IDs with `remap_mscoco_category: False` unless `num_classes` and the label mapping have been deliberately designed for those raw IDs.

For standard COCO:

- Keep `num_classes: 80`.
- Keep `remap_mscoco_category: True`.
- Use the standard 80 COCO categories with their original sparse COCO IDs.

For Objects365:

- Keep the Objects365 config's `num_classes: 366` and `remap_mscoco_category: False` unless you have a deliberate class-head change.
- Treat Object365 remap/resize preprocessing as a long, mutating data-preparation workflow; this sub-skill only supports preflight and validation.

## Safe custom COCO-format setup

1. Choose model size and workflow:
   - Train from scratch/custom checkpoint: `configs/dfine/custom/dfine_hgnetv2_{model}_custom.yml`.
   - Fine-tune from an Objects365 checkpoint: `configs/dfine/custom/objects365/dfine_hgnetv2_{model}_obj2custom.yml` for `s`, `m`, `l`, or `x`.
2. Edit the included custom dataset YAML:
   - `num_classes: <your class count>`
   - `remap_mscoco_category: False`
   - train/val `img_folder`
   - train/val `ann_file`
3. Ensure COCO JSON has top-level `images`, `annotations`, and `categories` lists.
4. Ensure every annotation references an existing image ID and category ID.
5. Ensure each bbox is COCO `xywh` with finite width/height and nonnegative width/height.
6. Run the bundled validator before training:

```bash
python ../scripts/validate_detection_dataset.py \
  --annotation dataset/annotations/instances_train.json \
  --image-root dataset/images/train \
  --dataset-config configs/dataset/custom_detection.yml
```

Run it again for validation JSON/root. Add `--json` if a caller needs machine-readable output.

### Two-class custom fine-tune from Objects365 checkpoint

For a two-class custom dataset such as `person` and `car`:

```yaml
num_classes: 2
remap_mscoco_category: False
categories:
  - {id: 0, name: person}
  - {id: 1, name: car}
```

Use an `obj2custom` config matching the checkpoint size where available. The data/config part is only the class count, remap policy, category IDs, and paths. The actual `-t <checkpoint>` command belongs in [../../training-evaluation/SKILL.md](../../training-evaluation/SKILL.md). If the user wants to edit Objects365 class-head mapping such as `Person`/`Car` source IDs, route to [../../architecture-api/SKILL.md](../../architecture-api/SKILL.md) because that touches solver/model internals.

## Object365 remap/resize preflight

D-FINE's Object365 preparation expects a large dataset with train/val JSON files, image trees, a validation subset split, and a resized annotation set. The original helper scripts write new JSON files and resized images. Do not run those long mutating operations from this sub-skill.

Before a user deliberately runs Object365 remap/resize elsewhere, check:

- Base directory has train and validation subtrees.
- Original annotation names are present before remap: `zhiyuan_objv2_train.json` and `zhiyuan_objv2_val.json`.
- Validation images copied into the expected train-side location if the remap workflow needs them.
- There is enough disk space for resized images and new JSON files.
- The target config points at the postprocessed JSON names used by D-FINE, usually `new_zhiyuan_objv2_train_resized.json` and `new_zhiyuan_objv2_val_resized.json`.
- A small JSON-only validation passes before and after preprocessing.

Use the bundled validator for annotation consistency and optional image existence checks. For actual training after preprocessing, hand off to [../../training-evaluation/SKILL.md](../../training-evaluation/SKILL.md).

## YAML override examples

D-FINE `-u` overrides use dot paths and YAML-parsed values. Shell quoting is the caller's responsibility.

```bash
# Change global train/val batch sizes for a four-rank run.
-u train_dataloader.total_batch_size=64 val_dataloader.total_batch_size=128

# Point a custom config at a dataset.
-u train_dataloader.dataset.img_folder=/data/my/images/train \
   train_dataloader.dataset.ann_file=/data/my/annotations/instances_train.json \
   val_dataloader.dataset.img_folder=/data/my/images/val \
   val_dataloader.dataset.ann_file=/data/my/annotations/instances_val.json \
   num_classes=2 remap_mscoco_category=False

# Change input size; keep data and model spatial size aligned.
-u train_dataloader.dataset.transforms.ops='[{type: Resize, size: [320, 320]}]' \
   train_dataloader.collate_fn.base_size=320 \
   val_dataloader.dataset.transforms.ops='[{type: Resize, size: [320, 320]}]' \
   eval_spatial_size='[320, 320]'
```

Prefer editing a copied YAML or a small derived YAML for durable experiments. Use CLI overrides for short experiments or one-off launch scripts.

## How training/evaluation consumes these configs

`YAMLConfig` constructs objects lazily from the merged config:

- `model`, `criterion`, and `postprocessor` use shared `num_classes`, `eval_spatial_size`, focal-loss, and remap settings.
- `train_dataloader` and `val_dataloader` build datasets and transforms from the merged dataloader dictionaries.
- `evaluator` builds a COCO evaluator from the validation dataloader when `evaluator.type: CocoEvaluator`.
- `get_rank_batch_size` computes per-rank dataloader batch size from `total_batch_size / world_size`.

Once paths, categories, batch size, and input size are correct, switch to [../../training-evaluation/SKILL.md](../../training-evaluation/SKILL.md) for launch commands or [../../inference-export/SKILL.md](../../inference-export/SKILL.md) for inference/export commands that reuse the config.
