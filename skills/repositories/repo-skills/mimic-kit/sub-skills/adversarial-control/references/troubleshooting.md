# Troubleshooting

## Installation and import issues

| Symptom | Likely cause | What to check | Typical fix |
| --- | --- | --- | --- |
| `ModuleNotFoundError` for the simulator backend | External simulator is not installed | Confirm which backend the route expects | Install the matching backend before trying native train/test runs. |
| `ModuleNotFoundError` for `isaacgym` | Isaac Gym is absent | AMP, ADD, and ASE docs all assume a simulator backend | Use the bundled CPU/CUDA-only checks for drafting, or install Isaac Gym for native runs. |
| `ModuleNotFoundError` for `isaaclab` | Isaac Lab is absent | Some task-policy routes use Isaac Lab instead of Isaac Gym | Switch to the backend that is actually installed, or install Isaac Lab. |
| `ModuleNotFoundError` for `newton` or `warp` | Newton/Warp is absent | Newton-native routes need external packages | Install Newton/Warp before attempting native validation. |
| Import succeeds in a shell but not in a script | Source layout is script-oriented and not packaged | Check that the MimicKit checkout is on the local import path for the session | Run from a MimicKit checkout with source imports configured the same way as the route scripts. |

## Missing data and asset gaps

| Symptom | Likely cause | What to check | Typical fix |
| --- | --- | --- | --- |
| Motion file not found | `data/motions/` is not populated | Check the `motion_file` in the env config | Download the motion assets before training or testing. |
| Model file not found in test mode | No trained checkpoint is available | Check the `--model_file` path | Train first or point to a valid checkpoint. |
| Object asset not found for task envs | The task env expects object XMLs that are not in this checkout | Look for location, steering, or dodgeball object files under `data/assets/objects/` | Supply the missing object XMLs or avoid that visualization route until the assets are restored. |
| Sword-and-shield env cannot build | Character asset bundle is incomplete | Check the matching character asset path in the env config | Switch to the humanoid variant or restore the missing asset bundle. |
| `args/smp_dodgeball_humanoid_args.txt` points at a missing agent config | The checkout does not contain the matching dodgeball agent YAML | Check `data/agents/` for a matching file | Treat the policy route as unresolved and hand off to `smp`; do not invent a replacement config. |

## Reward balance and discriminator collapse

| Symptom | Likely cause | What to tune first | Notes |
| --- | --- | --- | --- |
| Agent ignores motion style | `disc_reward_weight` or `disc_reward_scale` is too low | Increase `disc_reward_weight`, then `disc_reward_scale` | Also confirm the motion asset matches the current env and embodiment. |
| Agent ignores the task | `task_reward_weight` is too low | Increase `task_reward_weight` | If the env is task-conditioned, keep the task reward and imitation reward in balance. |
| Discriminator saturates quickly | Replay buffer is too small, regularization is too weak, or observations are mismatched | Check `disc_buffer_size`, `disc_replay_samples`, `disc_grad_penalty`, and `disc_logit_reg` | Mismatched `num_disc_obs_steps` or `disc_dof_vel_obs` can look like collapse. |
| Discriminator outputs almost constant logits | Poor observation normalization or stale replay data | Re-check obs normalization and replay sizes | In AMP/ASE, verify the live obs and demo obs come from the same config family. |
| ADD reward is nearly useless | The diff observation is too close to zero or the pairwise obs are misaligned | Re-check `disc_obs_demo - disc_obs` and `num_disc_obs_steps=1` | ADD depends on paired agent/demo observations. |

## ASE-specific issues

| Symptom | Likely cause | What to tune first | Notes |
| --- | --- | --- | --- |
| Latents change too often | `latent_time_min/max` are too small | Increase both latent timing values | The latent should persist long enough to affect behavior. |
| Latents never seem to change | `latent_time_min/max` are too large or reset timing is mis-specified | Lower the timing window | Check the env-time reset logic before changing the encoder. |
| Encoder reward stays near zero | `enc_reward_weight` is too low or the latent/encoder interfaces do not match | Increase `enc_reward_weight` and confirm `latent_dim` | The encoder reward is an alignment term, not a pure imitation score. |
| Diversity term destabilizes the actor | `diversity_weight` is too large or `diversity_tar` is unrealistic | Lower `diversity_weight` first | Tune the target ratio only after the loss magnitude looks sensible. |
| ASE starts from the same pose every reset | `default_reset_prob` is too low or too high for the intended mix | Adjust `default_reset_prob` | The default-pose mix is part of the skill diversity route. |

## CLI and workflow misuse
- Use `--mode train` for training and `--mode test` for evaluation.
- In test mode, keep the same env and agent family as training and add `--model_file`.
- Keep the env config and agent config aligned: AMP, ADD, and ASE all change the discriminator or encoder input shape in different ways.
- If you switch from imitation-only AMP to task-conditioned AMP, make sure the task reward fields are present in the env config and the task AMP agent config is selected.
- If you switch from AMP to ADD or ASE, do not expect an old checkpoint to load cleanly unless the full shape and reward family stayed identical.

## Backend and verification limitations
- This sub-skill is drafted with simulator-native workflows preserved but not fully executed.
- Only CPU/CUDA torch imports, parser help, compile checks, and tiny converter fixtures were verified in the environment used for drafting.
- Native AMP, ADD, ASE, and task-control train/test loops still require the matching external simulator backend and the downloaded motion/model/asset bundles.
