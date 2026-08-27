# DeepXDE model lifecycle, training, callbacks, and checkpoints

This reference covers the DeepXDE training surface after a valid `data` object and compatible `net` object already exist. It avoids PDE residual construction and operator-data details, which are routed to sibling sub-skills.

## Core API signatures

| API | Signature | Purpose and notes |
| --- | --- | --- |
| `dde.Model` | `Model(data, net)` | Wrap a `deepxde.data.Data` instance and a `deepxde.nn.NN` instance. The model owns optimizer state, callbacks, `losshistory`, and `train_state`. |
| `Model.compile` | `compile(optimizer, lr=None, loss="MSE", metrics=None, decay=None, loss_weights=None, external_trainable_variables=None, verbose=1)` | Configure backend training functions. Call once before `train`, and call again after structural changes such as a changed number of PDE/BC losses. |
| `Model.train` | `train(iterations=None, batch_size=None, display_every=1000, disregard_previous_best=False, callbacks=None, model_restore_path=None, model_save_path=None, epochs=None, verbose=1)` | Train and return `(losshistory, train_state)`. `epochs` is a deprecated alias for `iterations`. |
| `Model.predict` | `predict(x, operator=None, callbacks=None)` | Predict network output for NumPy inputs, or evaluate a two-argument operator such as a PDE residual. Three-argument operators with auxiliary variables are not implemented for PyTorch/JAX/Paddle prediction in this version. |
| `Model.save` | `save(save_path, use_iteration_suffix=True, protocol="backend", verbose=0)` | Save backend state and return the concrete checkpoint path. With the default suffix, an iteration number is inserted before the backend extension. |
| `Model.restore` | `restore(save_path, device=None, verbose=0)` | Restore a concrete checkpoint path. `device` remapping is supported only by the PyTorch backend. |

## Practical lifecycle recipes

### Fresh training

```python
model = dde.Model(data, net)
model.compile(
    "adam",
    lr=1e-3,
    loss="MSE",
    metrics=["l2 relative error"],
)
losshistory, train_state = model.train(
    iterations=5000,
    display_every=500,
    callbacks=[],
)
y = model.predict(x_eval)
```

Use `display_every` as the cadence for printed validation/test losses and metrics. `train_state` tracks current and best training state; `losshistory` stores step, train losses, test losses, and metrics.

### Adam warm-up followed by L-BFGS

```python
model.compile("adam", lr=1e-3)
model.train(iterations=2000, display_every=200)

dde.optimizers.set_LBFGS_options(maxiter=500, ftol=1e-12, gtol=1e-12)
model.compile("L-BFGS")
losshistory, train_state = model.train(display_every=50)
```

L-BFGS is an external optimizer. In PyTorch, `lr` and `decay` are ignored for `"L-BFGS"`; use `dde.optimizers.set_LBFGS_options(...)` before `compile`. If L-BFGS appears to stop early or stagnate, consider `dde.config.set_default_float("float64")` before model/data construction and rerun in an environment where the backend supports it.

### Checkpoint and resume

```python
# Save at train end.
losshistory, train_state = model.train(
    iterations=1000,
    model_save_path="checkpoints/runA",
)
# Model.save returns a concrete path such as checkpoints/runA-1000.pt on PyTorch.

# Save periodically during training.
checkpoint = dde.callbacks.ModelCheckpoint(
    "checkpoints/runA",
    save_better_only=True,
    period=100,
    monitor="test loss",
)
model.train(iterations=5000, display_every=100, callbacks=[checkpoint])

# Resume into an identically constructed data/net/model, compiled first.
model2 = dde.Model(data2, net2)
model2.compile("adam", lr=1e-3)
model2.restore("checkpoints/runA-1000.pt", device="cpu")
model2.train(iterations=1000, disregard_previous_best=True)
```

Checkpoint portability is backend-specific. PyTorch saves `.pt` files containing model and optimizer state; TensorFlow and Paddle use their own formats. `protocol="pickle"` saves a Python pickle but is not the protocol to use with `restore()`.

## Compile options

### Optimizer names

Common PyTorch-verified optimizer strings include:

- `"adam"`, `"adamw"`, `"sgd"`, `"rmsprop"` for standard mini-batch style updates. These require `lr`.
- `"L-BFGS"` and `"L-BFGS-B"` for backend external L-BFGS flows. PyTorch treats both as `torch.optim.LBFGS` and ignores `lr`/`decay`.
- `"NNCG"` for PyTorch NysNewtonCG. It is beta, PyTorch-only, ignores `lr`/`decay`, and must be configured through `dde.optimizers.set_NNCG_options(...)`.

Other backends expose different optimizer sets. Treat non-PyTorch optimizer behavior as unverified in this construction unless separately tested.

### Losses, metrics, and weights

- `loss` can be one loss identifier/callable used for every loss component, or a list matching the number of data loss components.
- Common loss identifiers include `"MSE"`, `"mean squared error"`, `"MAE"`, `"mean absolute error"`, `"mean l2 relative error"`, and backend-specific entries such as percentage/cross-entropy losses.
- `metrics` is a list evaluated on the model test data at each displayed test step. Common metric identifiers include `"l2 relative error"`, `"mean l2 relative error"`, `"nanl2 relative error"`, `"mean squared error"`, `"MSE"`, `"MAPE"`, `"max APE"`, and `"APE SD"`.
- `loss_weights=[...]` multiplies individual loss components before summing. For PDE problems, order must match the data object's residual/BC loss ordering; if the number of BCs changes due to resampling, recompile.

### Learning-rate decay

Use the decay tuple supported by the selected backend. PyTorch supports:

| Decay tuple | Meaning |
| --- | --- |
| `("step", step_size, gamma)` | `torch.optim.lr_scheduler.StepLR` |
| `("cosine", T_max, eta_min)` | `torch.optim.lr_scheduler.CosineAnnealingLR` |
| `("inverse time", decay_steps, decay_rate)` | Lambda schedule `1 / (1 + decay_rate * step / decay_steps)` |
| `("exponential", gamma)` | `torch.optim.lr_scheduler.ExponentialLR` |
| `("lambda", lambda_fn)` | `torch.optim.lr_scheduler.LambdaLR` |

Do not pass decay to L-BFGS/NNCG expecting it to tune those optimizers in PyTorch; the code warns that learning rate is ignored.

### External trainable variables

`external_trainable_variables` accepts one `dde.Variable` or a list of variables for inverse problems or trainable physical constants. On TensorFlow v1 compatibility backend this argument is ignored because all trainable `dde.Variable` objects are collected automatically. On PyTorch, L-BFGS does not support per-parameter options; if L2 regularization is set, DeepXDE warns that it also applies to external variables.

## `train()` details and batch-size rules

| Data/workflow | Use `batch_size`? | Rule |
| --- | --- | --- |
| `dde.data.PDE` / `dde.data.TimePDE` | No | Leave `batch_size=None`. To change sampled PDE/BC points while training, use `dde.callbacks.PDEPointResampler`. |
| `dde.data.Function` | Usually no | The implementation returns the full sampled function data. `online=True` resamples pseudorandom points each step. |
| `dde.data.DataSet` | No effect in this version | `train_next_batch` returns the full arrays. If you need true mini-batches, verify the specific data class supports them or use operator data classes routed to the operator sub-skill. |
| `dde.data.MfFunc` / `dde.data.MfDataSet` | No effect in this version | Full low/high-fidelity arrays are returned. Ensure outputs are a list of low/high targets. |
| DeepONet Cartesian product data | Yes, with special rules | An integer batches the branch input; a tuple batches `(branch_batch, trunk_batch)`. Route shape details to the operator sub-skill. |
| `PointSetBC` / `PointSetOperatorBC` inside PDE workflows | Class-level batch size | Use the BC object's `batch_size` and `PDEPointResampler(..., bc_points=True)` when supported by the backend, not `Model.train(batch_size=...)`. |

`iterations` counts weight-update steps for standard optimizers. For external optimizers, the effective number of internal optimizer iterations is controlled by backend-specific optimizer options; `train(iterations=...)` may be ignored for L-BFGS flows.

## Callback catalog

| Callback | Constructor | Use when | Caveats |
| --- | --- | --- | --- |
| `ModelCheckpoint` | `ModelCheckpoint(filepath, verbose=0, save_better_only=False, period=1, monitor="train loss")` | Save snapshots during training. `monitor` is `"train loss"` or `"test loss"`. | With `save_better_only=True`, improvement is checked only when the train loop updates validation/test losses at `display_every`. |
| `EarlyStopping` | `EarlyStopping(min_delta=0, patience=0, baseline=None, monitor="loss_train", start_from_epoch=0)` | Stop when `loss_train` or `loss_test` stops improving. | Monitor names differ from `ModelCheckpoint`: use `"loss_train"` or `"loss_test"`. |
| `Timer` | `Timer(available_time)` | Stop after approximately `available_time` minutes. | Checked at epoch/iteration boundaries. |
| `PDEPointResampler` | `PDEPointResampler(period=100, pde_points=True, bc_points=False)` | Resample PDE training points and optionally BC points. | If `num_bcs` changes, DeepXDE raises and asks you to recompile. BC point resampling is backend-limited; PyTorch/Paddle are supported in the source code for `bc_points=True`. |
| `VariableValue` | `VariableValue(var_list, period=1, filename=None, precision=2)` | Log external trainable variables or inverse parameters. | Writes to stdout by default or keeps the target file open. Use a deliberate output path. |
| `OperatorPredictor` | `OperatorPredictor(x, op, period=1, filename=None, precision=2)` | Log an operator value such as a residual/derivative at fixed points. | `op` must be a two-argument operator `(inputs, outputs)`; backend tensor ops must match the selected backend. |
| `DropoutUncertainty` | `DropoutUncertainty(period=1000)` | Estimate uncertainty via MC dropout. | Designed for networks with dropout; warning in source says not to combine with techniques that behave differently in train/test such as batch normalization. PyTorch support is not advertised by the original function example and should be verified before relying on it. |

Callbacks are passed as a list to `model.train(..., callbacks=[...])`. Prediction callbacks can also be passed to `model.predict(..., callbacks=[...])`, but many built-in callbacks are training-oriented.

## Prediction and residual evaluation

Plain prediction:

```python
x_eval = np.linspace(-1, 1, 101)[:, None]
y_pred = model.predict(x_eval)
```

Operator prediction for a PDE-style residual:

```python
def residual(inputs, outputs):
    # Use backend tensor operations and dde.grad here.
    return dde.grad.jacobian(outputs, inputs, i=0, j=0)

r = model.predict(x_eval, operator=residual)
```

For PyTorch, JAX, and Paddle in this version, `Model.predict` raises `NotImplementedError` for three-argument operators requiring auxiliary variables. If your PDE data used `auxiliary_var_function` and your residual needs auxiliary variables at prediction time, route the issue to backend-specific verification rather than assuming PyTorch support.

## Plotting and result files

`dde.saveplot(losshistory, train_state, issave=True, isplot=True, output_dir=None)` saves loss/train/test text files and optionally displays Matplotlib plots. In noninteractive agents, CI, or headless servers:

```python
dde.saveplot(losshistory, train_state, issave=True, isplot=False, output_dir="outputs")
```

Avoid `isplot=True` unless an interactive display or noninteractive Matplotlib backend has been configured. The bundled smoke script intentionally does not call `saveplot`.
