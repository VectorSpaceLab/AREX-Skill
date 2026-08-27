# Compatibility and installation

## Supported operating contract

This skill targets DLTK 0.2.1 and the TensorFlow 1.x graph-era public API. The
source package imports or uses `tf.Session`, `tf.placeholder`, `tf.layers`,
`tf.contrib`, `tf.train`, `tf.data.Dataset.make_initializable_iterator`, and
`tf.estimator`. A known-compatible reference configuration is Python 3.7 with
TensorFlow 1.15 and dependency pins that retain the removed NumPy aliases used
by some legacy paths.

The repository's public declarations are historical and inconsistent: its
README describes TensorFlow >=1.4, while its legacy requirements pin
`tensorflow-gpu==1.3.0`. Treat those as evidence of the era, not as a modern
resolver specification. Choose one coherent TensorFlow 1.x stack and verify
all required symbols before running an application. Do not claim TensorFlow
2.x compatibility, current CUDA support, or a successful migration merely
because a compatibility namespace makes an import pass.

## Minimal probe

Run the root `scripts/check_environment.py` from any working directory. A
successful probe should report:

- a TensorFlow version beginning with `1.`;
- `Session`, `layers`, `contrib`, and `estimator` attributes;
- DLTK package metadata version `0.2.1`; and
- imports for the selected DLTK core, IO, network, and utility modules.

A caller may use a different Python 3/TensorFlow 1.x environment, but must
repeat the probe and document any dependency variation. The package metadata
alone is not proof that every optional application dependency is installed.
SimpleITK is needed for NIfTI workflows, pandas for CSV-driven applications,
and the TensorFlow 1.x deployment predictor is needed for the historical
SavedModel path.

## Backend policy

CPU is the verified baseline for package semantics, tiny graph execution,
Reader behavior, and the selected native tests. CUDA is optional and
unverified for this skill: DLTK's historical GPU requirements predate modern
GPU driver/toolkit combinations, and no selected capability is GPU-exclusive.
A CPU check therefore proves functional semantics only, not GPU throughput or
modern accelerator compatibility. ROCm, MPS, and vendor accelerators are not
part of this package contract.

## Dependency hazards

- Keep NumPy and protobuf within the compatibility range of the selected
  TensorFlow 1.x wheel. Modern NumPy may expose removed aliases or reject the
  package's legacy indexing patterns.
- `SimpleITK`, NIfTI files, and dataset permissions are separate from the core
  import gate. Do not silently replace missing medical-image dependencies with
  fake successful reads.
- The examples may import plotting, notebook, CSV, or image packages that are
  not needed by the core API. Install only what the selected workflow needs.
- If a required symbol or module is missing, stop at the gate and report the
  exact mismatch. Do not mutate a caller's existing environment without an
  explicit decision.
