---
name: objectives-and-training
description: "Choose and wire TorchRL losses, value estimators, target updaters,
  trainers, Hydra configs, and SOTA recipes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TorchRL objectives and training

Use this sub-skill when a task is about TorchRL objective modules, value estimators, target-network updates, trainer hooks, Hydra algorithm configs, or choosing an algorithm recipe. Typical triggers: `ClipPPOLoss`, `PPOLoss`, `SACLoss`, `DQNLoss`, `DDPGLoss`, `TD3Loss`, `IQLLoss`, `CQLLoss`, `MAPPOLoss`, `ValueEstimators`, `make_value_estimator`, `set_keys`, `_AcceptedKeys`, `SoftUpdate`, `HardUpdate`, `Trainer`, trainer hooks, config parity, and `sota-implementations`.

## Route before acting

- Actor, critic, distribution, recurrent-module, and policy-wrapper construction belongs to sibling sub-skill `modules-and-policies`. Return here after the modules expose the TensorDict keys the loss expects.
- Collector topology, replay buffers, prioritized samplers, and data movement belong to sibling sub-skill `collectors-and-replay`. Return here for loss-side priority keys and target updates.
- Environment specs, action specs, `step_mdp`, simulator setup, and transforms belong to sibling sub-skill `envs-and-transforms`.
- LLM GRPO/SFT/RLHF and VLA-specific serving or dataset workflows belong to sibling sub-skill `llm-vla-and-services`; this sub-skill only covers generic loss-key and trainer conventions that those workflows share.

## Operating sequence

1. Pick the loss family from [loss API reference](references/loss-api-reference.md) by algorithm, action space, online/offline setting, and multi-agent layout.
2. Verify the actor/critic/replay/env dependencies before writing training code: module `out_keys`, environment `action_spec`, replay sample keys, and `("next", ...)` transition fields must match the loss key map.
3. Configure TensorDict keys with `loss.set_keys(...)` using the accepted key names listed in [loss API reference](references/loss-api-reference.md). Prefer `NestedKey` tuples for nested fields.
4. Build the value estimator with `loss.make_value_estimator(ValueEstimators.<name>, ...)` or a standalone estimator such as `GAE`; make sure reward/done/terminated keys are forwarded to the estimator.
5. Add target-network updaters when the loss has delayed target parameters, and call updater `step()` at the correct cadence; see [training algorithms](references/training-algorithms.md).
6. If using TorchRL `Trainer`, register hooks deliberately and follow config/class parity rules from [trainer and configs](references/trainer-and-configs.md).
7. Use [SOTA implementation map](references/sota-implementation-map.md) as a reference-only recipe index. Do not run long SOTA launchers as generic helper scripts.
8. For failures, start with [troubleshooting](references/troubleshooting.md), then use the bundled inspection helper.

## Bundled helper

- [scripts/inspect_loss_keys.py](scripts/inspect_loss_keys.py) prints a named loss class signature, whether `set_keys` is available, default configurable TensorDict keys when accessible, and the default value estimator. It performs no training and is safe to run from any current directory.

## Verification boundary

The skill content is based on repository source, public reference docs, tutorials, SOTA recipe files, objective tests, trainer/config code, and CPU package/API inspection. Core objective/trainer APIs are CPU-verifiable. CUDA kernels, Triton paths, distributed learner backends, simulator-heavy examples, and long SOTA training are optional or reference-only unless a future task provisions those dependencies explicitly.
