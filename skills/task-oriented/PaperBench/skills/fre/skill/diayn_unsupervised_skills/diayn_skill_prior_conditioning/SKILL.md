---
name: diayn_skill_prior_conditioning
description: Build fixed-prior latent skill schedules and per-timestep conditioning records for DIAYN-style unsupervised rollouts.
---

# DIAYN Skill Prior Conditioning

Use this skill when a recovery or implementation needs the DIAYN latent skill sampling contract: a fixed categorical prior, one sampled skill per episode, and the same skill used for every timestep in that episode. Do not use it for learned skill priors or task-reward meta-policies.

## Inputs

- `num_skills`: positive integer number of categorical skills.
- `episodes`: positive integer rollout episode count.
- `horizon`: positive integer timestep count per episode.
- Optional `seed` for deterministic sampling.

## Outputs

- Episode-level sampled skill ids.
- Timestep conditioning records with one-hot skill vectors.
- Uniform prior probabilities and `log_prior` values.

## Workflow

1. Validate positive dimensions and create a uniform prior over skill ids.
2. Sample one skill id per episode with the supplied seed.
3. Expand each episode skill into all timesteps without resampling.
4. Pass `log_prior` to DIAYN reward computation as `log p(z)`.
5. Preserve generated schedule logs as recovery evidence when running experiments.

## Validation

Run `python scripts/skill_prior.py --num-skills 3 --episodes 3 --horizon 2 --seed 7` for a JSON smoke output. Run `python -m pytest tests` or the Distiller skill-tree validator with `--run-tests` for deterministic assertions.

## Limitations

The helper does not train a policy and does not infer a skill prior from data. It intentionally preserves the fixed-prior assumption from DIAYN.
