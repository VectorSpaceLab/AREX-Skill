---
name: data-preparation
description: "Prepare and validate OpenRLHF datasets for SFT, reward modeling,
  DPO, PPO/RL prompts, chat-template use, dataset mixing, packing-sensitive
  length checks, and VLM image placeholders before expensive training."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenRLHF Data Preparation

Use this sub-skill when the task is about dataset schemas, key mapping, chat-template choices, prompt/reward/preference records, tiny dry-run validation, or VLM image placeholder alignment for OpenRLHF.

## Route by Training Mode

- **SFT**: prepare prompt/response or multiturn chat records; see `references/data-formats.md#sft-records` and validate with `scripts/validate_openrlhf_dataset.py --mode sft`.
- **Reward model**: prepare chosen/rejected pairs, optional prompt prefixes, and optional margin values; see `references/data-formats.md#reward-model-records` and validate with `--mode rm`.
- **DPO**: prepare chosen/rejected preferences with optional shared prompt; see `references/data-formats.md#dpo-records` and validate with `--mode dpo`.
- **PPO/RL prompts**: prepare prompt-only records with optional labels and datasource fields; see `references/data-formats.md#ppo-and-rl-prompt-records` and validate with `--mode ppo`.
- **VLM prompts**: verify `<image>` placeholders line up with the configured image key before Ray/vLLM training; see `references/data-formats.md#vlm-image-prompts` and `references/troubleshooting.md#multimodal-image-mismatches`.

## Core Decisions

- Match CLI key flags (`--data.input_key`, `--data.output_key`, `--data.prompt_key`, `--data.chosen_key`, `--data.rejected_key`, `--data.label_key`, `--data.image_key`) to the actual record fields before launching training.
- Choose exactly one prompt formatting path: use `--data.apply_chat_template` for chat-message lists, or `--data.input_template` for plain string prompts.
- For SFT multiturn data, enable `--data.multiturn` only with `--data.apply_chat_template`, and put the full trajectory under `--data.input_key` rather than splitting assistant turns into `--data.output_key`.
- For mixed datasets, keep comma-separated `--data.dataset` and `--data.dataset_probs` counts aligned; probabilities are parsed as floats and must match the dataset count.
- Treat `--data.max_len`, prompt length, packing, ring attention, and VLM image counts as preflight risks; see `references/validation.md` before running expensive GPU jobs.

## Safe Local Validator

Run the bundled validator on tiny local JSON or JSONL samples without importing OpenRLHF, Ray, torch, datasets, or transformers:

```bash
python skills/openrlhf/sub-skills/data-preparation/scripts/validate_openrlhf_dataset.py \
  --mode sft \
  --input sample.jsonl \
  --input-key question \
  --output-key response \
  --max-samples 20
```

The validator checks required keys, null/empty values, chat-message shape, chosen/rejected confusion, dataset probability counts, rough length limits, and VLM placeholder/image alignment. It is a schema preflight, not a tokenizer-accurate training simulation.

## Boundaries

- For full SFT/RM/DPO training command construction, hand off to `supervised-preference-training` after data validates.
- For PPO/Ray/vLLM rollout setup, agent functions, or reward services, hand off to `rl-agent-training` after prompt data validates.
- For installation, CUDA, flash-attn, Ray, vLLM, DeepSpeed, checkpoint, and environment issues, hand off to `operations-and-utilities`.
