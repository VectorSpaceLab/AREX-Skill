---
name: application-recipes
description: "Navigate ColossalAI first-party application packages, environment
  isolation, data/model prerequisites, and command anatomy without assuming
  heavyweight app execution is verified."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Application Recipes

Use this sub-skill when the task names ColossalChat/Coati, Colossal-LLaMA, ColossalEval, ColossalQA, ColossalMoE, or asks which first-party ColossalAI application project to use.

Application packages are useful but broad. They often require separate installation, large models, datasets, credentials, CUDA kernels, or dependency pins that can conflict with the core ColossalAI package environment.

## Route Here

- Choose among first-party applications by task: RLHF/post-training, LLaMA pretraining/SFT, LLM evaluation, retrieval QA, or MoE training/inference.
- Plan isolated environments and dependency constraints for application packages.
- Explain command anatomy from application scripts without running heavy model/data workflows.
- Diagnose app dependency conflicts, missing model weights, dataset format issues, and service/credential requirements.

## Reroute

- Core Booster plugin details: use `../booster-training/SKILL.md`.
- Core Colossal-Inference API and generation details: use `../inference-and-serving/SKILL.md`.
- Core launch/hostfile/NCCL issues: use `../installation-and-launch/SKILL.md`.
- ShardFormer or topology design: use `../parallelism-and-sharding/SKILL.md`.

## Application Map

- **ColossalChat / Coati**: SFT, reward model, PPO, DPO, SimPO, ORPO, KTO, GRPO, LoRA, quantization, and post-training command families.
- **Colossal-LLaMA**: continual pretraining, SFT, tokenizer/model/data preparation, training scripts, and LLaMA checkpoint inference examples.
- **ColossalEval**: dataset preparation, inference configs, dataset/GPT evaluation configs, metrics, and leaderboard reproduction flow.
- **ColossalQA**: LangChain-style retrieval conversation, vector stores, local/API LLMs, document loading, memory, and SQL/file paths.
- **ColossalMoE**: MoE training and inference examples powered by ColossalAI.

## References and Helper

- `references/application-overview.md` gives a task-to-app routing table and environment isolation rules.
- `references/colossalchat.md` covers ColossalChat/Coati stages and command families.
- `references/llama-eval-qa-moe.md` covers Colossal-LLaMA, ColossalEval, ColossalQA, and ColossalMoE.
- `references/troubleshooting.md` lists app-specific dependency, data, model, and credential failures.
- `scripts/application_env_matrix.py` prints package names and notable dependency conflicts.

## Operating Rules

- Do not claim application imports or native tests are verified unless a separate app environment was prepared and checked.
- Do not install app requirements into a stable core ColossalAI environment without checking version conflicts.
- Treat shell scripts as command anatomy: adapt paths, model names, datasets, GPU counts, and secrets to the user's environment.
