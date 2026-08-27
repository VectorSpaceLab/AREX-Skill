---
name: evaluation
description: "Evaluate pretrained PPO checkpoints, resolve
  checkpoint/environment configuration, and diagnose load or render issues."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Evaluation

Use this sub-skill when the user asks to test a pretrained network, evaluate a checkpoint, render a trained policy, average episode rewards, or understand why a PPO checkpoint load fails.

Do not use this sub-skill for training-loop changes, PPO update debugging, reward-log plotting, or GIF composition. Route log plots and frame/GIF workflows to the sibling [visualization sub-skill](../visualization/SKILL.md). Route low-level `PPO.load`, `PPO.save`, `select_action`, and architecture questions to the root shared [API reference](../../references/api-reference.md).

## What this sub-skill owns

- Resolving the pretrained checkpoint path convention: `PPO_preTrained/<env_name>/PPO_<env_name>_<random_seed>_<run_num>.pth`.
- Matching checkpoint names to environment names, action-space class, and PPO constructor dimensions.
- Preserving continuous-policy `action_std` alignment; the repo's checkpoint files do not store `action_std`.
- Running or adapting the `test.py` evaluation pattern: load policy, run episodes, print per-episode rewards, and report the average reward.
- Deciding whether rendering is safe in local, notebook, remote, or headless sessions.
- Diagnosing missing Gym/Roboschool dependencies, checkpoint path mistakes, Gym/Gymnasium API drift, and state-dict shape mismatches.

## Quick workflow

1. **Resolve the intended checkpoint before running an environment.** Use the bundled helper from this sub-skill directory:

   ```bash
   python scripts/evaluation_config_helper.py --list-presets
   python scripts/evaluation_config_helper.py \
     --env-name RoboschoolWalker2d-v1 \
     --checkpoint-root PPO_preTrained \
     --check-file
   ```

   The helper is path/configuration-only by default. It does not import `gym`, `roboschool`, or the PPO module and does not run rollouts.

2. **Match the live environment to the checkpoint.** The environment used for `gym.make(env_name)` must expose the same observation dimension, action dimension, and action-space type that were used to save the state dict. A checkpoint named for `CartPole-v1` is not load-compatible with `LunarLander-v2`, and a discrete checkpoint is not compatible with a continuous `Box` policy.

3. **Construct the PPO agent with evaluation-compatible arguments.** The original testing script uses `lr_actor=0.0003`, `lr_critic=0.001`, `gamma=0.99`, `eps_clip=0.2`, and `K_epochs=80`. These update hyperparameters are mostly inert during pure `select_action` evaluation, but the constructor still requires them. Continuous policies also require an `action_std` float at construction time.

4. **Load the checkpoint once the dimensions are known.** The shared PPO implementation saves `policy_old.state_dict()` and `load(checkpoint_path)` loads the same state dict into both `policy_old` and `policy` using `torch.load(..., map_location=...)`. Use the root [API reference](../../references/api-reference.md) for exact load/save behavior.

5. **Run episodes and average rewards.** The native evaluation loop resets the env, calls `ppo_agent.select_action(state)`, steps the env until `done` or `max_ep_len`, clears the rollout buffer after each episode, prints episode reward, and reports `average test reward` over `total_test_episodes`.

6. **Render only when the display path is ready.** Numeric evaluation does not require rendering. For on-screen display, use a compatible Gym render path and a real display. For `rgb_array` frame capture and GIF assembly, switch to [visualization](../visualization/SKILL.md).

## Core references

- [Evaluation workflow](references/evaluation-workflow.md) - evaluation loop adaptation, old/new Gym API handling, and render choices.
- [Checkpoints and environments](references/checkpoints-and-envs.md) - file naming, built-in pretrained environment presets, and action-space matching rules.
- [Troubleshooting](references/troubleshooting.md) - missing dependencies, checkpoint mismatch, headless rendering, and Gym/Gymnasium compatibility failures.
- [Root PPO API reference](../../references/api-reference.md) - constructor, `select_action`, `save`, and `load` details shared across sub-skills.

## Validation commands

Safe checks for this sub-skill should avoid long rollouts unless the user explicitly has the environment packages, display, and checkpoint ready:

```bash
python scripts/evaluation_config_helper.py --help
python scripts/evaluation_config_helper.py --env-name CartPole-v1 --checkpoint-root PPO_preTrained --check-file
python -m py_compile scripts/evaluation_config_helper.py
```

A real episode rollout is optional and dependency-bound because the native `test.py` imports legacy `gym` and `roboschool`; do not treat a missing optional environment package as a failure of the helper or documentation.
