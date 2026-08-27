---
name: naflex-generative
description: "Use open_clip NaFlex variable-resolution image/audio pipelines and
  NaFlex GenLIP/GenLAP generative workflows safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# NaFlex Generative

Use this sub-skill when the task mentions NaFlex, `--use-naflex`, variable image resolution/aspect batching, variable-duration NaFlex audio, `NaFlexDataConfig`, patch dictionaries, NaFlex CLIP/CLAP, `naflexgenlip*`, `naflexgenlap*`, generative image/audio captioning, GenLIP zero-shot scoring, attentive probes, or caption-token budget planning.

## Route First

- For ordinary dense CLIP image/text inference, preprocessing, and cosine zero-shot on standard CLIP models, use `../model-inference/SKILL.md`.
- For generic training loop, checkpoint, distributed, optimizer, or resume mechanics, use `../training/SKILL.md` and return here only for NaFlex-specific batches, schedules, or loss scaling.
- For audio zero-shot dataset evaluation with contrastive CLAP/NaFlexCLAP, use `../audio-clap/SKILL.md`.
- For retrieval metrics, model conversion/export, or Hugging Face publishing, use `../evaluation-conversion/SKILL.md`.

## What This Covers

- NaFlex training/eval flags: `--use-naflex`, `--force-naflex-vision`, `--naflex-patch-sizes`, `--naflex-seq-lens`, token budgets, batch divisors, pad multiples, and `--naflex-loss-scale`.
- `NaFlexDataConfig`, `create_naflex_data_config_from_args`, `create_naflex_eval_transform`, `NaFlexBatcher`, WebDataset/CSV NaFlex wiring, and dict batch schemas.
- Image and audio patch dictionaries with `patches`, `patch_coord`, `patch_valid`, and optional scheduled `seq_len`.
- Dense-to-NaFlex conversion paths via `force_naflex_vision` for compatible native ViT and timm EVA/ViT towers.
- GenLIP/GenLAP differences from contrastive CLIP/CLAP: caption LM loss, prefix-LM masks, tiktoken text, and generative scoring/probe caveats.
- Safe bundled helpers: `scripts/naflex_config_report.py` for config validation and `scripts/genlip_scoring_args.py` for cost/planning reports without loading checkpoints or reading datasets.

## Fast Workflow

1. Decide whether the user has a contrastive NaFlex CLIP/CLAP task or a generative GenLIP/GenLAP task; GenLIP/GenLAP cannot be evaluated with `encode_text` cosine similarity.
2. Read `references/naflex-data.md` for parser flags, config defaults, dict schemas, token-budget scheduling, variable text, and eval transform requirements.
3. Read `references/generative-workflows.md` for GenLIP/GenLAP model/task behavior, generative zero-shot scoring, attentive probes, and caption-stat workflows.
4. Read `references/conversion.md` before using `--force-naflex-vision` or loading dense/timm checkpoints into NaFlex vision towers.
5. Read `references/troubleshooting.md` when NaFlex imports, eval transforms, schedules, patch dicts, variable text, or GenLIP scoring fail.
6. Run `python scripts/naflex_config_report.py --patch-sizes 16 --seq-lens 128 256 --max-tokens-per-batch 16384` or `python scripts/genlip_scoring_args.py --templates simple --num-images 200 --score-batch 512` to sanity-check user-supplied settings before expensive runs.

## Key Rules

- `--use-naflex` enables the NaFlex data pipeline and implies `--force-naflex-vision` for ordinary image models, but GenLIP, GenLAP, and NaFlexCLAP set `use_naflex` without forcing image-tower conversion.
- NaFlex eval requires a NaFlex transform factory: pass `aug_cfg={"use_timm": True, "naflex": True}` or use CLI `--use-naflex`; otherwise `create_naflex_eval_transform` rejects the transform.
- Image NaFlex batches are dicts, not dense tensors: `image["patches"]`, `image["patch_coord"]`, `image["patch_valid"]`, plus scheduler `image["seq_len"]` in train batches.
- Audio NaFlex batches use the same patch keys under `audio`; `patch_coord` is `(freq, time)`, with full-height strips treated as 1-D time RoPE for GenLAP.
- GenLIP/GenLAP train with autoregressive caption loss over `[media_patches ; caption_tokens]`; use `text_valid` for variable/padded text and do not expect contrastive `image_features @ text_features` semantics.
- `--naflex-loss-scale` only affects NaFlex dict batches and scales by actual local batch size relative to `--batch-size`: `none`, `linear`, or `sqrt`.

## Evidence Anchors

This sub-skill distills behavior from NaFlex config/data modules, conversion modules, GenLIP/GenLAP modules/tasks, GenLIP research probe scripts, and NaFlex/GenLIP/GenLAP tests. It is self-contained for runtime use; reopen repository source only when refreshing the skill for new code changes.
