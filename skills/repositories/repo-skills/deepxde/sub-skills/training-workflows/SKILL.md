---
name: training-workflows
description: "Guide DeepXDE model lifecycle, optimizers, callbacks, prediction,
  checkpoints, plotting, function fitting, tabular data, and multifidelity
  training workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 2.1
---

# DeepXDE Training Workflows

Use this sub-skill after the user already has compatible DeepXDE `data` and `net` objects and needs to train, checkpoint, resume, predict, or diagnose a `dde.Model` workflow. This construction verified PyTorch CPU behavior; TensorFlow, JAX, Paddle, GPU, and Horovod behavior should be treated as optional or backend-specific unless separately verified.

## Route first

- PDE residuals, geometry, boundary/initial conditions, inverse-variable setup, and adaptive sampling point design: [../pinn-problem-setup/SKILL.md](../pinn-problem-setup/SKILL.md).
- Backend installation, backend selection, dtype, autodiff, seed, XLA, GPU, Horovod, or parallel setup: [../backend-and-configuration/SKILL.md](../backend-and-configuration/SKILL.md).
- DeepONet/MIONet/PDEOperator data shapes and operator-network construction: [../operator-learning/SKILL.md](../operator-learning/SKILL.md).

## Read these bundled references

- [references/model-lifecycle.md](references/model-lifecycle.md): concrete `Model(data, net)` lifecycle, `compile`, `train`, optimizers, callbacks, predict, save/restore, metrics, and plotting.
- [references/data-and-function-workflows.md](references/data-and-function-workflows.md): `Function`, `DataSet`, `MfFunc`, and `MfDataSet` data contracts and shape checks.
- [references/troubleshooting.md](references/troubleshooting.md): optimizer/backend/plot/checkpoint/convergence failure triage.

## Safe smoke check

Run the bundled function-approximation smoke when you need to confirm the training loop and PyTorch CPU backend before adapting a larger problem:

```bash
python scripts/smoke_function_approximation.py --iterations 3 --num-train 8 --num-test 16
```

The script sets `DDE_BACKEND=pytorch` before importing DeepXDE unless the environment already sets a backend, uses a tiny `dde.data.Function` + `dde.nn.FNN`, performs no plotting, writes only to a caller-selected output directory when requested, and prints a JSON summary.

## Minimal lifecycle pattern

```python
import deepxde as dde

model = dde.Model(data, net)
model.compile("adam", lr=1e-3, metrics=["l2 relative error"])
losshistory, train_state = model.train(iterations=1000, display_every=100)
y_pred = model.predict(x_eval)
```

Keep the `data` and `net` compatible with the selected backend. For PDE and TimePDE training, do not use `batch_size`; resample PDE or boundary points with `dde.callbacks.PDEPointResampler` instead. For ordinary function, tabular, multifidelity, and operator datasets, follow the data-specific batching rules in the references.
