---
name: training-and-evaluation
description: "Use HighwayEnv safely as an RL training, rollout, evaluation,
  rendering, and recording target."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Training and evaluation sub-skill

Use this sub-skill when an agent needs to run bounded rollouts, smoke-test an environment before training, integrate optional RL libraries, evaluate learned policies, use vectorized environments for RL, configure pixel/video evaluation, or avoid unbounded HighwayEnv training loops.

## Routing boundaries

- For choosing environment IDs, versioned environment names, reset/step basics, `render_mode` basics, registration, finite-MDP helpers, and general vectorized Gymnasium operation, read `../simulation-environments/SKILL.md`.
- For observation, action, reward, `info["rewards"]`, goal/success, image-observation, or continuous-action configuration decisions, read `../observations-actions-rewards/SKILL.md`.
- For custom roads, vehicles, dynamics, custom environment classes, or changing transition/reward internals, read `../road-vehicle-dynamics/SKILL.md`.
- Use this sub-skill only after the package imports and a basic environment can be created.

## Runtime references and helper

- Read `references/rl-integration.md` before using HighwayEnv with Stable-Baselines3, Torch, rl-agents, vectorized training, image observations, or policy evaluation. It includes optional dependency boundaries, Gymnasium-compatible loop patterns, SB3 DQN/PPO skeletons, and bounded evaluation patterns.
- Read `references/rendering-and-recording.md` when rendering during evaluation, collecting `rgb_array` frames, using image observations, recording videos, or diagnosing too-fast videos and headless display behavior.
- Read `references/troubleshooting.md` when training fails, videos are blank or too fast, optional RL imports are missing, Gymnasium/SB3 API signatures mismatch, image/CNN shapes fail, vectorized environments fail, or policies are unexpectedly poor.
- Run `scripts/random_policy_rollout.py` for a no-RL-dependency smoke test that samples random actions for a bounded number of episodes and steps, optionally renders `rgb_array` frames, and can write a JSON rollout summary.

## Safe default workflow

1. Confirm installation and environment creation with the root skill or simulation sub-skill.
2. Run a bounded random-policy smoke test before any RL training:
   ```bash
   python scripts/random_policy_rollout.py --env-id highway-v0 --episodes 1 --max-steps 20
   ```
3. If training with optional RL libraries, start from the skeletons in `references/rl-integration.md`, keep `total_timesteps` small for the first validation run, and evaluate with a hard episode and step cap.
4. If recording video, use the pattern in `references/rendering-and-recording.md` and always close the wrapped environment.

## Handoff contract

A successful use of this sub-skill should produce one or more of:

- a bounded smoke-test result with episode return, steps, termination/truncation status, and crash/success summary;
- an RL integration plan that explicitly lists optional dependencies and safe training/evaluation limits;
- a recording plan that uses `rgb_array`/`RecordVideo` safely and avoids too-fast videos;
- a clear route to another sub-skill if the blocker is environment selection, observation/action/reward configuration, or custom dynamics rather than training/evaluation.
