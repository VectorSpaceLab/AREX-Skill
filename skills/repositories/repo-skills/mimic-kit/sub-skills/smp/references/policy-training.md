# SMP Policy Training

Use this reference for SMP task-policy training and testing after a compatible prior has been prepared.

The policy path is built around `SMPAgent`, `SMPModel`, `SMPEnv`, and the task env subclasses for location, steering, and dodgeball.
The bundled checker is [`../scripts/check_smp_config.py`](../scripts/check_smp_config.py).

## Core policy behavior

`SMPAgent` is a PPO-style agent with two extra SMP pieces:

1. a frozen TinyMDM prior loaded from `smp_prior_cfg` and `smp_prior_model`
2. a reward term derived from `ESM_SDS_loss`

The combined reward is effectively:

```text
reward = task_reward_weight * task_reward + smp_reward_weight * smp_reward
smp_reward = exp(-normalized_sds_loss * sds_loss_scale) * smp_reward_scale
```

The agent also supports Generative State Initialization (GSI), which populates a buffer of prior-sampled initial states.

## Bundled task setups

| Scenario | Env config | Agent config | Prior config | Engine preset | Notes |
| --- | --- | --- | --- | --- | --- |
| Single-clip humanoid | `data/envs/smp_humanoid_env.yaml` | `data/agents/smp_humanoid_agent.yaml` | `tools/diffusion_model/config/tinymdm_single_clip.yaml` | `data/engines/isaac_lab_engine.yaml` in the bundled args | `enable_gsi: False`; motion file is the spinkick clip |
| Location | `data/envs/smp_location_humanoid_env.yaml` | `data/agents/smp_task_humanoid_agent.yaml` | `tools/diffusion_model/config/tinymdm_multi_clip.yaml` | `data/engines/isaac_lab_engine.yaml` in the bundled args | `enable_gsi: True`; no extra motion file is supplied at policy time |
| Steering | `data/envs/smp_steering_humanoid_env.yaml` | `data/agents/smp_task_humanoid_agent.yaml` | `tools/diffusion_model/config/tinymdm_multi_clip.yaml` | `data/engines/isaac_lab_engine.yaml` in the bundled args | same prior family as location |
| Dodgeball | `data/envs/smp_dodgeball_humanoid_env.yaml` | shared task agent baseline | multi-clip prior family | `data/engines/isaac_gym_engine.yaml` in the bundled args | the bundled arg preset in this checkout points at a missing specialized agent file; treat that as a gap |

The shared task agent config is the default baseline for location, steering, and dodgeball-style task policies.

## Prior compatibility rules

`SMPAgent._check_prior_env_config()` enforces the following between the prior env config and the policy env config:

- `global_obs`
- `root_height_obs`
- `enable_tar_obs`
- `num_disc_obs_steps`
- `disc_dof_vel_obs`
- `key_bodies` length
- `control_freq` via the engine config

In the bundled SMP configs, the compatible layouts are:

- single-clip humanoid: `global_obs: True`
- location / steering / dodgeball: `global_obs: False`
- all bundled SMP envs: `root_height_obs: True`, `enable_tar_obs: False`, `disc_dof_vel_obs: False`, `num_disc_obs_steps: 10`
- all bundled SMP envs: the same five `key_bodies`
- all bundled engine configs: `control_freq: 30`

If any of these drift, rebuild the prior with the matching env config or switch the policy env to the prior's layout.

## GSI rules

When `enable_gsi: True`, the agent also enforces:

- the env must expose `init_gsi_buffer()`
- `enable_tar_obs` must be `False`
- `pose_termination` must be `False`

GSI-related tuning knobs include:

- `gsi_iters`
- `gsi_sampler`
- `gsi_inference_steps`
- `gsi_buffer_size`
- `gsi_regen_num_motions`
- `gsi_batch_size`

The bundled task config uses:

- `gsi_iters: 50`
- `gsi_sampler: ddpm`
- `gsi_inference_steps: 10`
- `gsi_buffer_size: 4096`
- `gsi_regen_num_motions: 1024`
- `gsi_batch_size: 256`

GSI only seeds initial states from the prior; it does not require a fresh motion dataset argument during policy training.

## Reward and tuning checklist

Primary SMP policy knobs:

- `smp_prior_cfg`
- `smp_prior_model`
- `smp_eval_batch_size`
- `sds_loss_scale`
- `diffusion_steps`
- `task_reward_weight`
- `smp_reward_weight`
- `enable_gsi`
- `gsi_*`

Useful notes from the bundled configs:

- `smp_eval_batch_size: 4096` can be reduced first when SDS reward evaluation runs out of memory.
- `diffusion_steps: [22, 15, 8]` selects the timesteps used by the SDS reward.
- `task_reward_weight` and `smp_reward_weight` control the task/prior trade-off.
- `smp_reward_scale` exists in code with a default of `1.0`, but the bundled configs primarily tune `smp_reward_weight`.
- The tuning priority called out in the source notes is `smp_reward_weight > sds_loss_scale >= diffusion_steps`.
- The task config also keeps `sds_normalizer_samples` very large so the SDS normalizer stays adaptive for a long warmup.

## Common launch pattern

Start from the bundled args preset that matches the task env, then replace the config files if you have a new prior:

```bash
python ../runner-and-backends/scripts/run_mimickit.py \
  --repo-root <mimickit-checkout> \
  -- --mode train \
  --num_envs 4096 \
  --engine_config <engine-config> \
  --env_config <smp-env-config> \
  --agent_config <smp-agent-config> \
  --visualize false \
  --out_dir <output-dir>
```

For testing, switch to `--mode test`, reduce `--num_envs`, and provide `--model_file`.

## Policy validation checklist

Before a real policy run, confirm:

- the prior config and checkpoint both exist
- the policy env matches the prior env layout
- the engine control frequency matches the prior config
- the selected env has the required object or motion assets downloaded
- the simulator backend is installed for the target engine
- GSI compatibility is satisfied if `enable_gsi: True`
- the agent config you picked actually exists in the checkout

## Current checkout limits

This repository snapshot verified only the source imports, parser help, compile smoke, and tiny converter fixtures.

It did not run policy training here because:

- the simulator backends are not installed in this environment
- the motion/model assets are absent from `data/motions/` and `data/models/`
- the object assets needed by the location, steering, and dodgeball task envs are absent from `data/assets/objects/`

Use [`../scripts/check_smp_config.py`](../scripts/check_smp_config.py) to catch layout mismatches before launching a real run.
