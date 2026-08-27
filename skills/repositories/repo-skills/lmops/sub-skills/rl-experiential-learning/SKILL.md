---
name: rl-experiential-learning
description: "Plan safe VeRL/Ray/vLLM experiential-learning workflows for OEL,
  OPCD, LLM-as-a-Coach, GAD, and OPO."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# rl-experiential-learning

Use this LMOps sub-skill when the user asks for VeRL-style RL, Ray/vLLM rollout, or experiential-learning post-training workflows in these project families:

- **OEL**: round-based experiential-knowledge extraction, experience-list construction, deploy/user trajectory collection, consolidation, checkpoint evaluation, and IF-Eval follow-up for Sokoban and FrozenLake-style text games.
- **OPCD**: math, text-game, and system-prompt context distillation; on-policy consolidation; off-policy trajectory/logit generation and training baselines.
- **LLM-as-a-Coach**: EL/RL training aliases, held-out WildChat evaluation, fuzzy benchmark generation, IF-Eval, and GPT-4o/OpenAI-compatible scoring.
- **GAD**: SeqKD baseline, warmup, adversarial training, generation/evaluation, branch switching, teacher-data preparation, and actor/critic checkpoint handling.
- **OPO**: exact on-policy GRPO-style configuration and optimal reward baseline checks.

Do not use this sub-skill for MiniLLM, DPKD, or Tuna non-VeRL distillation/ranking workflows; route those to the distillation-and-post-training sub-skill. Do not use it for CoRAG serving or LLMA reference decoding; route those to the rag-and-acceleration sub-skill.

## Safety contract

This runtime skill is a **planner and validator**. It must not start Docker containers, Ray clusters, vLLM servers, training, evaluation jobs, model downloads, checkpoint merges, W&B runs, Hugging Face downloads, OpenAI calls, or IF-Eval. Treat all paper-scale commands as staged plans for a target checkout that the user explicitly controls.

Before giving a concrete run plan, resolve:

1. Family: `oel`, `opcd`, `coach`, `gad`, or `opo`.
2. Stage: extraction, deploy, consolidation, evaluation, on-policy, off-policy, train, eval, fuzzy eval, end-task eval, score, SeqKD, warmup, adversarial, generation, or config.
3. Target checkout and prepared environment, including GPU class, node count, GPUs per node, Docker/Conda/Ray/vLLM readiness, and B200 versus A100/H100/H200 setup path when relevant.
4. Model roles: policy/student model, optional reference/teacher model, optional experiential/coach model, reward/discriminator model, and checkpoint step or range.
5. Data, checkpoint, and result roots as user-provided placeholders or environment variables; never hard-code machine-local roots.
6. Credential intent: W&B for training logs, Hugging Face for gated models/datasets, and OpenAI-compatible credentials for GPT-4o coach/scoring.

## Primary references

- [OEL and OPCD workflows](references/oel-opcd-workflows.md) covers OEL round extraction/deploy/consolidation/eval and OPCD math, text-game, and system-prompt on/off-policy flows.
- [LLM-as-a-Coach and GAD workflows](references/llm-as-a-coach-and-gad.md) covers Coach aliases, data/checkpoint/result roots, W&B/OpenAI/HF surfaces, and GAD branch-stage discipline.
- [OPO configuration reference](references/opo-config-reference.md) covers exact on-policy hyperparameter changes and optimal reward baseline handoff checks.
- [Troubleshooting](references/troubleshooting.md) covers heavy-backend boundaries, credentials, checkpoints, branches, data roots, Ray/vLLM, and unsafe evaluation caveats.

## Bundled scripts

Use scripts from this sub-skill directory only:

```bash
python scripts/verl_experiment_planner.py --family opcd --track system-prompt --stage on-policy --model <MODEL_OR_ID> --exp-name <EXP_NAME> --prompt-type safety --experience-path <PROMPT_FILE> --nodes 1 --gpus-per-node 8 --credentials wandb,hf
python scripts/check_experience_inputs.py --system-prompt-file <PROMPT_FILE> --prompt-type safety --strict
```

- `scripts/verl_experiment_planner.py` prints safe command skeletons and prerequisite checklists. It imports no LMOps code and never executes generated commands.
- `scripts/check_experience_inputs.py` validates experience lists, system prompt text/files, and expected data-root contents without loading models or importing LMOps code.

## Operating pattern

1. Classify and route with the references above.
2. Run the planner to produce a command/checklist draft, choosing explicit placeholders for models, roots, credentials, and GPU topology.
3. Run the input checker for any experience list, system prompt, or data root the plan depends on.
4. Return a staged plan plus unresolved prerequisites. Clearly label any GPU, Docker, Ray, vLLM, W&B, Hugging Face, OpenAI, IF-Eval, or checkpoint-merge step as unexecuted unless the user later runs it in Researcher mode.

## Verification status

Creation-time verification for this sub-skill is static and CPU-only. The generated scripts were designed to be safe planners/validators and not to import repository code. End-to-end Docker, Ray, vLLM, GPU training, model downloads, W&B logging, Hugging Face gated access, OpenAI scoring, checkpoint merging, and IF-Eval execution are documented but not claimed as locally verified by this skill.
