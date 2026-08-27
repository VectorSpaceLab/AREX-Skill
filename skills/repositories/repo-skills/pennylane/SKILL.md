---
name: pennylane
description: "Use PennyLane for quantum circuits, differentiable QNodes,
  devices, transforms, domain modules, data/io, and source-repo maintenance."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# PennyLane repo skill

Use this skill when a task involves the PennyLane Python package, a PennyLane source checkout, or quantum-computing workflows built with PennyLane. It covers the verified CPU core of PennyLane 0.46.0-dev73 and explicitly marks optional framework, plugin, and accelerator paths.

## First checks

1. Import the package as `qp` in examples and tests unless the surrounding project requires another alias:
   ```python
   import pennylane as qp
   print(qp.version())
   ```
2. For an installed-package smoke test, run [`scripts/pennylane_smoke.py`](scripts/pennylane_smoke.py). It imports PennyLane, creates a `default.qubit` QNode, executes it, and checks an Autograd gradient.
3. For API signatures, run [`scripts/inspect_pennylane_api.py`](scripts/inspect_pennylane_api.py) with names such as `QNode`, `qnode`, `device`, `grad`, `compile`, `qchem.Molecule`, or `estimator.estimate`.
4. Read [`references/install-and-inspection.md`](references/install-and-inspection.md) before changing dependencies, optional extras, interface packages, or backend claims.
5. Read [`references/troubleshooting.md`](references/troubleshooting.md) when imports, devices, measurements, gradients, optional backends, datasets, or source-checkout tests fail.

## Route by task

- **Build or debug circuits, QNodes, devices, measurements, shots, drawing, or `pl-device-test`:** read [`sub-skills/circuits-devices/SKILL.md`](sub-skills/circuits-devices/SKILL.md).
- **Choose operations/templates, compose observables, inspect matrices, decompose/compile/transform circuits, or create a custom operator:** read [`sub-skills/operators-transforms/SKILL.md`](sub-skills/operators-transforms/SKILL.md).
- **Work with gradients, differentiable interfaces, training loops, optimizers, `TorchLayer`, JAX/Torch/Autograd behavior, or Catalyst/qjit caveats:** read [`sub-skills/gradients-interfaces/SKILL.md`](sub-skills/gradients-interfaces/SKILL.md).
- **Use application modules such as qchem, fermi/bose/spin mappings, QAOA, kernels, qcut, shadows, pulse, `specs`, resources, or the estimator:** read [`sub-skills/applications-qchem-resource/SKILL.md`](sub-skills/applications-qchem-resource/SKILL.md).
- **Import/export circuits, load datasets, use debugging snapshots, configure logging, or reason about pytrees/concurrency support:** read [`sub-skills/io-data-logging/SKILL.md`](sub-skills/io-data-logging/SKILL.md).
- **Modify a PennyLane source checkout, add operators/devices/plugins, choose focused tests, run lint/format/tach, update changelog, or respect repo AI/GitHub policy:** read [`sub-skills/repo-development/SKILL.md`](sub-skills/repo-development/SKILL.md) and [`references/development-conventions.md`](references/development-conventions.md).

## What is verified here

- Required scope: CPU package import, `default.qubit`, QNode execution, Autograd gradients, installed package metadata, and the `pl-device-test` console script help.
- Optional/unverified unless the user or environment proves them: CUDA/ROCm/MPS devices, `lightning.gpu`, external plugins, Catalyst runtime, Torch/JAX/TensorFlow packages, qchem external solver extras, remote datasets, and network downloads.
- TensorFlow support is documented as no longer maintained in this repository version; prefer JAX or Torch for new ML workflows unless maintaining existing TensorFlow code.

## Core mental model

PennyLane quantum programs are Python functions containing quantum operations and ending in measurement processes. A `QNode` binds such a function to a device and exposes it as a callable object. Interfaces and differentiation methods determine how trainable arrays flow through the QNode and how gradients are computed. Operations, templates, transforms, and domain modules are composable layers around that core.

## Public package map

Read [`references/package-map.md`](references/package-map.md) for the high-level module map. Use source-level facts only after checking live API signatures or the relevant reference in this skill; avoid relying on memory because PennyLane changes signatures and module boundaries frequently.

## Development safety

If the task changes a PennyLane checkout, keep edits minimal, run only relevant tests, then run configured lint/format tools on changed files. Do not open or comment on GitHub issues/PRs, do not commit, and do not silence lint/coverage warnings without explicit human approval. Details are in [`references/development-conventions.md`](references/development-conventions.md).

## Provenance and routing metadata

- Source snapshot and evidence paths: [`references/repo-provenance.md`](references/repo-provenance.md)
- Router import metadata: [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json)
