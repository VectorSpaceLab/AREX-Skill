---
name: zhusuan
description: "Use ZhuSuan for Bayesian networks, variational inference,
  HMC/SG-MCMC sampling, and importance-sampling workflows on TensorFlow 1.x."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# ZhuSuan

ZhuSuan is a TensorFlow 1.x probabilistic-programming library for Bayesian deep
learning. Use this skill when the user asks about `import zhusuan as zs`,
Bayesian networks, latent-variable models, variational objectives, posterior
sampling, or the repo's example workflows.

## Quick start

1. Read `references/overview.md` for the module map and installation note.
2. Read `references/workflows.md` for the example-family map and dataset notes.
3. Read `references/api-reference.md` when you need exact signatures.
4. Read `references/troubleshooting.md` when install, TF1, dtype, or shape
   issues show up.
5. Run `scripts/core_smoke.py` after installing the package if you want a fast
   import-and-objective sanity check.

## Route to a sub-skill

- `sub-skills/modeling-primitives/SKILL.md` for distributions, BayesianNet,
  MetaBayesianNet, observations, deterministic nodes, and node inspection.
- `sub-skills/variational-inference/SKILL.md` for ELBO, IWAE, KLPQ,
  importance-sampling likelihoods, normalizing flows, and VAE/BNN/SVGP-style
  training.
- `sub-skills/mcmc-and-sampling/SKILL.md` for HMC, SGLD, PSGLD, SGHMC, SGNHT,
  AIS, and chain diagnostics.

## What this root skill is for

- Give the fastest route to the right workflow and reference.
- Provide the package-level install, import, and troubleshooting entry point.
- Keep the skill usable after the original checkout disappears.

## What this root skill is not for

- It is not a full API manual; read the relevant reference file instead.
- It is not a training script collection; the example families are summarized in
  `references/workflows.md` and the sub-skills.
- It is not a replacement for the sub-skills; those carry the detailed workflow
  guidance.

## Practical reminders

- ZhuSuan's core API is graph-based and TF1-style. Sessions, placeholders, and
  variable scopes still matter.
- The verified inspection environment used TensorFlow 1.15.5 with SciPy and
  mock on Python 3.6.
- The example families often need external data or optional image helpers, so
  keep them as references unless the user explicitly wants a full run.
