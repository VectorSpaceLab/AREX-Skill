---
name: operation-reference
description: "Choose and configure Augmentor operations, validation ranges, and
  custom Operation subclasses."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Augmentor operation reference

Use this sub-skill when a task is about selecting image augmentation operations, setting operation parameters, recovering from operation validation errors, or adding a custom `Augmentor.Operations.Operation` subclass to a pipeline.

## Fast routing

- Need method signatures, valid ranges, and exact recovery hints? Open [`references/api-reference.md`](references/api-reference.md).
- Need to choose transformations for an augmentation goal? Open [`references/operation-selection.md`](references/operation-selection.md).
- Need to debug validation errors, Pillow resize filters, or custom operations? Open [`references/troubleshooting.md`](references/troubleshooting.md).
- Need a safe runtime smoke check? Run [`scripts/augmentor_operation_probe.py`](scripts/augmentor_operation_probe.py) in an environment where `Augmentor`, Pillow, and NumPy are installed.

## Operating rules

1. Add operations to an `Augmentor.Pipeline` before sampling or processing; operation order is the execution order.
2. Treat every operation probability as `0 < probability <= 1`. A probability of `1` is the normal choice for deterministic resizing, greyscale conversion, and other required transforms.
3. Keep geometry parameters conservative: arbitrary rotation and shear are designed for at most 25 degrees; larger values are rejected or produce unusable images.
4. `Operation.perform_operation(images)` receives a list of PIL Images and must return a list of PIL Images. This list contract matters for future mask/ground-truth workflows.
5. Prefer `Pipeline` convenience methods for built-in operations. Mention lower-level classes such as `HSVShifting` and `Mixup` only as manual `Operation` classes; they are not top-level `Pipeline` convenience workflows.

## Boundaries

- Route disk scanning, output directories, class subfolders, `sample()`, `process()`, seeding, and multithreading to `pipeline-augmentation`.
- Route ground-truth masks, identical transforms across images and masks, and in-memory grouped arrays to `masks-and-arrays`.
- Route Keras-style generators, PyTorch transforms, and DataFrame-backed inputs to `generators-and-frameworks`.
