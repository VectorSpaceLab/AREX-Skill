# Cross-Cutting Troubleshooting

## `jaxlib==0.4.13` cannot be resolved

Symptom: `pip install waymo-open-dataset-tf-2-12-0==1.6.7` fails with no matching distribution for `jaxlib==0.4.13`.

Likely causes:
- Python version is too new for the old JAXlib wheel.
- The package index mirror does not expose older JAX release wheels.

Recovery:
1. Use Python 3.10 for WOD `1.6.7`.
2. Add the official JAX release links: `-f https://storage.googleapis.com/jax-releases/jax_releases.html`.
3. If a newer TensorFlow-specific WOD wheel is available, prefer that for newer Python versions instead of forcing old dependencies.

## TensorFlow reports no CUDA libraries

Symptom: TensorFlow imports but prints CUDA/TensorRT warnings or lists no GPU devices.

This is acceptable for CPU WOD utilities, V2 component work, metric config inspection, and most documentation tasks. It is not proof of GPU challenge timing or model inference. For GPU-specific tasks, prepare a TensorFlow GPU environment that matches the user's driver, CUDA runtime, and challenge model stack, then rerun a device allocation smoke.

## WOD package imports but optional camera segmentation fails

Symptom: `ModuleNotFoundError: deeplab2` from camera segmentation metrics.

Camera segmentation metrics have an optional Deeplab2 dependency. Use `camera-and-segmentation` troubleshooting to decide whether to install it. Do not install it just to use unrelated WOD utilities.

## Dataset access versus package APIs

The package does not bundle full Waymo datasets. If a task needs real frames, motion scenarios, E2E driving logs, challenge assets, or benchmark submissions, confirm that the user has dataset access, accepted the applicable terms, and has local files or cloud paths. Use synthetic/bundled script checks only for package and workflow validation.

## Source checkout is not required for this skill

The generated scripts and references are self-contained. If a task asks to edit or test the upstream repository checkout, use `repo-build-test`; otherwise, work from the installed package and user-provided data.
