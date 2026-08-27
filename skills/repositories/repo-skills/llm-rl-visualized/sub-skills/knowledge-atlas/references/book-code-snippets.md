# Book code snippets

All snippets in `src/code_from_book.md` are educational orientation only. They explain concepts and wiring patterns, not production-ready implementations.

## What each snippet family shows

| Topic | What it shows | What to tell the user | Caveat |
| --- | --- | --- | --- |
| LoRA | low-rank A/B factors, frozen base weights, scaling | the core idea of parameter-efficient adaptation | not a drop-in module for every framework |
| jq SFT cleaning | JSON to JSONL, null filtering, field rename, length filtering, sampling | a simple data-shaping pipeline for SFT corpora | shell tools and field names must be adapted |
| DPO | chosen/rejected pairs, policy/reference logprobs, beta, log-sigmoid loss | the preference-optimization skeleton | token gathering and masking depend on the tokenizer and framework |
| GAE | reverse-time advantage recursion from rewards and values | the advantage estimator used by PPO-style methods | terminal handling and bootstrapping matter |
| PPO / RLHF | actor, critic, reference model, reward model, KL penalty, clip objective, entropy | the alignment-training loop skeleton | shapes, batching, and reward plumbing are simplified |

## How to talk about the snippets
- If the user asks whether a snippet is production code, answer no.
- If the user asks what a snippet proves, explain the concept it isolates.
- If the user asks to port the snippet to a framework, say the sketch still needs framework-specific masks, batching, device handling, dtype handling, and logging.
- If the user asks whether a snippet is enough to train a model, answer that it is a conceptual orientation, not a complete trainer.

## Fast routing hints
- `LoRA` questions usually belong with SFT or PEFT discussions.
- `DPO` questions usually belong with chosen/rejected pairs and preference optimization.
- `GAE` questions usually belong with policy optimization and advantage estimation.
- `PPO` questions usually belong with RLHF, actor-critic, or policy-gradient style training.
- `jq` questions usually belong with SFT data preprocessing and cleaning.

## Provenance note
This file was distilled from `src/code_from_book.md`.
