---
name: llm-fine-tuning
description: "Use AgileRL LLM fine-tuning and post-training workflows for GRPO,
  CISPO, GSPO, DPO, SFT, LLM PPO/REINFORCE, vLLM, DeepSpeed, and optional LLM
  dependencies."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AgileRL LLM Fine-Tuning

Use this sub-skill when the task involves AgileRL LLM post-training or fine-tuning: `GRPO`, `CISPO`, `GSPO`, LLM PPO, LLM REINFORCE, `SFT`, `DPO`, reasoning/preference/multiturn/SFT trainers, AgileRL LLM envs, vLLM rollout backends, DeepSpeed, PEFT, quantization, checkpointing, or `agilerl[llm]`.

## Read First

- `references/workflows.md` for reasoning, preference, multiturn, and SFT/DPO routes.
- `references/api-reference.md` for algorithms, trainers, envs, and utilities.
- `references/configuration.md` for optional dependencies, Accelerate, vLLM, quantization, and checkpoint settings.
- `references/troubleshooting.md` for backend, model, tokenizer, reward, and dependency failures.
- `scripts/inspect_llm_dependencies.py --help` for safe optional dependency checks.

## Boundaries

- Use `../hpo-and-mutation/SKILL.md` for generic mutation/tournament concepts; this sub-skill explains LLM-specific limitations.
- Use `../training-workflows/SKILL.md` for classical Gymnasium RL.
- Use `../offline-bandits-data/SKILL.md` for tabular/offline RL datasets, not LLM preference/reasoning data.

## Workflow Routes

| Task | AgileRL route |
| --- | --- |
| Reasoning RL with verifiable rewards | GRPO/CISPO/GSPO and `finetune_llm_reasoning(...)` |
| Preference optimization | DPO or preference-oriented GRPO and `finetune_llm_preference(...)` |
| Multi-turn LLM agents | LLM PPO, LLM REINFORCE, GRPO, and `finetune_llm_multiturn(...)` |
| Supervised fine-tuning | `SFT` and `finetune_llm_sft(...)` |
| Checkpoint/quantization/vLLM rollout planning | Configuration and troubleshooting references here |

## Safe Validation

```bash
python scripts/inspect_llm_dependencies.py --json
```

This reports optional packages and CUDA availability. It does not download models, load vLLM, start DeepSpeed, or train.
