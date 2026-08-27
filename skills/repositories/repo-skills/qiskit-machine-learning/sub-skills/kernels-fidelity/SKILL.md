---
name: kernels-fidelity
description: "Evaluate, configure, and train Qiskit Machine Learning
  fidelity-based quantum kernels, including statevector kernels,
  ComputeUncompute fidelity, duplicate and PSD policies, trainable parameters,
  and kernel losses."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Fidelity kernels

Use this route when the task is to turn a parameterized quantum feature map into
fidelity kernel matrices, select a fidelity primitive or statevector simulation,
control duplicate/PSD/shot behavior, bind trainable feature-map parameters, or
optimize a kernel with `QuantumKernelTrainer`.

## Fast route

1. Define an explicit `QuantumCircuit` feature map whose data-parameter count
   equals the input feature dimension. The current implementation's base class
   rejects a missing feature map, even where a constructor annotation permits
   `None`; do not rely on an implicit default.
2. Choose `FidelityStatevectorKernel` for exact/classically simulated overlaps,
   optionally with bounded caching and shot-noise emulation. Choose
   `FidelityQuantumKernel` for a sampler-backed `BaseStateFidelity`; its default
   fidelity is `ComputeUncompute` over the QML reference sampler.
3. Evaluate `K_train = kernel.evaluate(X)` and, for held-out data,
   `K_test = kernel.evaluate(X_test, X_train)`. Check shapes before passing a
   precomputed matrix to a consumer. Route QSVC/QSVR fitting to the algorithms
   sub-skill; this skill owns the kernel object and matrices, not model fitting.
4. For noisy symmetric training matrices, keep `enforce_psd=True` unless the
   downstream algorithm or experiment explicitly requires the raw noisy matrix.
   Select `evaluate_duplicates` deliberately for primitive kernels.
5. For a trainable feature map, construct a trainable fidelity kernel, bind every
   training parameter with `assign_training_parameters`, then use
   `QuantumKernelTrainer` with a derivative-free optimizer and an appropriate
   kernel loss. Route optimizer-specific choices to the optimizers sub-skill.
6. If a sampler requires backend-specific transpilation, construct
   `ComputeUncompute(sampler=..., pass_manager=...)` using a pass manager for the
   same backend and validate the resulting circuit layout before execution.

Read [workflows](references/workflows.md) for concrete procedures,
[api-reference](references/api-reference.md) for signatures and matrix semantics,
[fidelity-and-runtime](references/fidelity-and-runtime.md) for primitive/runtime
adaptation, and [troubleshooting](references/troubleshooting.md) before changing
an otherwise working configuration.

## Applicability and boundaries

- This route covers `BaseKernel`, `FidelityQuantumKernel`,
  `FidelityStatevectorKernel`, their trainable variants, `BaseStateFidelity`,
  `ComputeUncompute`, `StateFidelityResult`, `QuantumKernelTrainer`, and kernel
  losses (`SVCLoss`, `SVRLoss`, `MSRLoss`, `MARLoss`, `HuberLoss`).
- It covers feature-map dimensions, symmetric/asymmetric evaluation, duplicate
  shortcuts, PSD projection, statevector caching, shot noise, parameter binding,
  trainer outputs, and fidelity runtime/pass-manager adaptation.
- It does not choose classical optimizers, fit QSVC/QSVR models, or explain raw
  QNN gradient workflows. Use the linked algorithms, optimizers, or qnn-gradients
  routes when those are the primary task.
- Keep matrices in memory or in user-named artifacts; do not assume a source
  checkout exists at runtime. Install public dependencies using the package's
  published installation instructions, for example `pip install qiskit-machine-learning`
  plus compatible Qiskit and scikit-learn packages.

## Minimal acceptance checks

Run the bundled smoke check with `python path/to/kernel_smoke.py`. It constructs
a two-feature statevector kernel, asserts a square symmetric training matrix,
checks the asymmetric `(1, 2)` shape, and verifies unit self-fidelity. For a
sampler-backed or trainable deployment, additionally check the relevant workflow
and runtime failure cases in the references. Do not claim hardware verification
from a statevector-only smoke test.
