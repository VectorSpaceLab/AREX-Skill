---
name: motion-imitation
description: "DeepMimic, AWR, LCP, and static-object/vault motion-imitation
  workflows for MimicKit."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# motion-imitation

Use this sub-skill for motion-tracking workflows in a MimicKit checkout:

- DeepMimic PPO-style motion imitation
- AWR motion imitation
- LCP motion imitation
- vault and other static-object imitation recipes built on `StaticObjectsEnv`

Do not use this sub-skill for AMP, ADD, or ASE discriminator flows, SMP prior or policy flows, motion conversion, motion viewing, or generic runner/backend setup; route those to `adversarial-control`, `smp`, `motion-tools`, or `runner-and-backends`.

## Start here

1. Read `references/deepmimic-awr-lcp-workflows.md` for command templates, recipe/config pairings, and vault/static-object notes.
2. Read `references/config-tuning.md` before editing motion, reward, termination, or batch settings.
3. Read `references/troubleshooting.md` when a command fails, a model will not load, or an asset is missing.

## What to keep aligned

- Keep `env_config`, `agent_config`, and `args/*.txt` aligned for the same recipe.
- Use the same character family across the asset, motion, env, agent, and arg files.
- For test runs, start from the matching training arg file and override with `--mode test`, `--num_envs 4`, `--visualize true`, and an explicit `--model_file`.
- For vault/static-object recipes, keep the `objects` list, contact bodies, and motion clip in sync.
- If the simulator backend or downloaded assets are missing, hand off to `runner-and-backends` instead of inventing a runnable command.

## Key knobs this sub-skill explains

- `motion_file`
- `reward_*_w` and `reward_*_scale`
- `pose_termination` and `pose_termination_dist`
- `enable_tar_obs` and `tar_obs_steps`
- `joint_err_w`
- `lcp_weight`
- `awr_temp` and `a_weight_clip`
- shared PPO/AWR/LCP `steps_per_iter`, `iters_per_output`, `test_episodes`, `actor_epochs`, `actor_batch_size`, `critic_epochs`, and `critic_batch_size`

## Provenance

This sub-skill was distilled from `README.md`, `docs/README_DeepMimic.md`, `docs/README_AWR.md`, `docs/README_LCP.md`, `mimickit/envs/deepmimic_env.py`, `mimickit/envs/static_objects_env.py`, `mimickit/learning/ppo_agent.py`, `mimickit/learning/awr_agent.py`, `mimickit/learning/lcp_agent.py`, and the `data/envs`, `data/agents`, and `args` filename matrix.
