---
name: palm-rlhf-pytorch
description: "Operate the PaLM-rlhf-pytorch package for PaLM modeling, reward
  modeling, and RLHF/post-training workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PaLM-rLHF PyTorch

Use this repo skill for the `PaLM-rlhf-pytorch` package: the base PaLM transformer, reward models, implicit process rewards, and post-training trainers such as PPO, GRPO, TPO, and FlowRL.

## What This Skill Covers

- `palm-modeling`: construct, inspect, finetune, and smoke-check the base `PaLM` transformer.
- `reward-modeling`: train or inspect `RewardModel` and `ImplicitPRM` workflows.
- `policy-optimization`: use `RLHFTrainer`, `ActorCritic`, GRPO, TPO, or FlowRL for post-training.

## Start Here

1. Read [`references/package-overview.md`](references/package-overview.md) for the public import surface and package shape.
2. Read [`references/troubleshooting.md`](references/troubleshooting.md) for install/import, backend, and dependency pitfalls.
3. Run the bundled inspector to confirm the installed package is usable:

```bash
python scripts/inspect_palm_rlhf.py --device auto --check-cuda
```

If you only want a parser/import check first, use:

```bash
python scripts/inspect_palm_rlhf.py --help
```

## Installation

From a checkout of this repository, install the package in editable mode:

```bash
python -m pip install -e .
```

The project metadata requires Python 3.6+, but the verified inspection environment uses Python 3.11 with PyTorch 2.13 CUDA wheels. Keep the version consistent with the installed environment you are targeting.

## Route to the Right Sub-Skill

- Ask about PaLM construction, next-token loss, generation, embeddings, LoRA scopes, or the source pretraining recipe → `sub-skills/palm-modeling/SKILL.md`.
- Ask about reward scores, prompt masks, binned rewards, or implicit process rewards → `sub-skills/reward-modeling/SKILL.md`.
- Ask about PPO/GRPO/TPO/FlowRL trainers, prompt-token-id setup, or bounded post-training smoke tests → `sub-skills/policy-optimization/SKILL.md`.

## Public Import Surface

The root package exports these user-facing names:

```python
from palm_rlhf_pytorch import PaLM, RewardModel, RLHFTrainer, ActorCritic, ImplicitPRM
```

Trainer variants are module-qualified:

```python
from palm_rlhf_pytorch import grpo, tpo, flowrl
```

Use the root exports for the standard PPO path and the module-qualified names for the newer trainer variants.

## Common Prompt Shapes

- `"Build me a tiny PaLM smoke test"` → `palm-modeling`.
- `"How do I score sequences or train a reward model?"` → `reward-modeling`.
- `"Which RLHF trainer should I use?"` → `policy-optimization`.
- `"The example fails on CPU or with a missing extra"` → root troubleshooting plus the relevant sub-skill.
- `"I need one small end-to-end smoke"` → root route plus the three sub-skills in order.

## Fast Verification Ladder

1. Run `python scripts/inspect_palm_rlhf.py --help`.
2. Run `python scripts/inspect_palm_rlhf.py --device auto --check-cuda`.
3. Run the smallest sub-skill smoke script for the workflow you care about.
4. Only then consider a longer or more specialized workflow.

## Self-Containment Rule

All runtime guidance here is self-contained. Do not direct future agents to open, run, or depend on the original repository checkout once the skill has been generated.

## Freshness Check

Before treating this skill as current for a checkout, read [`references/repo-provenance.md`](references/repo-provenance.md). If the repo commit or dirty state differs from that snapshot, refresh the skill.

## Related References

- [`references/package-overview.md`](references/package-overview.md) for the verified import surface and workflow map.
- [`references/troubleshooting.md`](references/troubleshooting.md) for package-wide recovery steps.
- Each sub-skill's `references/` directory for workflow-specific API tables, recipes, and troubleshooting.
- Each sub-skill's `scripts/` directory for the safe tiny smoke helpers that correspond to that workflow.
