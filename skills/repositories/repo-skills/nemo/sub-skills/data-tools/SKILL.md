---
name: data-tools
description: "Use for NeMo Speech data preparation, JSON manifests, Lhotse and
  tarred datasets, duration bins, dataset weights, tokenizers, evaluation
  utilities, CTC segmentation, checkpoint utilities, and safe data validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data Tools

Use this sub-skill for shared NeMo Speech data preparation and utility work: JSONL manifests, Lhotse `input_cfg` planning, CutSet/Shar inputs, tarred dataset conversion, duration-bin and dataset-weight estimation, tokenizer preparation, ASR evaluator data contracts, CTC segmentation catalogs, speech data explorer/simulator planning, checkpoint utilities, and customization dataset preparation.

Route model-specific training, decoding, inference, or architecture work to sibling sub-skills such as `../asr/SKILL.md`, `../audio/SKILL.md`, or `../speechlm2/SKILL.md` when those are the primary goal. Route repository contribution policy, linting, and test strategy to a repo-development sub-skill when present.

## Start Here

1. Read `references/data-formats.md` before creating or validating NeMo manifests, Lhotse `input_cfg`, tokenizer corpora, ASR evaluator inputs, or customization JSONL.
2. Read `references/lhotse-and-tarred-data.md` before enabling Lhotse, estimating duration bins, mixing datasets, converting to tarred data, or planning Shar/CutSet inputs.
3. Read `references/tool-catalog.md` before using NeMo data utility scripts, tokenizers, checkpoint averaging, ASR evaluator, CTC segmentation, Speech Data Explorer, Speech Data Simulator, or customization dataset prep.
4. Read `references/troubleshooting.md` when imports, optional dependencies, CUDA/backends, Hydra overrides, manifest schemas, tar shard alignment, tokenizer generation, or long data workflows fail.

## Safe Bundled Tool

- `scripts/validate_manifest.py` validates JSONL manifests without importing NeMo, downloading data, opening audio contents by default, training, starting servers, or writing outputs.
- From this sub-skill directory, run it before long data jobs: `python scripts/validate_manifest.py manifest.jsonl --required audio_filepath duration text --min-duration 0.1 --max-duration 30 --summary`.
- Use `--check-files` only when local audio paths are expected to exist and file-existence checks are safe; omit it for tarred manifests, remote URIs, object-store paths, and manifests with audio filenames inside tar archives.

## Evidence Base

This sub-skill distills repository evidence from `docs/source/dataloaders.rst`, `docs/source/tools/*.rst`, `docs/source/common/data.rst`, `scripts/speech_recognition/*.py`, `scripts/tokenizers/*.py`, `scripts/dataset_processing/**`, `scripts/checkpoint_averaging/**`, `tools/asr_evaluator/**`, `tools/ctc_segmentation/**`, `tools/speech_data_explorer/**`, `tools/speech_data_simulator/**`, `tools/customization_dataset_preparation/**`, `tests/collections/common/test_lhotse_*`, and customization dataset preparation tests. Runtime guidance is self-contained; do not require future agents to reopen those source files or run original checkout scripts.
