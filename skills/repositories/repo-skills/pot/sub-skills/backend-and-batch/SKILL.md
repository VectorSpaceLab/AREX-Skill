---
name: backend-and-batch
description: "Use POT with NumPy, PyTorch, JAX, TensorFlow, CuPy arrays, backend
  detection and conversion, optional backend controls, and batched OT/GW
  solvers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# POT Backend and Batch Operations

Use this sub-skill when the task involves POT array backends or many same-shaped OT problems: NumPy baseline arrays, optional PyTorch/JAX/TensorFlow/CuPy arrays, backend discovery and conversion, environment variables that disable optional backend imports, mixed-backend errors, TensorFlow NumPy behavior, `ot.batch` vectorization, or gradient-memory choices.

Read [references/backend-reference.md](references/backend-reference.md) when deciding how to call `get_backend`, `get_backend_list`, `to_numpy`, backend classes, optional backend extras, disable environment variables, TensorFlow setup, or dtype/device-preserving conversion.

Read [references/batch-solvers.md](references/batch-solvers.md) when building batched `dist_batch`, `solve_batch`, `solve_sample_batch`, or `solve_gromov_batch` workflows, checking verified signatures/defaults, validating plan shapes/marginals, or comparing a batched solve with a looped solve.

Read [references/troubleshooting.md](references/troubleshooting.md) when POT raises mixed-backend `ValueError`s, optional imports are missing, TensorFlow NumPy behavior is inactive, GPU or CuPy variants are confusing, PyTorch gradient memory is too high, or batch dimensions/weights/methods fail.

Run [scripts/backend_batch_smoke.py](scripts/backend_batch_smoke.py) after installing POT to print detected backend implementations and exercise deterministic NumPy batch-solver fixtures without plotting, downloads, native repo tests, source checkouts, or optional backend assumptions.

Route mathematical OT solver selection to the owning solver sub-skill: `core-solvers` for ordinary exact/Sinkhorn OT, `gromov` for GW/FGW modeling, `unbalanced-partial` for relaxed mass, `barycenters` for barycenter construction, and `sliced-gaussian-large-scale` for approximation families. This sub-skill owns backend mechanics and batch vectorization, not choosing the mathematical model.
