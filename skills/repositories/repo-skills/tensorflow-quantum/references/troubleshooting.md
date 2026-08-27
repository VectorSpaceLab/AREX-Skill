# Troubleshooting

This page covers cross-cutting install, import, version, and smoke-check failures.

## Legacy Keras or TensorFlow import errors

### Symptom
TensorFlow or TFQ import fails, or the runtime behaves like Keras 3 when the package expects legacy Keras.

### Likely cause
`TF_USE_LEGACY_KERAS=1` was not set before Python imported TensorFlow or TensorFlow Quantum.

### Recovery
- Start a new process.
- Export `TF_USE_LEGACY_KERAS=1` before the first import.
- Re-run `python -m pip check`.
- Re-run `python scripts/tfq_smoke_check.py --quick`.

## Dependency mismatch or broken install

### Symptom
`pip check` reports conflicts, or the smoke helper imports TensorFlow but fails later with version or ABI errors.

### Likely cause
The installed TensorFlow, TF-Keras, Cirq, NumPy, or SciPy versions do not satisfy the package metadata.

### Recovery
- Reinstall the companion stack listed in `references/installation-and-compatibility.md`.
- Keep the environment on Python 3.10-3.12.
- Retry `python -m pip check` and the bundled smoke helper.

## Source checkout shadows the installed wheel

### Symptom
Running `python -c "import tensorflow_quantum"` from a source checkout fails with an error such as `cannot import name 'pauli_sum_pb2'` even though the wheel installation works elsewhere.

### Likely cause
The current working directory is a source checkout, so Python imports the checkout package instead of the installed wheel. A source checkout can require generated proto or compiled op artifacts that a wheel already includes.

### Recovery
- Run installed-package checks from outside the source checkout, or run the bundled smoke helper by absolute path.
- If source-checkout import is the real goal, build/install the checkout with its native build workflow and refresh the skill after source metadata changes.
- Do not treat this as a package-wheel failure until the same import fails outside the checkout.

## Package version mismatch

### Symptom
`tfq.__version__` does not match the provenance snapshot, or you are using a different checkout than the one this skill was generated from.

### Likely cause
The skill is stale for the current repository state.

### Recovery
- Compare the checkout against `references/repo-provenance.md`.
- If the commit or package metadata changed, refresh the skill.
- Do not treat a stale skill as current just because import smoke still passes.

## Smoke helper fails on GPU-related warnings

### Symptom
The smoke helper prints CUDA plugin or no-device warnings, but the CPU checks still complete.

### Likely cause
TensorFlow detected GPU libraries on the host even though the smoke path is CPU-only.

### Recovery
- Keep the smoke focused on CPU behavior unless a GPU backend is intentionally required.
- If the helper actually fails, re-check the install and the legacy-Keras setup.

## Route to the right sub-skill

- Low-level tensor or backend issues: `sub-skills/tensor-ops-and-execution/SKILL.md`
- Keras layer wiring or noisy readout issues: `sub-skills/keras-quantum-layers/SKILL.md`
- Differentiator or optimizer issues: `sub-skills/differentiation-and-optimizers/SKILL.md`
- Dataset downloads or notebook recipe issues: `sub-skills/datasets-and-tutorials/SKILL.md`
