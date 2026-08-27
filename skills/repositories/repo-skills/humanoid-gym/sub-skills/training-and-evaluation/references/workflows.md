# Workflows

This reference covers the canonical training and evaluation flow for the `humanoid_ppo` task.

## 1) Readiness first

Before any native launch attempt, confirm the runtime facts that matter for this repo:

- Python 3.8-era environment.
- `humanoid==1.0.0` installed from this checkout.
- Isaac Gym Preview 4 manually installed and importable.
- PyTorch 1.13.1 with CUDA 11.7-era wheels or equivalent matching the host driver.
- Matching `--sim_device` and `--rl_device` settings.

If Isaac Gym is missing, stop at command construction and static API inspection. Do not claim training/play execution succeeded.

## 2) Build a training command

Use the bundled builder to print a safe command rather than launching the simulator directly.

Example smoke command:

```bash
python scripts/build_training_command.py \
  --task humanoid_ppo \
  --run-name smoke \
  --num-envs 16 \
  --max-iterations 1 \
  --headless \
  --sim-device cuda:0 \
  --rl-device cuda:0
```

Notes:
- `humanoid/scripts/train.py` consumes `--task`, `--run_name`, `--headless`, `--num_envs`, `--max_iterations`, `--resume`, `--load_run`, `--checkpoint`, and Isaac Gym device flags.
- `load_run` and `checkpoint` are only used for a real resume path when `--resume` is present.
- `XBotLCfg.env.num_envs` defaults to 4096, so small overrides are the normal smoke path.

## 3) Understand the training flow

`train.py` does the following:

1. `task_registry.make_env(...)` creates the Isaac Gym environment.
2. `task_registry.make_alg_runner(...)` builds the PPO runner and logging directory.
3. `OnPolicyRunner.learn(...)` collects rollouts, computes returns, updates PPO, and saves checkpoints.

Important runtime facts:
- Logging directory format is `logs/<experiment_name>/<date_time>_<run_name>/`.
- Checkpoints are saved as `model_<iteration>.pt`.
- `OnPolicyRunner.learn` starts W&B/TensorBoard logging when a log directory is present.
- Training uses `init_at_random_ep_len=True` in the public entry point.

## 4) Resume or select a checkpoint

When the user supplies only a run directory and a checkpoint number, use the runner lookup rules instead of asking for a full path.

Resolution rules from `get_load_path`:
1. Read runs under `logs/<experiment_name>/`.
2. Ignore the `exported/` directory.
3. Sort timestamped run folders by month/day/time when possible.
4. If `load_run` is omitted, choose the newest run.
5. If `checkpoint` is omitted, choose the newest `model_*.pt` file in that run.

Example resume command:

```bash
python scripts/build_training_command.py \
  --task humanoid_ppo \
  --run-name resume_a \
  --resume \
  --load-run Jan12_09-30-15_resume_a \
  --checkpoint 1200 \
  --headless
```

## 5) Build a play/evaluation command

Use the bundled play builder to describe a checkpoint load and evaluation intent.

Example checkpoint evaluation command:

```bash
python scripts/build_play_command.py \
  --task humanoid_ppo \
  --run-name eval_a \
  --load-run Jan12_09-30-15_resume_a \
  --checkpoint 1200 \
  --headless \
  --no-render
```

Important caveat:
- `humanoid/scripts/play.py` still hard-codes `EXPORT_POLICY=True`, `RENDER=True`, and `FIX_COMMAND=True` unless the source is edited.
- The helper can record that a user wants to disable rendering or command forcing, but that intent is advisory until the source is patched.
- The evaluation entry point also forces a one-env, plane-terrain, low-noise setup for testing.

## 6) TorchScript export path

`play.py` exports the policy actor only, not the critic:

- Export root: `logs/<experiment_name>/exported/policies/`
- Export filename: `policy_1.pt`

This export happens through `export_policy_as_jit`, which scripts `actor_critic.actor` on CPU.

## 7) PPO customization touchpoints

Use the API reference for the exact symbols, but the main customization points are:

- `XBotLCfgPPO.policy.actor_hidden_dims` / `critic_hidden_dims`
- `XBotLCfgPPO.algorithm` hyperparameters
- `XBotLCfgPPO.runner.num_steps_per_env`, `max_iterations`, `save_interval`
- `OnPolicyRunner` class/algorithm selection via the runner config strings

## 8) Safe verification boundary

Allowed without Isaac Gym:
- Command construction.
- Static API inspection.
- ActorCritic shape checks in a CPU-only environment.

Blocked without Isaac Gym:
- Native `train.py` and `play.py` execution.
- Any claim that PPO training or evaluation actually ran in Isaac Gym.
