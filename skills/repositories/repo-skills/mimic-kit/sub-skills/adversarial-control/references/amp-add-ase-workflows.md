# AMP, ADD, and ASE workflow matrix

## Quick chooser

| Route | Best fit | Core files | Key knobs | Ready-made args | Notes |
| --- | --- | --- | --- | --- | --- |
| AMP imitation-only | Stylized motion imitation with no task reward mix | `envs/amp_env.py`, `learning/amp_agent.py`, `data/envs/amp_humanoid_env.yaml`, `data/agents/amp_humanoid_agent.yaml` | `num_disc_obs_steps`, `disc_dof_vel_obs`, `disc_buffer_size`, `disc_replay_samples`, `disc_grad_penalty`, `disc_reward_scale`, `task_reward_weight`, `disc_reward_weight` | `args/amp_humanoid_args.txt` | Same family also appears for `g1`, `go2`, `pi_plus`, and `smpl` embodiments. |
| AMP task-location | Motion imitation plus a moving destination task | `envs/task_location_env.py`, `data/envs/amp_location_humanoid_env.yaml`, `data/envs/amp_location_humanoid_sword_shield_env.yaml`, `data/agents/amp_task_humanoid_agent.yaml` | `tar_speed`, `tar_change_time_min`, `tar_change_time_max`, `tar_dist_min`, `tar_dist_max`, `dist_threshold`, `pos_err_scale`, `vel_err_scale`, `pos_reward_w`, `vel_reward_w`, `face_reward_w`, `task_reward_weight`, `disc_reward_weight` | `args/amp_location_humanoid_args.txt`, `args/amp_location_humanoid_sword_shield_args.txt` | Task reward and imitation reward are blended by the agent config. |
| AMP task-steering | Motion imitation plus a heading and speed task | `envs/task_steering_env.py`, `data/envs/amp_steering_humanoid_env.yaml`, `data/envs/amp_steering_humanoid_sword_shield_env.yaml`, `data/agents/amp_task_humanoid_agent.yaml` | `rand_tar_dir`, `rand_face_dir`, `tar_speed_min`, `tar_speed_max`, `tar_change_time_min`, `tar_change_time_max`, `reward_steering_tar_w`, `reward_steering_face_w`, `reward_steering_vel_scale`, `task_reward_weight`, `disc_reward_weight` | `args/amp_steering_humanoid_args.txt`, `args/amp_steering_humanoid_sword_shield_args.txt` | Keep target-heading and facing-heading rewards separate when tuning. |
| ADD differential imitation | Motion imitation with a target-vs-agent discriminator on obs differences | `envs/add_env.py`, `learning/add_agent.py`, `data/envs/add_humanoid_env.yaml`, `data/agents/add_humanoid_agent.yaml` | `num_disc_obs_steps=1`, `enable_tar_obs`, `pose_termination`, `disc_buffer_size`, `disc_replay_samples`, `disc_logit_reg`, `disc_grad_penalty`, `disc_reward_scale`, `task_reward_weight`, `disc_reward_weight` | `args/add_humanoid_args.txt` | The discriminator sees the normalized difference between target and agent disc observations. |
| ASE latent embeddings | Reusable skill embeddings with encoder reward and latent routing | `envs/ase_env.py`, `learning/ase_agent.py`, `learning/ase_model.py`, `data/envs/ase_humanoid_env.yaml`, `data/envs/ase_humanoid_sword_shield_env.yaml`, `data/agents/ase_humanoid_agent.yaml` | `latent_dim`, `latent_time_min`, `latent_time_max`, `enc_reward_weight`, `diversity_weight`, `diversity_tar`, `default_reset_prob`, `disc_buffer_size`, `disc_replay_samples`, `disc_reward_scale`, `task_reward_weight`, `disc_reward_weight` | `args/ase_humanoid_args.txt` | ASE is AMP plus latent conditioning, encoder supervision, and diversity pressure. |
| Related task-dodgeball env | Projectile-avoidance task shape used as a reference point | `envs/task_dodgeball_env.py`, `data/envs/smp_dodgeball_humanoid_env.yaml`, `args/smp_dodgeball_humanoid_args.txt` | `num_projectiles`, `hit_dist`, `hit_force_threshold`, `hit_delta_v_threshold`, `proj_dist_min`, `proj_dist_max`, `proj_speed_min`, `proj_speed_max`, `proj_trigger_time_min`, `proj_trigger_time_max`, `proj_aim_noise_scale` | `args/smp_dodgeball_humanoid_args.txt` | The matching agent config is absent in this checkout; treat the policy route as unresolved and hand off to `smp`. |

## Command recipes

### AMP imitation-only
```bash
python ../runner-and-backends/scripts/run_mimickit.py --repo-root <mimickit-checkout> -- \
  --arg_file args/amp_humanoid_args.txt
```

### AMP task-location
```bash
python ../runner-and-backends/scripts/run_mimickit.py --repo-root <mimickit-checkout> -- \
  --arg_file args/amp_location_humanoid_args.txt
python ../runner-and-backends/scripts/run_mimickit.py --repo-root <mimickit-checkout> -- \
  --arg_file args/amp_location_humanoid_sword_shield_args.txt
```

### AMP task-steering
```bash
python ../runner-and-backends/scripts/run_mimickit.py --repo-root <mimickit-checkout> -- \
  --arg_file args/amp_steering_humanoid_args.txt
python ../runner-and-backends/scripts/run_mimickit.py --repo-root <mimickit-checkout> -- \
  --arg_file args/amp_steering_humanoid_sword_shield_args.txt
```

### ADD differential imitation
```bash
python ../runner-and-backends/scripts/run_mimickit.py --repo-root <mimickit-checkout> -- \
  --arg_file args/add_humanoid_args.txt
```

### ASE latent embeddings
```bash
python ../runner-and-backends/scripts/run_mimickit.py --repo-root <mimickit-checkout> -- \
  --arg_file args/ase_humanoid_args.txt
```

### Related task-dodgeball env (reference only)
```bash
python ../runner-and-backends/scripts/run_mimickit.py --repo-root <mimickit-checkout> -- \
  --arg_file args/smp_dodgeball_humanoid_args.txt
```

## Generic test-mode shape

Use the same arg file and add a model checkpoint when testing:

```bash
python ../runner-and-backends/scripts/run_mimickit.py --repo-root <mimickit-checkout> -- \
  --arg_file <matching_args.txt> --mode test --num_envs 4 --visualize true --model_file <trained_model.pt>
```


## Embodiment variants

The same AMP and ADD route pattern repeats for the `g1`, `go2`, `pi_plus`, and `smpl` families where matching config pairs exist. Swap the agent and env filenames to the matching embodiment family and keep the route logic unchanged.

ASE in this checkout is humanoid-focused, with a sword-and-shield variant in the same route family.

## Source anchors

Distilled from `docs/README_AMP.md`, `docs/README_ADD.md`, `docs/README_ASE.md`, `mimickit/envs/amp_env.py`, `mimickit/envs/add_env.py`, `mimickit/envs/ase_env.py`, `mimickit/envs/task_location_env.py`, `mimickit/envs/task_steering_env.py`, `mimickit/envs/task_dodgeball_env.py`, `mimickit/learning/amp_agent.py`, `mimickit/learning/add_agent.py`, `mimickit/learning/ase_agent.py`, and the matching `data/agents`, `data/envs`, and `args` families.
