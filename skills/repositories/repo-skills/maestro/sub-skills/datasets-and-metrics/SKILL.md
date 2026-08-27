---
name: datasets-and-metrics
description: "Validate Maestro dataset layouts, Roboflow identifiers, COCO
  adapters, metrics, run directories, reproducibility, and device selection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# datasets-and-metrics

Use this sub-skill for the shared data and metric layer that sits in front of all Maestro model workflows.

## Covers

- JSONL datasets with `train` / `valid` / `test` splits and required `image`, `prefix`, `suffix` keys.
- COCO datasets with `_annotations.coco.json` and VLM adapter callbacks.
- Roboflow identifier parsing and dataset resolution.
- Metric selection, tracking, plot export, and metric JSON dumps.
- Run directory creation, reproducibility seeding, and device-string parsing.

## Does not cover

- Florence-2, PaliGemma 2, or Qwen2.5-VL model-specific train, predict, collate, or formatter logic.
- Real Roboflow downloads unless you intentionally set `ROBOFLOW_API_KEY`.

## Start here

- [data formats](references/data-formats.md)
- [API reference](references/api-reference.md)
- [metrics and utilities](references/metrics-and-utilities.md)
- [troubleshooting](references/troubleshooting.md)
- [validate_jsonl_dataset.py](scripts/validate_jsonl_dataset.py)
- [smoke_coco_vlm_adapter.py](scripts/smoke_coco_vlm_adapter.py)

## Routing notes

- Route COCO detection string formatting and model-specific object-detection flows to sibling sub-skills such as `../florence-2/` and `../qwen-2-5-vl/`.
- Route JSON extraction prompt and collate behavior to `../paligemma-2/` or the relevant model sub-skill.
- Use this sub-skill to validate the shared dataset shape first, then hand off to the model-specific skill.

## Typical flow

1. Validate a JSONL dataset with `scripts/validate_jsonl_dataset.py`.
2. Resolve a local path or Roboflow identifier with `resolve_dataset_path()`.
3. For COCO data, provide prefix and suffix formatter callbacks to `COCOVLMAdapter` or `create_data_loaders()`.
4. Select metrics with `parse_metrics()` and track them with `MetricsTracker`.
5. Set reproducibility and device policy before model-specific training or inference.

## Quick rules

- `create_data_loaders()` expects `train`, `valid`, and `test` splits.
- COCO loading needs both formatter callbacks.
- `parse_metrics()` accepts `edit_distance`, `bleu`, and `mean_average_precision`.
- `parse_device_spec()` accepts `auto`, `cpu`, `cuda`, `cuda:N`, and `mps`.
- `ensure_reproducibility()` can be used at process start even when you do not pass a seed.
