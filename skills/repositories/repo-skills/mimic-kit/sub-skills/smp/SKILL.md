---
name: smp
description: "Score-Matching Motion Priors workflows for TinyMDM prior
  training/testing and SMP task policies."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SMP

Use this sub-skill when the user wants to:

- train or sample a TinyMDM motion prior
- train or test an SMP policy with a prior reward and optional GSI
- check whether a prior config can safely back a policy env before launch

## Route elsewhere

- Generic runner, engine, device, distributed, and logging mechanics: use `runner-and-backends`
- Motion conversion, motion viewing, or log plotting: use `motion-tools`
- AMP / ADD / ASE non-SMP adversarial control: use `adversarial-control`

## Bundled assets

- [Prior training reference](references/prior-training.md)
- [Policy training reference](references/policy-training.md)
- [Troubleshooting](references/troubleshooting.md)
- [Prior wrapper](scripts/train_smp_prior.py)
- [Config checker](scripts/check_smp_config.py)

## Operating contract

1. Always resolve `--repo-root` before touching prior configs or assets.
2. Use `scripts/train_smp_prior.py --dry-run-config` first when you only need to validate paths and imports.
3. Before policy training, confirm the chosen agent, env, prior config, prior model, and engine control frequency match.
4. Treat simulator-native workflows as external dependencies. This subtree does not bundle Isaac Gym, Isaac Lab/Isaac Sim, Newton/Warp, or downloaded motions/models/assets.
5. If a config mismatch is reported, fix the env/prior pairing instead of weakening the compatibility checks.
