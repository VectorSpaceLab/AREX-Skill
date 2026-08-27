---
name: open-clip
description: "Route OpenCLIP model loading, inference, training, audio CLAP,
  NaFlex generative workflows, evaluation, checkpoint conversion, and package
  troubleshooting tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# OpenCLIP

Use this repo skill for OpenCLIP (`open_clip_torch`) tasks involving CLIP-style vision-language models, CoCa, CLAP audio-text models, NaFlex variable-resolution pipelines, GenLIP/GenLAP generative models, training commands, zero-shot evaluation, retrieval metrics, checkpoint conversion, and Hugging Face export planning.

## Start Here

- Install for inference with `pip install open_clip_torch`; install selected extras only when needed, such as `pip install 'open_clip_torch[training]'` for training/data utilities and `pip install 'open_clip_torch[audio]'` for CLAP audio workflows.
- Run `python scripts/check_open_clip_env.py` to confirm importability, package version, model registry access, and optional audio/training modules before deep troubleshooting.
- Read `references/repo-provenance.md` before refreshing or comparing this skill to a source checkout.
- Read `references/troubleshooting.md` for cross-cutting install, optional dependency, cache/download, torch/CUDA, and stale-skill issues.
- Read `references/source-script-map.md` when a user asks about bundled helpers or why original long-running scripts are not directly reproduced.

## Route By Task

| User intent | Read first | Why |
| --- | --- | --- |
| Load a model, choose `pretrained`, tokenize text, preprocess images, create embeddings, or inspect model config | `sub-skills/model-inference/SKILL.md` | Owns `create_model*`, `get_tokenizer`, transforms, pretrained tags, `hf-hub:`/`local-dir:`, CoCa inference, and no-download smoke checks. |
| Build or debug training commands, datasets, task wrappers, precision, FSDP, `torch.compile`, optimizer/scheduler, checkpoints, or parser defaults | `sub-skills/training/SKILL.md` | Owns `python -m open_clip_train.main`, dict batch contracts, CSV/WebDataset/synthetic data, task-era wrappers, and training-safe helper scripts. |
| Work with CLAP or NaFlexCLAP audio models, audio transforms, `webdataset-audio`, HF audio zero-shot, or HF CLAP checkpoint conversion | `sub-skills/audio-clap/SKILL.md` | Owns audio configs, audio dict shapes, audio zero-shot flags, optional audio extras, and CLAP conversion troubleshooting. |
| Use `--use-naflex`, variable image/audio token budgets, patch dictionaries, NaFlex conversion, GenLIP, GenLAP, generative scoring, or probe planning | `sub-skills/naflex-generative/SKILL.md` | Owns NaFlex data config, `patches`/`patch_coord`/`patch_valid`, GenLIP/GenLAP model differences, and expensive-script planning helpers. |
| Build zero-shot classifiers, ImageNet zero-shot routes, retrieval metrics, checkpoint key reports, state-dict conversion/export, or HF Hub push plans | `sub-skills/evaluation-conversion/SKILL.md` | Owns contrastive evaluation, retrieval chunking, checkpoint prefix/EMA diagnostics, conversion/export routing, and safe key-inspection helpers. |

## Common Decisions

- Use `model-inference` for ordinary CLIP/CoCa embedding tasks; use `evaluation-conversion` only when the task asks for classifier construction, retrieval metrics, checkpoint keys, conversion, or export.
- Use `audio-clap` for audio data and CLAP zero-shot; do not force ImageNet/image zero-shot workflows onto audio-only models.
- Use `naflex-generative` when images or audio are represented as patch dictionaries or when a GenLIP/GenLAP model lacks contrastive `encode_text` semantics.
- Use `training` for command construction and data validation; route model-family-specific NaFlex or audio details to the owning sub-skill.
- Treat pretrained downloads, Hugging Face datasets, checkpoint loading, probe training, and large training/evaluation runs as explicit user-authorized operations, not default smoke checks.

## Bundled Helpers

- `scripts/check_open_clip_env.py` verifies imports, package metadata, registry counts, optional audio/training imports, and selected torch backend facts without downloading weights.
- `sub-skills/model-inference/scripts/inference_smoke.py` creates a no-download model/tokenizer/preprocess smoke by default.
- `sub-skills/training/scripts/training_arg_report.py` reports parsed training defaults without building models, data loaders, or distributed process groups.
- `sub-skills/training/scripts/validate_csv_dataset.py` validates CSV/TSV path and caption columns without starting training.
- `sub-skills/audio-clap/scripts/audio_config_report.py` and `sub-skills/audio-clap/scripts/clap_zero_shot_args.py` inspect audio config and plan HF audio zero-shot flags without downloading datasets.
- `sub-skills/naflex-generative/scripts/naflex_config_report.py` and `sub-skills/naflex-generative/scripts/genlip_scoring_args.py` validate token-budget/generative scoring settings before expensive runs.
- `sub-skills/evaluation-conversion/scripts/zero_shot_classifier_smoke.py` and `sub-skills/evaluation-conversion/scripts/checkpoint_key_report.py` provide no-download classifier and checkpoint diagnostics.

## Guardrails

- Do not ask future agents to run OpenCLIP repository examples, tests, notebooks, or shell launchers as runtime instructions; use bundled helpers and references instead.
- Do not assume every optional dependency is installed. Training, audio, Hugging Face tokenizers, datasets, and backend features have separate dependencies and failure modes.
- Do not run download-prone pretrained/HF workflows unless the user explicitly allows network/cache access.
- Do not treat skipped native tests or heavyweight examples as passing; use the relevant helper and report safety limits.
- If the source repository commit, package version, public APIs, or major docs changed since `references/repo-provenance.md`, refresh this skill before relying on fine details.
