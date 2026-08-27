---
name: donut
description: "Use Donut for OCR-free document understanding, checkpoint
  inference, fine-tuning, evaluation, and SynthDoG synthetic document
  generation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Donut

Use this repo skill when the task involves NAVER/ClovaAI Donut: OCR-free document understanding with a Swin encoder and BART-like decoder, plus SynthDoG synthetic document generation. This skill is self-contained; do not reopen the original checkout for routine Donut usage.

## Route by task

| User intent | Read or run |
| --- | --- |
| Load a Donut checkpoint, run one-image prediction, compare prompts, or start the Gradio demo | [`sub-skills/inference/SKILL.md`](sub-skills/inference/SKILL.md) |
| Fine-tune, validate dataset JSONL, evaluate a checkpoint, read metrics, or debug configs/checkpoints | [`sub-skills/training/SKILL.md`](sub-skills/training/SKILL.md) |
| Generate synthetic document images, render SynthDoG configs, or adapt resources/fonts/corpora | [`sub-skills/synthdog/SKILL.md`](sub-skills/synthdog/SKILL.md) |
| Inspect public package APIs, signatures, token helpers, and object relationships | [`references/api-reference.md`](references/api-reference.md) |
| Decide which bundled workflow helper or sub-skill owns a request | [`references/workflow-map.md`](references/workflow-map.md) |
| Diagnose install/import, Hugging Face, CUDA, Gradio, dataset, or SynthDoG dependency failures | [`references/troubleshooting.md`](references/troubleshooting.md) |
| Check source baseline, commit, version, and refresh triggers | [`references/repo-provenance.md`](references/repo-provenance.md) |

## Fast start

1. Install a Donut-capable Python environment. For inference only, `pip install donut-python` plus a compatible PyTorch build is the starting point. Training needs CUDA-capable PyTorch. SynthDoG generation also needs `synthtiger` and its image/text dependencies.
2. Smoke-check the environment without the source repo:
   ```bash
   python scripts/runtime_smoke.py
   python scripts/runtime_smoke.py --check all --require-cuda  # when training and SynthDoG are in scope
   ```
3. Route to a sub-skill before giving detailed commands. Each sub-skill owns its own scripts and troubleshooting notes.

## Core facts to preserve

- Package distribution: `donut-python`; import module: `donut`.
- Public exports include `DonutConfig`, `DonutModel`, `DonutDataset`, `JSONParseEvaluator`, `load_json`, and `save_json`.
- `DonutModel.from_pretrained(...)` loads local or Hugging Face checkpoints and requests the Donut repositories' `official` revision.
- `DonutModel.inference(...)` returns a dictionary with a `predictions` list; parsed JSON is the default output.
- Dataset rows use `file_name` plus a JSON-encoded `ground_truth` string containing either `gt_parse` or `gt_parses`.
- Training is GPU-oriented in the original scripts; do not promise CPU training equivalence.
- No model weights, datasets, or large SynthDoG assets are bundled in this skill. Users must provide checkpoints, images, datasets, and SynthDoG resources.

## Bundled helpers

- [`scripts/runtime_smoke.py`](scripts/runtime_smoke.py): cross-workflow environment/API smoke check.
- [`sub-skills/inference/scripts/run_inference.py`](sub-skills/inference/scripts/run_inference.py): single-image inference and prompt comparison.
- [`sub-skills/inference/scripts/launch_demo.py`](sub-skills/inference/scripts/launch_demo.py): Gradio demo launcher.
- [`sub-skills/training/scripts/train_donut.py`](sub-skills/training/scripts/train_donut.py): bundled CUDA-oriented trainer entry point.
- [`sub-skills/training/scripts/check_training_config.py`](sub-skills/training/scripts/check_training_config.py): config and metadata validator.
- [`sub-skills/training/scripts/evaluate_dataset.py`](sub-skills/training/scripts/evaluate_dataset.py): local/HF dataset evaluation helper and validation-only mode.
- [`sub-skills/training/references/configs/`](sub-skills/training/references/configs/): bundled CORD, DocVQA, RVL-CDIP, and TrainTicket config examples.
- [`sub-skills/synthdog/scripts/render_config.py`](sub-skills/synthdog/scripts/render_config.py): render bundled SynthDoG placeholder configs for external resources.
- [`sub-skills/synthdog/scripts/template.py`](sub-skills/synthdog/scripts/template.py): bundled SynthDoG template used by `synthtiger`.

## Boundaries

Use Donut for OCR-free document-image understanding, classification, extraction, visual QA, and synthetic-document pretraining data generation. Do not use this skill for generic PDF parsing, OCR engines, RAG chunking, non-document computer vision models, or unrelated Transformers training unless Donut APIs, checkpoints, config files, errors, or data formats are central to the request.
