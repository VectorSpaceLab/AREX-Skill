# Package Overview

## Purpose

This reference gives a compact, verified summary of the package surface so future agents can choose the right sub-skill without reopening the source checkout.

## Package Shape

- Distribution name: `PaLM-rlhf-pytorch`
- Import package: `palm_rlhf_pytorch`
- Project version in the inspected snapshot: `0.7.5`
- Build backend: `hatchling`
- No console scripts were declared in the inspected metadata.

## Public Root Imports

```python
from palm_rlhf_pytorch import PaLM, RewardModel, RLHFTrainer, ActorCritic, ImplicitPRM
```

Additional trainer modules:

```python
from palm_rlhf_pytorch import grpo, tpo, flowrl
```

## User-Facing Workflow Map

| Workflow | Main API | Typical user intent | Best sub-skill |
| --- | --- | --- | --- |
| Base transformer modeling | `PaLM` | build, score, generate, finetune, or merge LoRA scopes | `palm-modeling` |
| Reward estimation | `RewardModel` | score prompts/responses or train a binned/scalar reward model | `reward-modeling` |
| Implicit process rewards | `ImplicitPRM` | derive dense token-level rewards from model/reference log-prob differences | `reward-modeling` |
| PPO post-training | `RLHFTrainer`, `ActorCritic` | run the default RLHF trainer around a PaLM and reward model | `policy-optimization` |
| GRPO / TPO / FlowRL | `grpo.RLHFTrainer`, `tpo.RLHFTrainer`, `flowrl.FlowRLTrainer` | choose a newer post-training algorithm or compare trainer families | `policy-optimization` |

## Verified Runtime Facts

- `PaLM.generate` treats `seq_len` as the target total length, not just the number of new tokens.
- `PaLM.forward(return_loss=True)` performs next-token cross entropy internally.
- `RewardModel` supports both scalar and binned outputs and can use prompt masks or prompt lengths.
- `ImplicitPRM` returns dense rewards over the shifted target sequence.
- The trainers all expect exactly one prompt input style: `prompts`, `prompts_path`, or `prompt_token_ids`.
- The package uses `accelerate` internally for trainer workflows.
- `flash_attn=True` selects PyTorch scaled-dot-product attention, not the external `flash-attn` package.

## What To Read Next

- Read `sub-skills/palm-modeling/SKILL.md` for base transformer workflows.
- Read `sub-skills/reward-modeling/SKILL.md` for reward and implicit process reward workflows.
- Read `sub-skills/policy-optimization/SKILL.md` for trainer selection and tiny RLHF smoke checks.
