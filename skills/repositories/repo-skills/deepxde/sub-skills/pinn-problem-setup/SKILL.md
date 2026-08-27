---
name: pinn-problem-setup
description: "Assemble DeepXDE forward and inverse PINN problems with geometry,
  residuals, conditions, data classes, and sampling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 2.1
---

# PINN problem setup

Use this sub-skill when a task needs the DeepXDE objects that define a physics-informed problem: geometry, time domain, PDE residual callbacks, boundary/initial/point-set constraints, inverse variables, and `dde.data.PDE`-family data objects. It is the setup layer before model compile/train/predict.

## Route first

- Backend selection, installation, dtype, random seed, autodiff mode, GPU, or Horovod questions: use `../backend-and-configuration/SKILL.md`.
- Optimizers, callbacks, save/restore, plotting, training schedules, metrics, or prediction lifecycle: use `../training-workflows/SKILL.md`.
- DeepONet, PI-DeepONet, MIONet, Cartesian-product operator data, or operator networks: use `../operator-learning/SKILL.md`.

## Setup checklist

1. Select the geometry and optional time domain. Use `dde.geometry.Interval`, `Rectangle`, `Disk`, `Cuboid`, `Hypercube`, `Hypersphere`, polygonal/point-cloud geometries, CSG (`|`, `-`, `&`), and `GeometryXTime` as appropriate.
2. Write the residual callback as `def pde(x, y): ...` (or `def pde(x, y, int_mat): ...` for IDE/FPDE). Use backend tensor operations inside the residual and DeepXDE gradients (`dde.grad.jacobian`, `dde.grad.hessian`).
3. Add soft constraints with `dde.icbc.*` classes or exact constraints with `net.apply_output_transform`.
4. Pick `dde.data.PDE`, `TimePDE`, `IDE`, or `FPDE`, including `num_domain`, `num_boundary`, `num_initial`, `train_distribution`, `anchors`, `exclusions`, and `num_test` deliberately.
5. For inverse PINNs, create `dde.Variable` unknowns, use them inside the residual, and pass them to `Model.compile(..., external_trainable_variables=...)` in the training workflow.

## References

- Build complete forward/inverse workflows from [references/pinn-workflows.md](references/pinn-workflows.md).
- Check constructor signatures, shape contracts, and backend verification notes in [references/api-reference.md](references/api-reference.md).
- Diagnose residual, BC, point-set, sampling, and exact-constraint failures with [references/troubleshooting.md](references/troubleshooting.md).

## Smoke script

Run the bundled tiny PyTorch CPU-safe Poisson smoke when you need to check that basic problem assembly, compile, one or two training iterations, prediction, and residual prediction work:

```bash
python scripts/smoke_poisson_1d.py --help
python scripts/smoke_poisson_1d.py --iterations 2
```

The bundled smoke runs only with the PyTorch backend and sets `DDE_BACKEND=pytorch` for the run. This construction verified PyTorch CPU for the basic `PDE` path; TensorFlow, JAX, Paddle, GPU, Horovod, and backend-limited IDE/FPDE examples are optional alternatives and must be verified before relying on them.
