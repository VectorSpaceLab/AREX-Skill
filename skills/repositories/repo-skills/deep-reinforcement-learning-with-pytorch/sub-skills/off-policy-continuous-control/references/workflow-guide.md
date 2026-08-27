# Off-Policy Continuous-Control Workflow Guide

This guide distills the repository's continuous-action examples into self-contained operating knowledge. The source scripts are intentionally **reference-only** for this skill: they are long-running, environment-sensitive trainers, and several need small compatibility edits on modern Gym/NumPy stacks.

## Variant map

| Variant | Default env in repo | Modern env to prefer | Action handling | Checkpoint layout | Use when |
| --- | --- | --- | --- | --- | --- |
| DDPG | `Pendulum-v0` | `Pendulum-v1` | Actor outputs `tanh * max_action`; exploration adds Gaussian noise then clips to `env.action_space.low/high`. | `./expDDPG.py<env>./actor.pth`, `critic.pth` | Deterministic actor-critic baseline for simple continuous control. |
| SAC single-Q | `Pendulum-v0` | `Pendulum-v1` | Samples tanh-squashed scalar action; intended normalized wrapper maps `[-1, 1]` to env bounds. | `./SAC_model/policy_net.pth`, `value_net.pth`, `Q_net.pth` | Explaining the early SAC implementation; avoid for checkpoint playback unless load is patched. |
| SAC dual-Q | `Pendulum-v0` | `Pendulum-v1` | Same normalized action idea, with two Q networks and min-Q target. | `./SAC_model/policy_net.pth`, `value_net.pth`, `Q_net1.pth`, `Q_net2.pth` | Comparing single-Q vs dual-Q SAC on Pendulum. |
| SAC BipedalWalker | `BipedalWalker-v2` | `BipedalWalker-v3` | Vector action, normalized wrapper, tensor replay buffer on selected device. | Same `SAC_model/` names as dual-Q. | SAC on Box2D continuous locomotion after Box2D/pygame checks. |
| SAC test agent | `BipedalWalker-v2`, `--mode test` | `BipedalWalker-v3` | Loads dual-Q-style actor and renders selected actions. | Expects `SAC_model/` in the working directory. | Saved SAC policy playback when matching checkpoint files exist. |
| TD3 | `Pendulum-v0` | `Pendulum-v1` | Actor outputs bounded action; training adds clipped exploration noise and target policy smoothing. | `./expTD3.py<env>./actor.pth`, `actor_target.pth`, `critic_1.pth`, `critic_1_target.pth`, `critic_2.pth`, `critic_2_target.pth` | TD3 baseline for Pendulum and SAC-vs-TD3 comparison. |
| TD3 BipedalWalker | `BipedalWalker-v2` | `BipedalWalker-v3` | Same TD3 action and target-noise logic with a 4-D action space. | `./expTD3_BipedalWalker-v2.py<env>./...` | TD3 on Box2D locomotion or BipedalWalker checkpoint playback. |

## Environment modernization

The repository was written for old Gym and names legacy IDs. In the verified dependency family, `gym.make('Pendulum-v0')` and `gym.make('BipedalWalker-v2')` are rejected as deprecated, while `Pendulum-v1` and `BipedalWalker-v3` work. Prefer modern IDs unless reproducing exact historical results in an older pinned environment.

Modernizing an env ID can also change the generated checkpoint directory because the scripts concatenate the script filename and env name. If a checkpoint was trained under a legacy ID, either keep the same env ID in an old Gym stack, move/copy the checkpoint files into the modern-name directory, or patch the script to accept an explicit checkpoint directory.

## DDPG notes

- Actor: two hidden layers of 400 and 300 units, final `tanh` scaled by `max_action`.
- Critic: state-action concatenation through 400 and 300 units to a scalar Q value.
- Replay buffer stores `(state, next_state, action, reward, done)` tuples and samples NumPy batches.
- Training loop is very large by default (`max_episode=100000`, `capacity=1000000`, `update_iteration=200`). Treat it as a training job, not a smoke test.
- Test mode loads `actor.pth` and `critic.pth`, then renders. The source test branch references `args.max_length_of_trajectory`, which is not defined; patch it to a concrete horizon or reuse `max_episode` before relying on DDPG test mode.

## SAC notes

- SAC scripts use a `NormalizedActions` wrapper to map policy actions in `[-1, 1]` into the Box action range. On modern Gym, the wrapper should implement `action()` and `reverse_action()`, not only legacy `_action()` and `_reverse_action()` methods.
- `SAC.py` is a simpler single-Q implementation and its `load()` method calls `torch.load` with the wrong signature. Use it for algorithm study or patch `load_state_dict(torch.load(path, map_location=device))` before playback.
- `SAC_dual_Q_net.py` and `SAC_BipedalWalker-v2.py` add twin Q networks and load files with the expected `load_state_dict(torch.load(...))` pattern.
- `test_agent.py` is a playback-oriented dual-Q BipedalWalker script. Its save/load logic uses `Q_net1.pth` for both Q networks in places, so verify the checkpoint filenames before treating Q2 as independently restored.
- Several SAC CLI arguments are typed as `int` even when their defaults are floats (`learning_rate`, `gamma`). If tuning from the command line, patch those parser types to `float` first.

## TD3 notes

- TD3 uses twin critics, target networks, delayed policy updates (`policy_delay=2`), clipped target policy noise, and replay-buffer sampling.
- Pendulum TD3 and BipedalWalker TD3 share almost the same code; the BipedalWalker file mainly changes the default env and checkpoint directory prefix.
- Default training loops are large (`num_iteration=100000`, horizon up to 2000 steps). Use a bounded budget for experiments.
- The source uses `np.float(done)`, which fails on NumPy versions where deprecated aliases were removed. Replace it with `float(done)` or `np.float64(done)`.

## Comparing SAC vs TD3

Use the same env ID, seed policy, time budget, render setting, and checkpoint-root convention. Normalize these differences before interpreting returns:

1. **Action scaling:** SAC assumes normalized policy actions; TD3 emits environment-scaled actions directly.
2. **Exploration:** SAC samples from a stochastic policy; TD3 adds Gaussian exploration noise in training and target policy smoothing in updates.
3. **Critics:** SAC dual-Q and TD3 both use twin Q networks, but SAC's objective includes entropy/log-probability terms.
4. **Checkpoint shape:** Pendulum checkpoints are incompatible with BipedalWalker checkpoints because observation/action dimensions differ.
5. **Environment IDs:** compare `Pendulum-v1` with `Pendulum-v1`, not one legacy and one modern ID.

## When to avoid launching training

Do not launch a default training script when the user only asks for inspection, comparison, compatibility, or checkpoint diagnosis. Use the compatibility helper and reference tables first, then ask for a run budget if training is truly requested.
