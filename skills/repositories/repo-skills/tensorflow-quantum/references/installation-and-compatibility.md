# Installation and Compatibility

## What to install

- Public package name: `tensorflow-quantum`
- Import name: `tensorflow_quantum`
- Supported Python range from the repo docs: 3.10 through 3.12
- Installed-package inspection during construction confirmed the public package surface and a working CPU smoke path.

## Public install path

Start with the published package:

```bash
python -m pip install tensorflow-quantum
python -m pip check
```

If you also need the documented TensorFlow companion stack in the same environment, install the compatible pair and set the legacy-Keras flag before importing TensorFlow or TFQ:

```bash
python -m pip install tensorflow==2.19.1 tf-keras==2.19.0
export TF_USE_LEGACY_KERAS=1
```

## Compatibility notes

The repository metadata and release setup pin or constrain the following package families:

| Dependency | Compatibility note |
|---|---|
| TensorFlow | Docs target 2.19.1 for the current source checkout. |
| TF-Keras | Use the legacy `tf-keras` package and set `TF_USE_LEGACY_KERAS=1` before import. |
| Cirq | Package metadata pins `cirq-core==1.5.0` and `cirq-google==1.5.0`. |
| NumPy | Package metadata expects NumPy 2.x. |
| SciPy | Package metadata constrains `scipy>=1.15.3,<2`. |
| SymPy | Package metadata pins `sympy==1.14`. |
| JAX | Package metadata constrains `jax>=0.5,<0.6`. |
| contourpy | Package metadata constrains `contourpy<=1.3.2`. |

## Minimal import check

After installation, confirm the package imports and reports a version:

```bash
TF_USE_LEGACY_KERAS=1 python -c "import tensorflow_quantum as tfq; print(tfq.__version__)"
```

For a slightly deeper check, use the bundled smoke helper:

```bash
TF_USE_LEGACY_KERAS=1 python scripts/tfq_smoke_check.py --quick
# Optional deeper package checks:
TF_USE_LEGACY_KERAS=1 python scripts/tfq_smoke_check.py --quick --layers --datasets --differentiators --math
```

## Version and refresh reminders

- If `tfq.__version__` changes materially from the provenance snapshot, refresh this skill.
- If package resolution pulls a different TensorFlow or TF-Keras combination, re-run `python -m pip check` and the smoke helper before trusting the install.
- If you are working from a source checkout rather than a wheel, keep the source setup notes separate from the runtime skill and refresh the skill when the package metadata changes.
