# D-FINE data/config troubleshooting

Use this when config selection, dataset paths, annotations, class counts, or dataloader setup fails before a training/evaluation/inference workflow. For actual launch/checkpoint errors, hand off to [../../training-evaluation/SKILL.md](../../training-evaluation/SKILL.md). For export/inference behavior after a config loads, hand off to [../../inference-export/SKILL.md](../../inference-export/SKILL.md).

## Fast triage

1. Confirm the final config family matches the dataset: COCO, Objects365, Objects365-to-COCO, custom, Objects365-to-custom, CrowdHuman, or VOC.
2. Confirm `__include__` paths resolve relative to the YAML file that declares them.
3. Confirm train/val `img_folder` and `ann_file` exist for `CocoDetection`, or VOC `root`, split txt, and label file exist for `VOCDetection`.
4. Confirm `num_classes` and `remap_mscoco_category` match the annotation category IDs.
5. Run the bundled COCO validator for each COCO-format split:

```bash
python ../scripts/validate_detection_dataset.py \
  --annotation dataset/annotations/instances_val.json \
  --image-root dataset/images/val \
  --dataset-config configs/dataset/custom_detection.yml
```

6. If distributed training will be used, verify `total_batch_size % world_size == 0` for train and validation dataloaders.

## Symptom matrix

| Symptom | Likely cause | Fix |
|---|---|---|
| `FileNotFoundError` or COCO loader cannot open `ann_file` | Config still has placeholder path, wrong split path, or include override did not apply | Edit the dataset YAML or add `-u train_dataloader.dataset.ann_file=... val_dataloader.dataset.ann_file=...`; validate both paths before launch. |
| Images not found even though JSON loads | JSON `file_name` is relative to a different root than `img_folder` | Point `img_folder` at the directory that should prefix JSON `file_name`, or rewrite `file_name` values in a deliberate dataset-prep step. Use validator `--image-root` to list missing examples. |
| Missing top-level `images`, `annotations`, or `categories` | Annotation is not COCO detection JSON or conversion script emitted a partial file | Re-export conversion output as COCO detection format. Required top-level lists are `images`, `annotations`, and `categories`. |
| Annotation `image_id` not found | Conversion dropped image entries or mixed train/val annotations | Regenerate the split so every annotation references an image in the same JSON. |
| Annotation `category_id` not found | Category list and annotations use different ID namespaces | Align `categories[].id` with every annotation `category_id`; keep train and val mapping identical. |
| `remap_mscoco_category` wrong for custom categories | Custom dataset used `True`, causing D-FINE to treat IDs as standard MS COCO IDs | Set `remap_mscoco_category: False` for custom, CrowdHuman, and Objects365. Only standard COCO should use `True`. |
| `num_classes` mismatch or class-head size mismatch | Config class count does not fit raw labels or checkpoint head | For custom data set `num_classes` to the number of target classes and keep label IDs `< num_classes`. If tuning from a checkpoint with a different class head, route the checkpoint/loading decision to [../../training-evaluation/SKILL.md](../../training-evaluation/SKILL.md). |
| `total_batch_size should be divisible by world size` | `YAMLConfig.get_rank_batch_size` divides global `total_batch_size` by distributed world size | Use a total batch size divisible by the number of ranks/processes, or run fewer/more processes. Do not set both `batch_size` and `total_batch_size`. |
| Assertion about choosing `batch_size` or `total_batch_size` | Both keys are present, or neither key is present after YAML merge | Keep exactly one key per dataloader. Prefer `total_batch_size` for D-FINE distributed recipes. |
| Dataloader or transform fails on boxes | Bboxes have negative width/height, non-finite values, wrong format, or are all zero-area after cropping | COCO bboxes must be `[x, y, width, height]`; width/height must be nonnegative and useful boxes should be positive area. Run the validator and fix conversion output. |
| Transform/collate failure involving image tensors | Non-image file, corrupt file, grayscale/alpha-only image, or inconsistent image mode | Convert dataset images to readable RGB images in a separate data-prep step; remove corrupt files or annotations. Re-run image existence checks. |
| Validation mAP looks wrong after custom setup | Category IDs differ between train/val, IDs start at 1 while `num_classes` assumes 0-based labels, or COCO remap is enabled accidentally | Use identical category tables in train and val. Prefer custom IDs `0..num_classes-1` with `remap_mscoco_category: False`. |
| Objects365 config cannot find `new_zhiyuan_objv2_*_resized.json` | Long remap/resize preprocessing was not completed, used a different suffix, or output path differs | Preflight the Object365 base tree and JSON names. Do not silently switch to original JSON unless the user accepts the difference from D-FINE recipes. |
| `__include__` appears ignored | The edited field is overridden later by the final model-size file or by CLI `-u` | Remember includes merge first, final config overrides after, and CLI updates override last. Inspect the final merged YAML when debugging. |

## Custom category checklist

For custom COCO-format datasets, require all of the following before training:

- `num_classes` equals the intended number of target classes.
- `remap_mscoco_category: False`.
- Every annotation category ID exists in `categories`.
- Every annotation category ID is less than `num_classes`.
- Train and validation JSONs use the same ID/name mapping.
- Category IDs are preferably contiguous from `0` to `num_classes - 1`.

If a user insists on one-based custom IDs, warn that raw labels equal category IDs when remap is false; this can waste class 0 or put the maximum ID outside the head range. Prefer remapping the dataset to zero-based IDs before training.

## Batch-size/world-size examples

D-FINE's dataloader computes per-rank batch size from the merged YAML:

- 4 processes with `train_dataloader.total_batch_size: 128` -> per-rank batch size 32.
- 8 processes with `train_dataloader.total_batch_size: 128` -> per-rank batch size 16.
- 3 processes with `total_batch_size: 128` -> invalid, because 128 is not divisible by 3.

Fix with a YAML edit or CLI override, then use [../../training-evaluation/SKILL.md](../../training-evaluation/SKILL.md) to regenerate the launch command.

## Object365 safety notes

The Object365 remap and resize helpers are long-running and mutating: they write new JSON files and can create resized image copies. In this sub-skill, limit work to:

- checking input tree shape,
- confirming expected original/postprocessed JSON names,
- validating JSON consistency,
- checking a bounded set of image paths when needed,
- warning about disk/time cost and backup needs.

Only run the actual remap/resize workflow after explicit user approval in an appropriate execution workflow.
