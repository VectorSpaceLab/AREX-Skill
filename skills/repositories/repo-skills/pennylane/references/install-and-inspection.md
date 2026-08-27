# Install and inspection guide

## Installation surfaces

PennyLane requires Python 3.12 or newer in this repo snapshot. For package users, the public base install is:

```bash
python -m pip install pennylane
```

For source-checkout work, use an isolated environment and install the checkout in editable mode only when the task requires local edits:

```bash
python -m pip install -e .
```

Do not install broad optional groups by default. Select extras or additional packages only when the workflow needs them.

## Base dependencies observed from package metadata

The base package depends on scientific and quantum runtime packages including `numpy>=2.0`, `scipy`, `networkx`, `rustworkx`, `autograd<1.9`, `autoray==0.8.10`, `pennylane-lightning>=0.45`, `requests`, `tomlkit`, `typing_extensions`, `packaging`, `diastatic-malt`, and `gast`.

Optional groups in this snapshot include `kernels`, dependency groups for `qchem`, `qcut`, `external-libraries`, `docs`, `doctest`, `dev`, and CI/reporting. These are not required for core QNode work.

## Minimal smoke checks

Run the bundled root smoke script against the active environment:

```bash
python path/to/pennylane/scripts/pennylane_smoke.py
```

Expected signals:

- `import pennylane` succeeds.
- `qp.version()` prints a version string.
- A `default.qubit` device executes a two-wire QNode.
- `qp.grad` returns a numeric derivative for a trainable `qp.numpy.array`.

For one-off inspection:

```python
import inspect
import pennylane as qp
print(qp.version())
print(inspect.signature(qp.QNode))
print(inspect.signature(qp.qnode))
print(inspect.signature(qp.device))
```

Live signatures verified for this snapshot include:

- `qp.QNode(func, device, interface='auto', diff_method='best', *, shots='unset', grad_on_execution='best', cache='auto', cachesize=10000, max_diff=1, device_vjp=False, postselect_mode=None, mcm_method=None, gradient_kwargs=None, static_argnums=(), executor_backend=None)`
- `qp.qnode(...)` with the same constructor settings as `QNode`
- `qp.device(name, *args, **kwargs)`
- `qp.grad(func, argnums=None, h=None, method=None)`
- `qp.execute(tapes, device, diff_method=None, interface='auto', *, grad_on_execution='best', cache='auto', cachesize=10000, max_diff=1, device_vjp=False, postselect_mode=None, mcm_method=None, gradient_kwargs=None, transform_program=None, executor_backend=None)`

## Console entry point

The repo exposes `pl-device-test` as a console script from `pennylane.devices.tests:cli`.

```bash
pl-device-test --help
```

Use it for plugin/device conformance tasks. Typical flags include `--device`, `--shots`, `--analytic`, `--skip-ops`, `--device-kwargs KEY=VAL`, and `--disable-opmath`.

## Backend policy

Core PennyLane workflows are CPU-verifiable with built-in simulators. Do not claim optional backend support unless the environment proves it:

- GPU simulators such as Lightning GPU require external plugin packages, CUDA-compatible wheels, a driver, and hardware.
- Torch and JAX interfaces require their packages and sometimes their own accelerator wheels.
- TensorFlow support is no longer maintained in the docs for this snapshot.
- Catalyst/qjit workflows require Catalyst runtime support outside the base package.
- Qchem, qcut, kernels, and external-library workflows may need optional packages such as OpenFermion/PySCF, CVX solvers, KAHYPAR, PyZX, Stim, Quimb, OpenQASM3, or Qualtran.

If a requested workflow names one of those surfaces, first install and smoke-check only the needed optional dependency set; never use a CPU import as proof of a GPU/plugin claim.
