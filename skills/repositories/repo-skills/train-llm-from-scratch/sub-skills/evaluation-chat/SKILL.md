---
name: evaluation-chat
description: "Guide GSM8K evaluation, answer verification, and checkpoint chat
  or raw inference for train-llm-from-scratch."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# evaluation-chat

Use this sub-skill when a future agent needs to evaluate or talk to checkpoints from the `train-llm-from-scratch` pipeline without re-opening source files.

## Use this for

- Building GSM8K evaluation commands for one checkpoint or a Base → SFT → DPO → PPO → GRPO stage table.
- Explaining greedy GSM8K accuracy, sample dumps, JSONL append files, and table rendering.
- Loading any stage checkpoint for inference and deciding chat-template mode versus raw continuation.
- Choosing chat sampling controls: greedy, temperature, top-p, top-k, max-new-token budget, and CPU/CUDA device.
- Explaining answer extraction, GSM8K correctness checks, and the verifier reward's small format bonus.

## Route elsewhere

- Training or resuming base checkpoints: `../model-pretraining/SKILL.md`.
- SFT, reward model, DPO/ORPO/KTO, PPO, or GRPO training: `../post-training-rlhf/SKILL.md`.
- Dataset preparation or validation before evaluation: `../data-preparation/SKILL.md`.
- Streamlit control-panel settings and jobs: `../configuration-ui/SKILL.md`.

## First decisions to make

1. Is the task evaluation, chat, or answer-format diagnosis?
2. Which checkpoint stage is being used: base/pretrained, SFT, DPO, PPO, GRPO, or reward checkpoint?
3. Is GSM8K data already locally available or is network/cache access allowed?
4. Should the output be deterministic (`--greedy`, required for headline eval) or sampled chat?
5. Which device is valid for the checkpoint and installed torch build: `cuda` or `cpu`?

## Reference map

- Read `references/evaluation.md` for evaluator flags, GSM8K scoring, stage tables, sample rows, and verifier behavior.
- Read `references/inference.md` for checkpoint loading, chat versus raw prompting, decoding, and chat CLI flags.
- Read `references/troubleshooting.md` when commands fail or outputs look malformed.

## Bundled helpers

- `scripts/build_eval_command.py` prints dry-run evaluation/table commands. It never loads a model or touches datasets.
- `scripts/build_chat_command.py` prints dry-run one-shot or REPL chat commands. It never loads a checkpoint.
- `scripts/check_answer_format.py` parses text with the same `<answer>`, `####`, and last-number priority used by the verifier family; it can optionally compare a gold number and estimate verifier reward.

Prefer the helpers when the user asks for commands. They make command construction explicit while avoiding accidental training, downloads, or checkpoint loads during planning.

## Operating guardrails

- Do not launch training from this sub-skill.
- Do not assume network access for GSM8K; confirm cache/data availability before running real evaluation.
- Use `--raw` for a base checkpoint; use default chat mode for instruction/post-training checkpoints.
- Use greedy decoding for comparable GSM8K numbers. Sampling is for interactive or qualitative chat, not the stage table.
- Do not treat the small verifier format bonus as proof of correctness; accuracy depends on the parsed numeric answer matching gold.
