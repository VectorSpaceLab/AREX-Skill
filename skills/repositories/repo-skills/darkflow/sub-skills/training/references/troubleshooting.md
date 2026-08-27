# Training Troubleshooting

## Purpose

Read this when a custom dataset, config edit, training run, or checkpoint resume fails.

## Data and label failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Annotation directory not found ...` | `--annotation` points to a missing folder | Use the folder that contains Pascal VOC XML files |
| Validator reports unknown labels | XML object names are not present in the label file | Add the class to the label file or fix the XML label spelling |
| `labels.txt and ... indicate inconsistent class numbers` | Label count and config `classes` disagree | Update the label file and the final `[region]` `classes` together |
| Batches fail with zero width/height errors | XML `size/width` or `size/height` is zero or missing | Fix or remove the bad annotation before training |
| Image load failures during batching | XML filenames are not present under the dataset image directory | Move images, fix XML `filename`, or pass the correct `--dataset` path |

## Config failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Final layer shape mismatch or random output layer initialization | `filters` does not equal `num * (classes + 5)` | Recalculate filters from the final region layer's `num` and class count |
| Pretrained weights do not partially reuse layers as expected | The copied config no longer aligns with the original model family | Keep the original base config unchanged and copy it before editing |
| Wrong labels appear during prediction after training | The active model name triggered built-in VOC/COCO label loading | Use a custom config name and pass `--labels <labels.txt>` if needed |

## Checkpoint failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `--load -1` cannot resume | The backup folder has no checkpoint state file | Point `--backup` to the checkpoint folder that contains the latest checkpoint metadata |
| Positive checkpoint step does not load | The step number does not exist for the selected model name | Check checkpoint filenames and use the correct step value |
| Restore errors after changing config | The checkpoint architecture differs from the current config | Revert incompatible config edits or start from weights rather than checkpoint state |

## Runtime and resource issues

- Long training runs require explicit time, data, and compute budget approval.
- CPU training is possible but slow; do not promise GPU behavior unless the TensorFlow 1.x GPU stack is verified.
- TensorBoard summaries need a writable `--summary` directory.
- Large image folders and high `--batch` values can exhaust memory. Reduce `--batch` first.

## Recovery order

1. Run `../scripts/check_voc_dataset.py` against labels, annotations, and images.
2. Recheck the config class and filter counts.
3. Run a tiny, explicitly bounded training attempt before a long training job.
4. Only then resume or export the trained checkpoint through `../../inference/SKILL.md`.
