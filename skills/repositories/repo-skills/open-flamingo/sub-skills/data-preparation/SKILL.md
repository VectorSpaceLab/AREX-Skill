---
name: data-preparation
description: "Prepare and validate OpenFlamingo data artifacts for MMC4/LAION
  training and VQA-style evaluation, including MMC4 WebDataset conversion and
  VQAv2/VizWiz result filling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# OpenFlamingo data preparation

Use this sub-skill when a task involves preparing or checking OpenFlamingo-compatible data before training or evaluation. It covers:

- Converting downloaded MMC4 ZIP metadata plus downloaded raw images into WebDataset tar shards whose samples contain a `json` payload.
- Confirming the expected LAION, MMC4, ChatGPT-generated interleaved sequence, VQAv2, VizWiz, and TextVQA data schemas.
- Filling VQAv2 or VizWiz test/test-dev submission JSON files so every required test question receives either a normalized prediction or an empty answer.
- Performing safe, bounded validation of common JSON inputs and shard path patterns before expensive training/evaluation runs.

Do not assume that full model downloads, full benchmark datasets, training, or benchmark evaluation have already been run. Treat those as expensive/network/data-dependent steps that require explicit user-provided data and runtime capacity.

## Bundled references

- [Data formats](references/data-formats.md): required schemas for MMC4 WebDataset samples, LAION tar samples, ChatGPT-generated interleaved samples, and VQA-style evaluation JSON.
- [Workflows](references/workflows.md): concrete conversion, validation, and result-filling commands with safety notes.
- [Troubleshooting](references/troubleshooting.md): symptoms and fixes for missing images, base64/PIL failures, brace expansion, shard sizing, missing question IDs, and huge annotation files.

## Bundled scripts

- [`scripts/validate_open_flamingo_data.py`](scripts/validate_open_flamingo_data.py): safe preflight validator for MMC4 JSON/JSONL/ZIP metadata, VQA prediction lists, and WebDataset tar path naming.
- [`scripts/convert_mmc4_to_wds.py`](scripts/convert_mmc4_to_wds.py): standalone MMC4 ZIP + image-directory to WebDataset tar converter.
- [`scripts/fill_vqa_testdev_results.py`](scripts/fill_vqa_testdev_results.py): standalone VQAv2/VizWiz result filler with answer normalization and input validation.

## Fast decision guide

1. **Training on LAION**: verify tar shards contain paired text and image components (`.txt` plus one of `.jpg`, `.jpeg`, `.png`) and pass matching shard braces to the training command.
2. **Training on MMC4**: first validate a bounded sample of the MMC4 JSON/JSONL metadata, then run the bundled MMC4 converter, then pass the resulting tar shard brace pattern as `--mmc4_shards`.
3. **Training on ChatGPT-generated interleaved sequences**: verify each JSON sample has `example`, `image_map`, and base64 images keyed by placeholders such as `_!_IMAGE1_!_`.
4. **VQAv2/VizWiz test submission**: validate the model prediction list, then run the result filler against the full test questions JSON.
5. **TextVQA/VizWiz annotations**: use VQA-style `questions` and `annotations` JSON files as described in [Data formats](references/data-formats.md); the bundled result filler is only for VQAv2 and VizWiz final/test-dev style outputs.

## Minimal safe checks

```bash
python scripts/validate_open_flamingo_data.py --help
python scripts/convert_mmc4_to_wds.py --help
python scripts/fill_vqa_testdev_results.py --help
```

For a small prediction file:

```bash
python scripts/validate_open_flamingo_data.py \
  --mode vqa-predictions \
  --input-path predictions.json \
  --max-records 100
```

For a small MMC4 metadata sample:

```bash
python scripts/validate_open_flamingo_data.py \
  --mode mmc4-json \
  --input-path shard_0.zip \
  --max-records 50
```
