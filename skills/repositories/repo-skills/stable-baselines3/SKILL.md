---
name: stable-baselines3
description: "Use Stable-Baselines3 for PyTorch reinforcement learning: train
  algorithms, validate Gymnasium environments, vectorize envs, customize
  policies, evaluate callbacks, and save/load SB3 models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Stable-Baselines3

Use this skill when a task involves Stable-Baselines3 (SB3), the PyTorch reinforcement-learning library with sklearn-like RL algorithms for Gymnasium environments.

## Install and Import Check

Stable-Baselines3 requires Python 3.10+ and PyTorch. For normal use:

```bash
pip install stable-baselines3
python - <<'PY'
import stable_baselines3 as sb3
print(sb3.__version__)
print(sb3.__all__)
PY
```

Use `pip install 'stable-baselines3[extra]'` only when the task needs optional rendering, TensorBoard/progress bars, Atari, plotting, or result-loading extras.

For a quick public API diagnostic, run [`scripts/sb3_doctor.py`](scripts/sb3_doctor.py) with `--help` first.

## Route by Task

- **Choose or train an algorithm**: use [`training-and-algorithms`](sub-skills/training-and-algorithms/SKILL.md) for A2C/PPO/DQN/SAC/TD3/DDPG selection, constructor parameters, `learn()`, action-space compatibility, and tiny smoke training.
- **Build, validate, or vectorize environments**: use [`environments-and-vectorization`](sub-skills/environments-and-vectorization/SKILL.md) for Gymnasium custom env APIs, `check_env`, `make_vec_env`, `DummyVecEnv`, `SubprocVecEnv`, `Monitor`, `VecNormalize`, and VecEnv API differences.
- **Evaluate, log, checkpoint, or load models**: use [`evaluation-and-persistence`](sub-skills/evaluation-and-persistence/SKILL.md) for `evaluate_policy`, callbacks, TensorBoard/logger behavior, `save()`, `load()`, replay buffers, `VecNormalize`, and portability debugging.
- **Customize policies and exploration**: use [`policies-and-customization`](sub-skills/policies-and-customization/SKILL.md) for `policy_kwargs`, custom feature extractors, `MultiInputPolicy`, action noise, gSDE, and `HerReplayBuffer`.

## Common Starting Points

- For a first CartPole-style training script, route to `training-and-algorithms` and use its `scripts/train_smoke.py` as a safe pattern.
- For custom Gymnasium env failures, route to `environments-and-vectorization` before changing the RL algorithm.
- For model portability or pickle/load errors, route to `evaluation-and-persistence` and use `print_system_info=True` guidance.
- For Dict observations, first validate spaces in `environments-and-vectorization`, then design `MultiInputPolicy` details in `policies-and-customization`.

## Shared References

- Read [`references/troubleshooting.md`](references/troubleshooting.md) for cross-cutting install/import, optional dependency, CPU/GPU, render, TensorBoard, and Gymnasium compatibility issues.
- Read [`references/native-verification.md`](references/native-verification.md) when selecting safe native SB3 tests or understanding which original repo behaviors informed this skill.
- Read [`references/repo-provenance.md`](references/repo-provenance.md) before deciding whether this skill matches a current Stable-Baselines3 checkout or needs refresh.

## Boundaries

This is a runtime user skill, not a maintainer release guide. It does not cover Docker image building, CI workflows, website generation, release publishing, or long benchmark training. If a task requires SB3 Contrib, RL Baselines3 Zoo, or SBX, treat those as adjacent projects and do not assume their APIs are included here.
