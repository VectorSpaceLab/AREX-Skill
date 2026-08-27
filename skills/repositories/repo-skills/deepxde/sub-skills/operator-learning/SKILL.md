---
name: operator-learning
description: "Use DeepXDE operator-learning data classes and networks: DeepONet,
  POD-DeepONet, MIONet, PI-DeepONet, function spaces, and ZCS."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 2.1
---

# DeepXDE Operator Learning

Use this sub-skill when the task is to build or debug DeepXDE operator-learning workflows: supervised DeepONet data, physics-informed DeepONet data, POD-DeepONet, MIONet, function-space sampling, aligned/cartesian-product shapes, multi-output DeepONets, or Zero Coordinate Shift (ZCS).

## Start here

1. Classify the data layout before choosing the network:
   - aligned shared evaluation grid: `dde.data.TripleCartesianProd` with `dde.nn.DeepONetCartesianProd`;
   - unaligned sample triples: `dde.data.Triple` with `dde.nn.DeepONet`;
   - two-input-function operators: `dde.data.QuadrupleCartesianProd` with `dde.nn.MIONetCartesianProd` when using the PyTorch-verified API;
   - physics-informed operators: `dde.data.PDEOperator` or `dde.data.PDEOperatorCartesianProd` layered on `dde.data.PDE`/`TimePDE`.
2. Read [operator workflows](references/operator-workflows.md) for recipe order, shape checks, PI-DeepONet flow, POD/MIONet notes, and ZCS usage.
3. Read [API reference](references/api-reference.md) for constructor signatures, shape tables, function-space families, multi-output strategy rules, and ZCS support boundaries.
4. Read [troubleshooting](references/troubleshooting.md) when labels, branch/trunk widths, PDE auxiliary variables, function-space sensors, or ZCS derivatives fail.
5. For a minimal supervised aligned DeepONet sanity check, run [scripts/smoke_deeponet_aligned.py](scripts/smoke_deeponet_aligned.py). It defaults to `DDE_BACKEND=pytorch`, uses synthetic data, performs one Adam iteration, and does not require a GPU.

## Routing boundaries

- Generic `Model.compile`, `Model.train`, prediction batching, metrics, checkpoints, and callbacks belong in [training workflows](../training-workflows/SKILL.md).
- Backend installation, `DDE_BACKEND`, dtype/autodiff defaults, GPU, and Horovod setup belong in [backend and configuration](../backend-and-configuration/SKILL.md).
- Ordinary PINN residual and boundary-condition recipes that do not use an operator data class belong in [PINN problem setup](../pinn-problem-setup/SKILL.md).

## Verification scope

This construction verified a PyTorch CPU environment and a standard aligned DeepONet smoke path. TensorFlow, JAX, Paddle, GPU/Horovod, and full PI-DeepONet/ZCS training are optional or alternative paths and are not claimed as runtime-verified here unless a future verification report adds them.
