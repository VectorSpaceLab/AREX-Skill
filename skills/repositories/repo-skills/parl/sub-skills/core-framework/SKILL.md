---
name: core-framework
description: "Build and debug PARL core Model, Algorithm, and Agent code, select
  PARL_BACKEND, verify backend aliases, save and restore Agents, and synchronize
  Model weights."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PARL core framework

Use this sub-skill when a task involves PARL's core `Model`, `Algorithm`, or `Agent` classes, backend alias selection, local import checks, `Agent.save` / `Agent.restore`, or `Model.get_weights` / `set_weights` / `sync_weights_to` behavior.

Do not use this sub-skill for choosing a complete RL algorithm recipe, xparl cluster lifecycle, or environment wrappers. Route those tasks to sibling operating skills:

- `../algorithm-recipes/` for DQN/DDPG/TD3/SAC/PPO/QMIX/MADDPG and example-level training structure.
- `../xparl-distributed/` for `@parl.remote_class`, `parl.connect`, `xparl start`, file distribution, and distributed security.
- `../environment-utils/` for Gym compatibility wrappers, replay memory, schedulers, logging, and vectorized environments.

## Operating workflow

1. **Choose the backend before importing PARL.** Set `PARL_BACKEND=torch`, `PARL_BACKEND=paddle`, or `PARL_BACKEND=fluid` in the process environment before any `import parl`. If it is unset, PARL selects an installed backend automatically, preferring Paddle 2.x over legacy Fluid over Torch.
2. **Verify aliases.** Confirm that `parl.Model`, `parl.Algorithm`, and `parl.Agent` resolve to the expected backend modules. The bundled checker can do this safely:

   ```bash
   python scripts/check_parl_core.py --backend torch --torch-smoke auto
   ```

3. **Implement the three layers in order.** Define a backend-specific `parl.Model`; pass it into a `parl.Algorithm` that implements `predict` / `learn` / optionally `sample`; wrap the algorithm in a `parl.Agent` that handles environment-facing data conversion and delegates to the algorithm.
4. **Keep data-flow responsibilities separate.** Model computes neural-network outputs; Algorithm owns losses, optimizers, target models, and weight updates; Agent performs environment I/O, preprocessing, sampling policy decisions, and persistence.
5. **Use weight APIs with matching structures.** `sync_weights_to` requires a different target instance of the same model class and compatible parameter shapes. `get_weights` / `set_weights` should be used between equivalent model or algorithm structures.
6. **Save and restore into an already-created architecture.** Recreate the same model/algorithm/agent structure before restoring. Use a backend-appropriate checkpoint path and pass an explicit model when the algorithm has more than one model.
7. **Escalate by symptom.** For import/backend failures, use `references/backend-selection.md`; for class/API behavior, use `references/api-reference.md`; for runtime errors, use `references/troubleshooting.md`.

## Backend verification status

This skill's runtime checks verified PARL 2.2.1 with the Torch backend aliases and a tiny Torch model weight sync / get / set smoke. Paddle 2.x and legacy Fluid guidance is source-backed and should be rechecked in the user's environment when those optional dependencies are installed.

## Reference map

- `references/api-reference.md` — distilled core API behavior and safe implementation patterns.
- `references/backend-selection.md` — how PARL chooses `torch`, `paddle`, or `fluid` and how to verify aliases.
- `references/troubleshooting.md` — common fixes for backend imports, NumPy/Torch compatibility, save/restore, and weight-shape mismatches.
- `scripts/check_parl_core.py` — deterministic local checker for version/backend aliases plus optional Torch smoke.
