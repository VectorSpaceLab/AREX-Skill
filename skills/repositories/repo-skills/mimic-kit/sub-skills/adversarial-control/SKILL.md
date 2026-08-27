---
name: adversarial-control
description: "AMP, ADD, ASE, and task-conditioned adversarial control workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# adversarial-control

Use this sub-skill for AMP, ADD, and ASE workflows in MimicKit, plus AMP task-conditioned location and steering routes. If the request is about SMP score-matching priors or prior-based task policies, hand off to the `smp` sub-skill instead.

## What it covers
- AMP imitation-only controllers and AMP task-mixed controllers.
- ADD differential discriminator training and control.
- ASE latent skill routing, encoder rewards, and diversity regularization.
- Task-conditioned location and steering control built on the AMP family.
- The task-dodgeball environment shape as a related reference point, with the full policy route handled elsewhere.

## Start here
1. Pick the route in `references/amp-add-ase-workflows.md`.
2. Confirm the discriminator, reward, and latent knobs in `references/discriminator-and-latent-configs.md`.
3. Use `references/troubleshooting.md` before changing configs or claiming a blocker.
4. Keep unresolved simulator, asset, or data gaps explicit.

## Route rules
- AMP imitation-only: same motion-clip imitation path, no task reward mix.
- AMP task-conditioned: combine motion imitation with location or steering tasks using the task AMP configs.
- ADD: use the differential discriminator path; the discriminator learns on target-vs-agent observation differences.
- ASE: use the latent-conditioned AMP path with encoder reward and diversity loss.
- Task-dodgeball: use the task env as a reference point only; the full policy route belongs with the SMP sub-skill.

## Do not route here
- SMP score-matching priors and task-policy training around those priors.
- DeepMimic, AWR, or LCP motion-imitation workflows.
- Motion conversion and visualization.
- Backend install, simulator selection, or low-level engine plumbing.

## Evidence distilled into this skill
This sub-skill was distilled from the AMP, ADD, and ASE docs plus the matching env, agent, and config families in a MimicKit checkout. Use the bundled references in this subtree for operational details; do not send future agents back to source-doc reads for routine routing.

## Stable config warning
If a change affects `num_disc_obs_steps`, `disc_dof_vel_obs`, or `latent_dim`, assume the saved model and the surrounding config pair may no longer match and re-check the whole route before reusing a checkpoint.
