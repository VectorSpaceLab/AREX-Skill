---
name: open-flamingo
description: "Use OpenFlamingo for vision-language model initialization,
  image-conditioned generation, distributed training, benchmark evaluation,
  RICES, MMC4/WebDataset conversion, and VQA-style result preparation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# OpenFlamingo repo skill

Use this skill when a task involves the OpenFlamingo (`open_flamingo`) package, Flamingo-style vision-language models, OpenCLIP vision encoders plus causal language models, interleaved image/text prompts, training on LAION/MMC4, benchmark evaluation, RICES feature caches, or OpenFlamingo data-preparation utilities.

Do **not** treat this skill as proof that a full model, dataset, or benchmark run already succeeded. Full generation, training, RICES, and evaluation require caller-provided checkpoints, datasets, cache/network permission, hardware, and time budget. The bundled scripts are safe preflight helpers and command builders unless the user explicitly asks to execute a generated command.

## Install and environment preflight

1. Install the package for the intended workflow:
   - model usage: `pip install open-flamingo`
   - training: install the package with training requirements
   - evaluation: install the package with evaluation requirements and ensure `scikit-learn` is present
2. Read [model zoo and compatibility](references/model-zoo-and-compatibility.md) before selecting released checkpoints, dependency pins, or offline cache behavior.
3. Run [`scripts/check_open_flamingo_env.py`](scripts/check_open_flamingo_env.py) for a safe import/signature/entrypoint check. It does not instantiate models or download assets.
4. If package layout or dependency versions differ substantially from [repo provenance](references/repo-provenance.md), refresh this skill before relying on detailed commands.

## Route by task

| User task | Read this |
|---|---|
| Initialize `create_model_and_transforms`, load checkpoints, prepare `<image>` prompts, run `forward()`/`generate()`, or debug `vision_x` and media cache behavior | [model-usage](sub-skills/model-usage/SKILL.md) |
| Build or troubleshoot OpenFlamingo training/fine-tuning commands, DDP/FSDP, LAION/MMC4 shard inputs, checkpoints, precision, or W&B | [training](sub-skills/training/SKILL.md) |
| Configure benchmark evaluation, supported dataset paths, `EvalModel`, metrics, result JSON, or RICES feature caches | [evaluation](sub-skills/evaluation/SKILL.md) |
| Convert/validate MMC4/WebDataset data, check LAION/MMC4 schemas, or fill VQAv2/VizWiz test-dev result files | [data-preparation](sub-skills/data-preparation/SKILL.md) |
| Diagnose install/import/dependency/cache/backend problems before choosing a workflow | [cross-cutting troubleshooting](references/troubleshooting.md) |

## High-value identifiers

- Public import: `from open_flamingo import create_model_and_transforms, Flamingo`
- Package version in this snapshot: `open_flamingo` 2.0.1
- Core model API: `create_model_and_transforms(...) -> (model, image_processor, tokenizer)`
- Special tokens: `<image>` and `<|endofchunk|>`
- Model media tensor: `vision_x` shaped `B x T_img x F x C x H x W`; OpenFlamingo supports `F=1`
- Training data families: LAION image/text WebDataset shards and MMC4 interleaved JSON/base64 WebDataset shards
- Evaluation families: COCO, Flickr30K, VQAv2, OK-VQA, TextVQA, VizWiz, ImageNet, Hateful Memes

## Safe helpers bundled with this skill

- [`scripts/check_open_flamingo_env.py`](scripts/check_open_flamingo_env.py): import/version/signature and packaged-entrypoint preflight.
- [`sub-skills/model-usage/scripts/validate_generation_inputs.py`](sub-skills/model-usage/scripts/validate_generation_inputs.py): validate prompt token counts and `vision_x` dimensions without imports or downloads.
- [`sub-skills/training/scripts/build_train_command.py`](sub-skills/training/scripts/build_train_command.py): print a validated `torchrun` command targeting the bundled training wrapper; never runs training.
- [`sub-skills/evaluation/scripts/build_eval_command.py`](sub-skills/evaluation/scripts/build_eval_command.py): print validated evaluation or RICES-cache commands targeting bundled wrappers; never runs evaluation.
- [`sub-skills/data-preparation/scripts/validate_open_flamingo_data.py`](sub-skills/data-preparation/scripts/validate_open_flamingo_data.py): bounded checks for MMC4 JSON, VQA predictions, and WebDataset path patterns.
- [`sub-skills/data-preparation/scripts/convert_mmc4_to_wds.py`](sub-skills/data-preparation/scripts/convert_mmc4_to_wds.py): standalone MMC4 ZIP/image-directory to WebDataset converter with safer validation.
- [`sub-skills/data-preparation/scripts/fill_vqa_testdev_results.py`](sub-skills/data-preparation/scripts/fill_vqa_testdev_results.py): standalone VQAv2/VizWiz result filler.

## Workflow guardrails

- Do not hand-run full training/evaluation/generation until the user provides local data/checkpoints or authorizes downloads and runtime cost.
- Prefer local cache paths and `use_local_files=True` for offline model initialization tasks.
- For evaluation, install `requirements-eval.txt` or add `scikit-learn` if `evaluate.py` fails on `sklearn.metrics`.
- If PyTorch imports but Transformers says PyTorch is unavailable, check the torch/Transformers compatibility note in [model zoo and compatibility](references/model-zoo-and-compatibility.md).
- Use the bundled training/evaluation wrappers instead of checkout-relative script paths; they locate the installed package and fix OpenFlamingo's local import quirks.
- For VQA test-dev submissions, local accuracy may be unavailable without private annotations; use `data-preparation` to format complete submission files.

## Provenance and routing metadata

- Read [repo provenance](references/repo-provenance.md) when checking staleness or before refreshing the skill.
- `references/repo-routing-metadata.json` records the structured router placement for managed repo-skill import. This production run intentionally did **not** import the skill because the user requested no import.
