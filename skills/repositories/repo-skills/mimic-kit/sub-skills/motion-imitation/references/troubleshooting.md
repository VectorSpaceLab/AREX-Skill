# Motion-imitation troubleshooting

This page covers the failures most likely to appear when running or editing DeepMimic, AWR, LCP, and vault/static-object recipes.

## Quick reality check

This checkout only verified source imports, CLI help, compile checks, and tiny motion-conversion fixtures. Simulator-native train/test runs still need an external backend and the downloaded motions, models, and object assets.

## Symptom table

| Symptom | Likely cause | What to check |
| --- | --- | --- |
| `ModuleNotFoundError` for `isaacgym`, `isaaclab`, `newton`, or `warp` | The required simulator backend is not installed | Install the matching backend or switch to `runner-and-backends`. These recipes are backend-dependent and are not runnable without it. |
| Missing motion, model, or object asset files | The checkout does not ship the full data bundle | Confirm `motion_file`, `model_file`, and any vault object asset paths. This repo copy only contains the humanoid asset files; motions, models, and object XMLs must be downloaded separately. |
| `assert init_std > 0` or an action-space mismatch | The character XML and agent config do not agree on joint limits or DoF size | Use the matching character asset, env YAML, and agent YAML together. The action normalizer expects non-zero joint bounds. |
| Immediate FAIL or very short episodes | `pose_termination_dist` is too strict, `contact_bodies` are wrong, or the motion clip does not match the character | Relax the termination distance, review the contact list, and make sure the motion clip matches the asset. |
| Observation or checkpoint shape mismatch after editing `enable_tar_obs` or `tar_obs_steps` | The model was trained with a different observation layout | Retrain after changing target-observation settings, or restore the original env/agent pair. |
| LCP runs but does not look smoother | `lcp_weight` is too low, too high, or the wrong agent class is being used | Start near the shipped default and adjust gradually. Make sure the recipe still uses `LCPAgent`. |
| AWR actor weights collapse or learning looks unstable | `awr_temp` or `a_weight_clip` is too aggressive | Increase the temperature, raise the clip, or both. |
| Vault geometry does not appear where expected | Wrong `objects` entry, wrong object XML, or wrong object pose | Check `file`, `pos`, and optional `rot`. The vault object assets referenced by the shipped configs are external and absent here. |
| Test run looks random or ignores the checkpoint | `--model_file` is missing, wrong, or loaded with the wrong recipe | Always pair `--mode test` with the intended checkpoint and matching env/agent configs. |
| Train/test commands point at the wrong recipe | The arg file is stale or edited independently from the YAMLs | Update the arg file, env YAML, and agent YAML together. |

## Common fixes by workflow

### DeepMimic

- Recheck `motion_file`, `joint_err_w`, and `reward_*` fields first.
- If the policy collapses early, look at `pose_termination` and `pose_termination_dist`.
- If the observation layout changes, do not reuse an old checkpoint.

### AWR

- Verify `awr_temp` and `a_weight_clip` if the actor stops improving.
- The actor still inherits the PPO-style action regularization knobs, so check those too.

### LCP

- `lcp_weight` is the main smoothness knob.
- If the model becomes overly smooth or loses task accuracy, reduce the weight in small steps.

### Vault / static objects

- Check that the object XML exists and the object positions are correct.
- Keep `contact_bodies` conservative enough that the vault obstacle, not the floor or the character's limbs, drives the termination logic.

## If the issue is not here

- If the problem is backend installation, use `runner-and-backends`.
- If the problem is motion conversion or visualization, use the motion-tools workflow.
- If the problem is AMP/ADD/ASE or SMP, switch to the matching sub-skill instead of forcing this one.
