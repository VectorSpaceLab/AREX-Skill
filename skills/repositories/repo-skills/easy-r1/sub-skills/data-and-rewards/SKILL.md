---
name: data-and-rewards
description: "Prepare EasyR1 dataset rows, prompt templates, and
  AutoRewardManager-compatible reward functions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# data-and-rewards

Use this sub-skill when a task is about EasyR1 input data, multimodal prompt formatting, or rule-based reward functions. It is a routing entry point; load the linked references for the concrete contracts and validation steps.

## Use this for

- Preparing text, image-text, multi-image, text-image mixed, or video dataset rows for EasyR1.
- Choosing and adapting Jinja prompt templates for math, R1-V, DAPO, and Android GUI-style tasks.
- Writing reward functions that EasyR1's `AutoRewardManager` can load through `worker.reward.reward_function`.
- Checking batch versus sequential reward functions and the required `overall` score key.
- Planning Android GUI number-game data/reward work without assuming a runnable device, game service, or VLM endpoint.

## Route elsewhere

- Training launch overrides, Ray/FSDP/vLLM sizing, KL/loss algorithm selection, and full job commands belong to the sibling `training-workflows` sub-skill.
- Low-level `DataProto` construction, tensor/non-tensor batch debugging, and padding APIs belong to the sibling `core-apis` sub-skill.
- Checkpoint merging and Hugging Face export belong to the sibling `checkpoint-export` sub-skill.

## Files to load

- [Data and reward formats](references/data-reward-formats.md): concrete dataset columns, prompt template patterns, reward signatures, score keys, and validation commands.
- [Android GUI cookbook](references/android-gui-cookbook.md): reference-only prerequisites, data shape, prompt, and reward design for the number-game workflow.
- [Troubleshooting](references/troubleshooting.md): common failures for datasets, templates, reward imports, score dictionaries, mixed media rows, remote datasets, and backend limits.
- [Reward smoke script](scripts/easyr1_reward_smoke.py): deterministic local checks for built-in reward contracts, mixed row guards, and optional custom `module.py:function` validation.

## Fast path

1. Identify the modality: text-only, image-text, multi-image, text-image mixed, or video.
2. Normalize rows to include the configured prompt and answer columns; use media lists only when the prompt contains the matching placeholder.
3. Select or write a Jinja prompt template that renders a single `content` variable and leaves chat-template wrapping to the tokenizer or processor.
4. Write a reward function with explicit `REWARD_TYPE = "batch"` or `REWARD_TYPE = "sequential"`; every returned score dictionary must contain numeric `overall`.
5. Run the bundled smoke script before launching training.

Full EasyR1 training is a CUDA workflow that also needs the full flash-attn/vLLM/Ray runtime. CPU/API smoke checks validate data and reward contracts only; they do not prove that a full training job will run.
