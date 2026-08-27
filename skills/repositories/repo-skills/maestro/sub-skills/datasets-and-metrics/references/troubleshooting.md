# Troubleshooting

This page focuses on the shared data and metric layer. If the issue is model-specific, hand it off to the relevant sibling sub-skill.

## JSONL dataset problems

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `dataset format not recognized` from `create_data_loaders()` | The root does not contain a detectable JSONL or COCO split | Confirm that at least one split directory has `annotations.jsonl` or `_annotations.coco.json`. |
| `All dataset splits (train, valid, and test) must be present` | One or more of the required splits is missing | Add all three splits before calling `create_data_loaders()`. |
| Missing key warnings | A JSONL row is missing `image`, `prefix`, or `suffix` | Fix the row and rerun the validator. |
| `image file not found` warnings | The `image` field does not resolve inside the split directory | Place the image inside the split folder or correct the relative path. |
| Zero valid entries after load | Every row was skipped during validation | Run `scripts/validate_jsonl_dataset.py` to identify the bad rows before training. |

## COCO dataset problems

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `COCO dataset detected, but detections_to_prefix_formatter and detections_to_suffix_formatter were not provided` | COCO input was passed without formatter callbacks | Pass model-specific formatter functions into `COCOVLMAdapter()` or `create_data_loaders()`. |
| `Could not parse annotations file` | The COCO JSON is malformed or not a COCO-like structure | Check the top-level `images`, `annotations`, and `categories` fields. |
| Dataset length is smaller than expected | Missing images or invalid annotation records were skipped | Use the bundled smoke script and inspect the COCO file and image paths. |

## Roboflow resolution problems

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `Missing Roboflow API key` | `ROBOFLOW_API_KEY` is not set | Export the key before calling `resolve_dataset_path()` on a Roboflow identifier. |
| `Maestro does not support <type> Roboflow datasets` | The project type is not mapped to a supported dataset format | Use a supported Roboflow project type or export the data locally first. |
| `No dataset versions available` | The Roboflow project exists but has not been versioned | Create a version or pass a specific versioned identifier. |
| `parse_roboflow_identifier()` returns `None` | The identifier is malformed | Use `workspace/project` or `workspace/project/version`. |

## Metric and tracker problems

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `Unsupported metric:` | The metric name is not one of the supported aliases | Use `edit_distance`, `bleu`, or `mean_average_precision`. |
| `evaluate` import or BLEU download trouble | The BLEU metric backend is unavailable or cannot reach its cache source | Install the metric dependencies or avoid BLEU in offline environments. |
| mAP results look flat or empty | The predictions and targets are not in `supervision.Detections` format | Check the object-detection formatting layer in the model-specific sub-skill. |

## Device and reproducibility problems

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `Unrecognized device spec:` | The device string is not one of the supported forms | Use `auto`, `cpu`, `cuda`, `cuda:N`, or `mps`. |
| `Requested cuda:N but only ... GPU(s) are available` | The requested GPU index is out of range | Choose a valid index or use `auto`. |
| A run becomes slower after enabling reproducibility | Deterministic algorithms and cuDNN benchmarking were tightened | Keep the deterministic settings for repeatability, or disable them only if the workflow explicitly allows it. |

## Quick recovery path

1. Run `scripts/validate_jsonl_dataset.py` on the dataset root.
2. If COCO data is involved, run `scripts/smoke_coco_vlm_adapter.py`.
3. Confirm the metric names with `parse_metrics()`.
4. Confirm the device string with `parse_device_spec()` and `device_is_available()`.
5. Hand off any model-specific formatting or training issues to the sibling sub-skill.
