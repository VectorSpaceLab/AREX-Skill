---
name: data-and-rewards
description: "Prepare and validate TRL datasets, chat templates, multimodal
  messages, tool-call data, packing, and built-in reward functions before
  trainer construction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TRL Data and Rewards

Use this sub-skill when a task is about shaping examples before they reach a TRL trainer, validating dataset columns, applying or cloning chat templates, preparing multimodal or tool-call messages, packing text datasets, or choosing built-in reward functions.

## Route by task

- Dataset schema or conversion: start with [Data Formats](references/data-formats.md) to identify standard vs conversational rows and task-specific columns.
- API behavior: use [API Reference](references/api-reference.md) for `trl.data_utils` and `trl.chat_template_utils` helpers such as `maybe_apply_chat_template`, `maybe_extract_prompt`, `unpair_preference_dataset`, `pack_dataset`, and `parse_response`.
- Reward selection: use [Reward Functions](references/reward-functions.md) for GRPO/RLOO-compatible built-ins and the `None`-means-skip behavior of math rewards.
- Data validation: run `scripts/validate_trl_dataset.py --help`, then validate local JSONL rows with `--task sft`, `--task dpo`, `--task reward`, or `--task grpo` before trainer setup.
- Failures: use [Troubleshooting](references/troubleshooting.md) for missing columns, implicit prompts, invalid chat templates, multimodal image mismatches, tool-call parsing, and optional reward dependencies.

## Boundaries

- This sub-skill covers dataset shape, preprocessing utilities, chat template preparation, multimodal/tool-call message shape, packing, and reward callable interfaces.
- For trainer class construction, callbacks, generation loops, or model/reference model setup, route to `core-training`.
- For YAML/CLI field names and launch recipes, route to `cli-and-configs`.
- For environment and tool-loop training behavior, route to `experimental-and-environments`.

## Safe workflow

1. Classify the row type and format before changing code: standard text strings and conversational message lists have different valid columns.
2. Normalize only when needed: use `maybe_*` helpers when rows may already be standard, and explicit helpers when conversion is required.
3. Apply chat templates only to conversational examples and pass `tools` only when the model/template supports tool calling.
4. Validate reward functions outside training with tiny in-memory completions or token-id lists; reward callables should accept extra trainer kwargs.
5. Run the bundled validator on JSONL samples before constructing trainers so schema issues surface without downloads or training.
