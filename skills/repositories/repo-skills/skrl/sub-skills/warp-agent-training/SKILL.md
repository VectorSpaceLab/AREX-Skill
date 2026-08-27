---
name: warp-agent-training
description: "Build and troubleshoot public skrl 2.1.0 Warp DDPG, PPO, and SAC
  workflows with warp-nn models, explicit CPU or CUDA device selection,
  memories, resources, and sequential training boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Warp agent training

Use this branch when the task explicitly targets NVIDIA Warp, `warp-lang`,
`warp-nn`, or skrl's Warp implementations of DDPG, PPO, or SAC. Keep this
branch focused on single-agent construction and package/API diagnosis.

## Route first

1. Select a supported Python environment and install the Warp extra described in
   [workflow and API](references/workflow-and-api.md). Verify the installed
   `skrl` version before building models.
2. Select a device explicitly. Start with `"cpu"` for a portable package/API
   check. Treat CUDA as a separate runtime path: a visible CUDA device or a
   successful import is not evidence that a training kernel, simulator, or
   driver/toolkit combination works.
3. Wrap the already-created single-agent environment with the Warp adapter in
   the environment branch. This branch consumes its `observation_space`,
   optional `state_space`, `action_space`, `num_envs`, and `device`; it does not
   choose or install external simulators. See
   [environment integration](../environment-integration/SKILL.md).
4. Choose algorithm roles and model mixins using
   [algorithm and component selection](references/algorithm-and-component-selection.md).
   Initialize lazy/model-instantiator parameters with `init_state_dict` before
   creating an agent.
5. Create `RandomMemory`, configure the agent, and give the agent to
   `SequentialTrainer`. The trainer initializes the agent; call `train()` or
   `eval()` only after the construction checks pass.
6. For failures, use the decision matrix in
   [Warp troubleshooting](references/troubleshooting.md), then the shared
   [root troubleshooting](../../references/troubleshooting.md).

## Verification boundary

The bundled [`warp_cpu_probe.py`](scripts/warp_cpu_probe.py) is a safe import,
version, CPU-device, and configuration probe. Run it with the target
interpreter before attempting a real environment. It does not create an
environment, compile or launch a user model, train, evaluate, write runs, or
prove CUDA behavior. A CPU result verifies only the package/API path covered by
the probe; it cannot validate CUDA acceleration or an external simulator.

This branch does not own generic adapter selection, multi-agent Runner
configuration, Torch, or JAX workflows. Link those requests to the root router
or the relevant sibling branch rather than translating framework-specific code
into Warp code.
