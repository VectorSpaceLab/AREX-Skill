---
name: training-and-evaluation
description: "Safely construct Humanoid-Gym PPO training and evaluation
  commands, checkpoint loads, and TorchScript export guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# training-and-evaluation

Use this sub-skill when a future agent needs to prepare or explain Humanoid-Gym PPO training and evaluation workflows without crossing into environment design or MuJoCo deployment.

## Use this skill for
- Building safe command lines for `humanoid/scripts/train.py` and `humanoid/scripts/play.py`.
- Choosing `--load_run` and `--checkpoint` when only a run directory or iteration number is known.
- Explaining `task_registry`, `OnPolicyRunner`, `PPO`, `ActorCritic`, and `RolloutStorage` behavior.
- Describing checkpoint layout, logging layout, and TorchScript export behavior.
- Checking backend readiness for Isaac Gym-based training/evaluation.

## Route elsewhere
- Robot, terrain, reward, observation, or task-definition changes → `environment-customization`.
- MuJoCo sim-to-sim rollout and exported-policy deployment → `sim2sim-deployment`.
- Real robot hardware deployment → out of scope.

## Safety boundary
- Native `train.py`/`play.py` execution still requires Python 3.8, `humanoid==1.0.0`, Isaac Gym Preview 4, and the matching CUDA/PyTorch stack.
- If Isaac Gym is missing, stop at static guidance and mark native training/play as `BLOCKED_REQUIRED_BACKEND`.
- `play.py` hard-codes export/render/command-fixing behavior unless the source file is edited; the bundled builder only surfaces intent.
- The public registered task in this checkout is `humanoid_ppo`; the parser default `XBotL_free` is stale.

## Bundled files
- `references/workflows.md`
- `references/api-reference.md`
- `references/troubleshooting.md`
- `scripts/build_training_command.py`
- `scripts/build_play_command.py`

## Operating rule
This skill is command-oriented. It prints or explains safe launch commands and API facts; it does not launch Isaac Gym training itself.
