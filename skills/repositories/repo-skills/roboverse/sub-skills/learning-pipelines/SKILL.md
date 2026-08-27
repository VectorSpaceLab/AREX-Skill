---
name: learning-pipelines
description: "Guides RoboVerse reinforcement learning, imitation learning, VLA
  evaluation, fusion, dataset, checkpoint, and policy pipeline decisions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Learning Pipelines

Use this route for training or evaluating RL, imitation-learning, VLA, or
fusion policies; preparing an IL dataset; selecting a runner; loading a
checkpoint; or debugging normalization and policy/environment contracts.

## Route

1. Select the family in [workflows.md](references/workflows.md): CleanRL,
   FastTD3, SB3, RSL-RL, IL runner/policy, VLA adapter, or fusion.
2. Install only the required extras. `learn` covers many learning dependencies;
   `vla` adds much larger TensorFlow/LeRobot/Transformers stacks. Individual
   policy folders can still have stricter versions.
3. Validate task registration, observation/action shapes, dataset schema, and a
   tiny CPU forward pass before allocating GPUs or starting data downloads.
4. Read [data-and-checkpoints.md](references/data-and-checkpoints.md) before
   conversion, resume, or evaluation; checkpoint normalization state and config
   are part of the policy contract.
5. Use [troubleshooting.md](references/troubleshooting.md) for optional imports,
   device selection, stale normalization, data layout, and evaluation drift.

Long training, external model/data acquisition, trackers, and policy servers are
never default smoke tests. State the exact task, simulator, device, dataset,
checkpoint, and backend actually exercised.

Task implementation routes to [task-development](../task-development/SKILL.md);
integration data/replay routes to
[benchmark-integrations](../benchmark-integrations/SKILL.md).
