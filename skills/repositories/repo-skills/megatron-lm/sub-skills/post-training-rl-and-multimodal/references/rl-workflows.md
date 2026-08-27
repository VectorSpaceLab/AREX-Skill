# Megatron RL and GRPO workflows

## Architecture

Megatron RL separates:

- agents/environments: receive an inference handle and return experience/rewards;
- trainer/evaluator: controls rollout generation and training/evaluation;
- inference backend: Megatron, OpenAI-compatible, or Hugging Face generation path;
- policy optimization: GRPO/RL loss, log probabilities, ratios, KL, entropy, and truncation metrics.

## Inputs to resolve

- policy/model checkpoint and tokenizer
- reward/environment config and data source
- inference backend and endpoint/handle
- rollout batch/sequence/packing settings
- TP/PP/CP/EP/DP topology
- checkpoint save/load and restart semantics
- optional external service credentials

## Validation order

1. Validate config/schema and model/tokenizer compatibility.
2. Run a tiny rollout/reward check or a parser/import smoke.
3. Verify generated sequence lengths and packed-data metadata.
4. Check logprob/reward/KL/ratio metrics are finite.
5. Run a bounded training step before large rollout counts.

## Common metrics

RL loss paths may report `lm loss`, KL terms, policy ratios, entropy, truncation counts, and token counts. When debugging, distinguish NaN/spiky-loss checks from ordinary reward variance.

## Hardware and dependency boundary

Megatron RL is research-oriented and GPU-heavy. CPU parser checks do not validate rollout/training execution. `train_rl.py --help` imports RL modules before argparse help, so a minimal environment may fail first on optional/test-group dependencies such as `pydantic`, `tensorboard`, or `wandb`; treat those as dependency diagnostics, not as proof that GRPO itself is broken. Use the install sub-skill for optional inference backend dependencies and the core sub-skill for topology.
