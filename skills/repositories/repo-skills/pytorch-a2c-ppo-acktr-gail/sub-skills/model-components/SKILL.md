---
name: model-components
description: "Use and adapt core policy, rollout, optimizer, distribution, and
  utility components in pytorch-a2c-ppo-acktr-gail."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model Components

Use this sub-skill when a task needs programmatic inspection, safe modification, or debugging of the repository's core Python components rather than an end-to-end environment run.

## Read This First

- API signatures, import paths, tensor shapes, and return values: [references/api-reference.md](references/api-reference.md).
- Architecture and modification guidance for policies, bases, rollouts, algorithms, KFAC, schedules, and log cleanup: [references/implementation-notes.md](references/implementation-notes.md).
- Common failures and fixes: [references/troubleshooting.md](references/troubleshooting.md).
- Safe CPU smoke script: [scripts/smoke_model_components.py](scripts/smoke_model_components.py).

## Best-Fit Tasks

Load this sub-skill for tasks such as:

- Instantiate `Policy`, `CNNBase`, `MLPBase`, action distributions, or `RolloutStorage` directly.
- Modify actor/critic base networks or recurrent policy behavior.
- Debug tensor shapes for `Policy.act`, `Policy.evaluate_actions`, rollout insertion, or PPO mini-batches.
- Reason about `A2C_ACKTR`, `PPO`, or `KFACOptimizer` update internals.
- Use `update_linear_schedule` or understand `cleanup_log_dir` side effects.

## Route Elsewhere

- End-to-end CLI training, evaluation, checkpoint playback, Gym environment wrappers, and command construction belong in `../training-workflows/`.
- GAIL expert-file schema, HDF5 conversion, discriminator updates, and imitation-learning workflow belong in `../gail-imitation/`.
- Cross-cutting installation, Gym/PyTorch dependency, optional simulator, and backend issues belong in the root skill's troubleshooting reference.

## Quick Smoke Check

From an environment where the package is installed, run:

```bash
python sub-skills/model-components/scripts/smoke_model_components.py
```

The script uses only CPU tensors and synthetic Gym spaces; it does not create environments, download data, or train an agent. A successful run prints `PASS model-components smoke`.
