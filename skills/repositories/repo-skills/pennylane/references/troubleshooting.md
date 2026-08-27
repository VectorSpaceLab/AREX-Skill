# Cross-cutting troubleshooting

## Import or install failures

Symptoms:
- `ModuleNotFoundError: No module named 'pennylane'`.
- Import fails on a base dependency such as `autograd`, `autoray`, `rustworkx`, `scipy`, or `pennylane_lightning`.
- A local source checkout imports instead of the intended installed wheel.

Recovery:
1. Confirm Python is 3.12 or newer for this snapshot.
2. Run `python -m pip show pennylane` and `python -m pip check` in the active environment.
3. If using a checkout, prefer `python -m pip install -e .` inside an isolated environment.
4. Re-run `python scripts/pennylane_smoke.py` from this skill or copy its code into the active environment.
5. Do not fix by installing every optional group; map the failing import to the workflow first.

## Device not found or wrong backend

Symptoms:
- `DeviceError` or a message that a named device is not installed.
- A task asks for `lightning.gpu`, hardware, or a vendor device but only base PennyLane is installed.

Recovery:
1. Check `qp.device('default.qubit', wires=...)` first to separate package import from plugin installation.
2. Use `qp.device.__globals__['_get_device_entrypoints']()` only for temporary inspection; do not depend on that private function in user code.
3. For external plugins, install the plugin package and run its own smoke test before using it in QNodes.
4. Treat CUDA/ROCm/MPS as optional unless the user explicitly selected that backend and the hardware/wheel combination is verified.

## Measurements and shot confusion

Symptoms:
- Unexpected scalar/vector/dictionary shapes.
- `sample`/`counts` unavailable or nondeterministic under analytic execution.
- Mixed measurement returns are hard to compare.

Recovery:
1. Confirm the QNode `shots` setting. Analytic shots (`shots=None`) support expectation/state/probability-style outputs, while sampling/counts need finite shots.
2. For finite-shot workflows, use `qp.set_shots` or construct/update the QNode/device with the desired shots.
3. Keep measurement returns homogeneous when possible. If returning tuples, assert each element's shape separately.
4. Use the circuits/devices troubleshooting reference for mid-circuit measurement and postselection options.

## Gradients report no trainable parameters

Symptoms:
- Warning: attempted to differentiate a function with no trainable parameters.
- `qp.grad` returns an empty tuple.

Recovery:
1. With Autograd, pass `qp.numpy.array(value, requires_grad=True)` or set `argnums` explicitly.
2. With JAX/Torch, use arrays/tensors from that framework and set `interface='jax'` or `interface='torch'` when auto-detection is ambiguous.
3. Confirm the QNode returns differentiable measurements such as expectation values, not raw samples.
4. Confirm the chosen `diff_method` works on the device and operations.

## Optional dependency failures

Symptoms:
- QASM/Qiskit/PyQuil/Qualtran converters fail to import external packages.
- Qchem tests fail on OpenFermion/PySCF or basis/external solver imports.
- Kernels/qcut workflows ask for CVX/KAHYPAR/opt_einsum extras.

Recovery:
1. Read the owning sub-skill and identify the smallest optional dependency set.
2. Install only that dependency set in an isolated environment.
3. Re-run a tiny workflow or import check before claiming support.
4. If network, credentials, datasets, or hardware are required, state the limitation and avoid destructive retries.

## Dataset/network/cache issues

Symptoms:
- Dataset load hangs or fails on network/cache/download errors.
- Remote dataset attributes are unavailable.

Recovery:
1. Do not make network mandatory for core skill verification.
2. Check `qp.data.load` parameters: `data_name`, `attributes`, `folder_path`, `force`, `num_threads`, `block_size`, `progress_bar`, and dataset-specific filters.
3. Use a temporary folder for experiments and preserve user cache directories unless instructed otherwise.
4. If a user needs an offline workflow, require a pre-downloaded dataset or an explicit local path.

## Source-checkout policy failures

Symptoms:
- Tests import an optional framework without a pytest marker.
- Lint/format/tach failures appear after a code change.
- A proposed GitHub comment or PR body contains unmarked AI-generated text.

Recovery:
1. Read `references/development-conventions.md` and `sub-skills/repo-development/`.
2. Run focused tests before linting.
3. Use the proper `.pylintrc` for source vs tests, then run `black`, `isort`, and `tach check` as relevant.
4. Never interact with GitHub autonomously; get explicit human approval for exact content.
