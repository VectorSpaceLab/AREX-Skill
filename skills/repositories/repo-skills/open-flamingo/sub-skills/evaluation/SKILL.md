---
name: "evaluation"
description: "Run and troubleshoot OpenFlamingo evaluation on supported
  captioning, VQA, and classification benchmarks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# evaluation

Use this sub-skill when you need to configure, launch-plan, or debug OpenFlamingo evaluation: selecting supported benchmark datasets, supplying `evaluate.py` model and data flags, using `EvalModel` prompt conventions, preparing or consuming RICES demonstration feature caches, and interpreting result files.

## Read first

- [CLI reference](references/cli-reference.md)
- [Dataset reference](references/dataset-reference.md)
- [Evaluation workflows](references/evaluation-workflows.md)
- [Troubleshooting](references/troubleshooting.md)
- [Safe evaluation command builder](scripts/build_eval_command.py)

## What this sub-skill covers

- Supported datasets and metrics:
  - COCO and Flickr30K captioning with CIDEr.
  - VQAv2, OK-VQA, TextVQA, and VizWiz VQA with VQA accuracy when annotations are supplied.
  - Hateful Memes classification with ROC AUC.
  - ImageNet classification with top-1 accuracy.
- OpenFlamingo `EvalModel` setup for checkpoint, language model, tokenizer, vision encoder, cross-attention interval, and precision.
- Zero-shot, few-shot, random-demonstration, and RICES-demonstration launch planning.
- Cached RICES feature naming and dataset-specific path requirements.
- Distributed evaluation, result JSON files, test-dev output behavior, and common import/dependency failures.

## Typical flow

1. Confirm the target datasets, splits, metric mode, checkpoint, language model, tokenizer, precision, and available devices.
2. Verify every selected dataset has the required image, question, annotation, or ImageNet root paths listed in [Dataset reference](references/dataset-reference.md).
3. For RICES, either provide a cache directory containing the expected dataset `.pkl` files or render a cache command first.
4. Render a command with `scripts/build_eval_command.py`; inspect the printed command before running it in a prepared OpenFlamingo environment.
5. For full benchmark runs, use a real checkpoint, complete datasets, and a distributed launch; for smoke checks, set `--num_samples` to a small value.
6. Read the aggregate result JSON and any VQA test-dev files emitted by the rank-0 process.

## Guardrails

- The bundled command builder only prints commands; it never downloads checkpoints, prepares datasets, or launches evaluation.
- Do not claim benchmark execution unless the printed command was actually run with the required data, checkpoint, and hardware.
- Full benchmark evaluation is checkpoint-, data-, and accelerator-dependent; prefer bounded smoke checks before committing GPU time.
- Treat test-dev VQA output as a submission artifact, not a locally computed accuracy, when public annotations are absent.
- Keep RICES cache files matched to the same dataset split and CLIP vision encoder used to create them.
