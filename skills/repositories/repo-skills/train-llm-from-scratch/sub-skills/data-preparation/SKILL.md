---
name: data-preparation
description: "Prepare and validate flat pretraining, packed SFT, preference, and
  RL prompt datasets for train-llm-from-scratch."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data Preparation Router

Use this sub-skill when a task is about building, inspecting, validating, or
triaging datasets for this repository's LLM pipeline. Keep training, checkpoint,
evaluation, chat, and UI work routed to the sibling skills listed below.

## Decide The Dataset Shape First

1. **Base pretraining text** -> flat HDF5 `tokens` array. Use for next-token
   base-model pretraining.
2. **SFT/instruction data** -> packed HDF5 with aligned `tokens` and
   `loss_mask`. Use for assistant-only supervised fine-tuning.
3. **Preference data** -> JSONL rows with `prompt`, `chosen`, and `rejected`.
   Use for reward-model training and DPO/ORPO/KTO.
4. **RL prompts** -> JSONL rows with `prompt` and numeric-or-null `gold`; the
   arithmetic curriculum is the same schema. Use for PPO and GRPO/RLVR.

Read [`references/data-formats.md`](references/data-formats.md) for exact schema,
mask, tokenizer, and data-loader contracts before accepting a user-provided file.
Read [`references/workflows.md`](references/workflows.md) for distilled command
recipes and safe small-data checks. Read
[`references/troubleshooting.md`](references/troubleshooting.md) when validation
fails or data generation is blocked by dependencies, cache, network, or context
limits.

## Safe Validators Bundled Here

These scripts do not download data, train models, modify input files, or require a
repository checkout. Run them before launching any stage that consumes the data.

- `scripts/inspect_h5_tokens.py` — inspect a flat pretraining HDF5 `tokens`
  dataset: shape, dtype, min/max, EOT count, and optional head decode.
- `scripts/validate_sft_h5.py` — validate packed SFT HDF5 `tokens` and
  `loss_mask` schema, binary mask, token range, and trained-token fraction.
- `scripts/validate_preference_jsonl.py` — validate preference JSONL rows and
  reject missing/empty fields or degenerate `chosen == rejected` pairs.
- `scripts/validate_rl_prompts_jsonl.py` — validate prompt/gold JSONL rows,
  numeric/null gold policy, and optional arithmetic-curriculum consistency.

## Routing Boundaries

- Base model training, DDP/bf16 pretraining, memory flags, checkpointing, and
  resume behavior -> [`../model-pretraining/SKILL.md`](../model-pretraining/SKILL.md).
- SFT, reward model, DPO/ORPO/KTO, PPO, GRPO, rollout, KL, and optimizer logic ->
  [`../post-training-rlhf/SKILL.md`](../post-training-rlhf/SKILL.md).
- GSM8K scoring, answer parsing during evaluation, stage tables, generation, and
  chat -> [`../evaluation-chat/SKILL.md`](../evaluation-chat/SKILL.md).
- JSON config editing, CLI override precedence, smoke configs, and Streamlit UI ->
  [`../configuration-ui/SKILL.md`](../configuration-ui/SKILL.md).

## Operating Checklist

1. Ask which downstream stage the data will feed and record the intended
   context length, data directory, cache policy, and whether network access is
   available.
2. Pick the matching dataset shape from this router; do not mix HDF5 pretraining
   tokens, packed SFT rows, preference pairs, and RL prompts.
3. If generating public data, use the distilled command recipe in
   [`references/workflows.md`](references/workflows.md), starting with a tiny
   limit when practical.
4. Validate the resulting file with the bundled script for that shape.
5. If validation fails, stop before training and use
   [`references/troubleshooting.md`](references/troubleshooting.md) to identify
   whether the fix is regeneration, path creation, cache/network repair, context
   length change, or schema cleanup.
