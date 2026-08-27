# SMP Troubleshooting

This page collects the failures that are most likely when working on SMP prior and policy flows.

## Fast symptom map

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Missing SMP prior config` or `Missing SMP prior model` | `smp_prior_cfg` / `smp_prior_model` still point at placeholder paths | Point the agent config at the files written by prior training, usually `diffusion_config.yaml` and `model.pt` under the prior output directory |
| `SMP prior env mismatch for global_obs/root_height_obs/enable_tar_obs/num_disc_obs_steps/disc_dof_vel_obs/key_bodies/control_freq` | The prior env layout and the policy env layout do not match | Rebuild the prior with the matching env config, or switch the policy env to the prior's layout |
| `GSI init-state buffer only supports SMP envs with init_gsi_buffer()` | GSI was enabled on a non-SMP env or a class without the GSI buffer hooks | Use an SMP env or disable `enable_gsi` |
| `SMP GSI init-state buffer requires enable_tar_obs=False` | GSI is not compatible with target observations | Keep `enable_tar_obs: False` for GSI runs |
| `SMP GSI init-state buffer requires pose_termination=False` | GSI was paired with pose termination | Disable pose termination for GSI runs |
| `motion_file` or dataset manifest is missing | The prior motion source was not downloaded into the checkout | Restore the requested motion `.pkl` or dataset YAML before training the prior |
| Prior training is very slow or runs out of memory | `batch_size`, `num_samples_stat`, `T`, `num_layers`, or `num_attention_heads` are too large | Reduce prior batch/stat counts first, then shrink the diffusion model or `T` |
| Policy training runs out of memory during SDS reward evaluation | `smp_eval_batch_size` is too large | Lower `smp_eval_batch_size` before changing the PPO batch size |
| `train_tinymdm.py` seems to ignore your config | The source trainer's default cfg path is not a valid file in this checkout | Pass `--cfg_path` explicitly or use the bundled wrapper default |
| The dodgeball arg preset fails on a missing agent file | `args/smp_dodgeball_humanoid_args.txt` points at a specialized agent config that is not present here | Use the shared task agent baseline or add the missing agent file before relying on the preset |
| Location / steering / dodgeball launch fails on object assets | `data/assets/objects/*.xml` is absent in this checkout | Restore the missing object assets before launching those task envs |
| Backend import errors for Isaac Gym / Isaac Lab / Newton / Warp | The external simulator backend is not installed | Install the simulator stack that matches the chosen engine config |

## Checklist before retrying

- Run the prior wrapper with `--dry-run-config` first.
- Run the policy checker with the chosen agent, env, and engine config.
- Confirm the target machine has the simulator backend you picked.
- Confirm the downloaded motion/model/object assets are present.
- Keep the env/prior control frequency aligned at 30 Hz for the bundled SMP presets.

## Current checkout limitation

This checkout only verified:

- CUDA torch imports and allocation
- parser help for the TinyMDM trainer
- source compile/import smoke
- tiny conversion fixtures

It did not run full prior or policy training because the external simulator backends and the downloaded motion/model/object assets are not available here.
