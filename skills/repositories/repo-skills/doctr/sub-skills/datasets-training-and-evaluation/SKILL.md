---
name: datasets-training-and-evaluation
description: "Use docTR datasets, label formats, safe dataset validation,
  training/evaluation reference scripts, metrics, transforms, DataLoader,
  synthetic generators, and DDP/GPU caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# docTR datasets, training, and evaluation

Use this sub-skill when the user needs to prepare, validate, load, train with, or evaluate datasets for docTR detection, recognition, OCR/KIE-style detection, layout analysis, table structure recognition, character classification, or orientation classification.

Do **not** run full training, dataset downloads, latency benchmarks, or multi-GPU jobs by default. First validate local labels and run only cheap import/help/batch-smoke checks unless the user explicitly asks for the heavy run and accepts compute/network costs.

## Route by user intent

- Custom or built-in dataset loading, JSON schema questions, `VOCABS`, `encode_string`, `decode_sequence`, `CharacterGenerator`, `WordGenerator`, transforms, or `DataLoader`: read [references/data-formats.md](references/data-formats.md).
- Choosing or adapting the reference training, evaluation, or latency scripts: read [references/training-scripts.md](references/training-scripts.md).
- Designing a safe preflight, one-batch smoke, metric interpretation, or checkpoint/evaluation handoff: read [references/evaluation-and-training.md](references/evaluation-and-training.md).
- Label validation, shape/class mismatches, vocab failures, DDP/GPU errors, DataLoader collation, synthetic font issues, or metrics returning `None`: read [references/troubleshooting.md](references/troubleshooting.md).
- If the user asks how to load trained weights into OCR/KIE/table/layout inference, route to the sibling model/customization and core OCR/KIE skills after completing the training/evaluation handoff.

## Safe local helper

Use the bundled validator before any custom-data training run:

```bash
python scripts/validate_doctr_labels.py --task detection --dataset-root DATASET_ROOT
python scripts/validate_doctr_labels.py --task recognition --dataset-root DATASET_ROOT --warn-spaces
python scripts/validate_doctr_labels.py --task layout --dataset-root DATASET_ROOT
python scripts/validate_doctr_labels.py --task table --dataset-root DATASET_ROOT
python scripts/validate_doctr_labels.py --task ocr --dataset-root DATASET_ROOT
```

The helper reads local JSON and checks local image existence only. It never trains, downloads, benchmarks, or imports heavyweight model code.

## Operating guardrails

1. Determine the task family first: detection, recognition, OCR/KIE-style detection, layout, table structure, character classification, or orientation classification.
2. Validate dataset layout and JSON shape before invoking docTR dataset classes.
3. For local training, require train and validation roots; for built-in training, use built-in dataset arguments instead of local paths. Do not mix local path and built-in dataset arguments for the same split.
4. For recognition, confirm the vocabulary before training or evaluating. Default examples often use the French vocab; custom multilingual labels need a compatible `VOCABS` entry or explicit model vocab.
5. For rotated geometry, keep the `use_polygons` / `--rotation` / `--eval-straight` choices consistent between dataset, training, and metrics.
6. For batching, pass the dataset `collate_fn` to the framework DataLoader because targets have variable-size dictionaries, arrays, strings, or table structures.
7. For DDP, use `torchrun`, let it set `LOCAL_RANK`, and choose a backend compatible with the visible hardware. `nccl` is CUDA-oriented; CPU or non-CUDA environments need a different backend or single-process execution.
