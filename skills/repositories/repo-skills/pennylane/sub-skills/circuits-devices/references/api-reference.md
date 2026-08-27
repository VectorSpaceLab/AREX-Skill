# Circuits and devices API reference

## QNode and qnode

Verified signature shape:

```python
qp.QNode(func, device, interface="auto", diff_method="best", *, shots="unset",
         grad_on_execution="best", cache="auto", cachesize=10000,
         max_diff=1, device_vjp=False, postselect_mode=None,
         mcm_method=None, gradient_kwargs=None, static_argnums=(),
         executor_backend=None)
```

`qp.qnode` exposes the same settings as a decorator. Important knobs:

- `interface`: `"auto"` by default; set explicitly when crossing into JAX/Torch/Autograd behavior.
- `diff_method`: `"best"` by default; route gradient-specific decisions to the gradients sub-skill.
- `shots`: use `"unset"` to inherit, `None` for analytic behavior where supported, or an integer/shot vector for sampling.
- `postselect_mode` and `mcm_method`: advanced mid-circuit measurement behavior; choose only when the circuit has mid-circuit measurements or postselection.
- `executor_backend`: advanced execution backend selection; verify before claiming concurrency or distributed behavior.

## Device loader

```python
qp.device(name, *args, **kwargs)
```

Common built-in devices in this snapshot include:

- `default.qubit`: general CPU state-vector simulation.
- `default.mixed`: density-matrix/noisy workflows.
- `default.clifford`: Clifford-specialized simulation.
- `default.tensor`: tensor-network style simulation.
- `reference.qubit`: reference behavior checks.
- `null.qubit`: no-op style execution for dry checks and certain resource workflows.
- `lightning.qubit`: available through the base dependency `pennylane-lightning` in the inspected environment.

External plugins register additional device names. Do not assume a device exists without importing its package and checking entry points.

## Measurements

Quantum functions must return one measurement process or a tuple of measurement processes. Common functions:

- `qp.expval(op)`: expectation value.
- `qp.var(op)`: variance.
- `qp.probs(wires=None, op=None)`: probability vector.
- `qp.sample(op=None, wires=None, dtype=None)`: samples; requires finite shots.
- `qp.counts(op=None, wires=None, all_outcomes=False)`: sample counts; requires finite shots.
- `qp.state()`: state vector where the device supports it.
- `qp.density_matrix(wires=...)`, `qp.vn_entropy`, `qp.purity`, `qp.mutual_info`: state-derived quantities.
- `qp.classical_shadow` and `qp.shadow_expval`: shadow measurements.

Return-shape discipline matters. For tuples, inspect each result separately instead of assuming one array shape.

## Execution and drawing

`qp.execute(tapes, device, diff_method=None, interface="auto", ..., transform_program=None)` is the lower-level batch execution API. Prefer QNodes unless the task explicitly manipulates tapes or transform programs.

Drawing helpers:

```python
qp.draw(qnode, wire_order=None, show_all_wires=False, decimals=2,
        max_length=100, show_matrices=True, show_wire_labels=True,
        level="gradient")

qp.draw_mpl(qnode, wire_order=None, show_all_wires=False, decimals=None,
            style=None, max_length=None, fig=None, level="gradient", **kwargs)
```

Use `level="user"`, `"device"`, `"gradient"`, or transform-program levels when explaining why a drawn circuit differs before/after compilation or gradient transforms.

## Device-test CLI

`pl-device-test` options observed from help:

- `--device DEVICE`
- `--shots SHOTS`
- `--analytic ANALYTIC`
- `--skip-ops`
- `--device-kwargs KEY=VAL [KEY=VAL ...]`
- `--disable-opmath DISABLE_OPMATH`

Use this CLI when validating a PennyLane-compatible device or plugin, not for ordinary QNode user code.
