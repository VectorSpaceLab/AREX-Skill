---
name: deepxde
description: "Use DeepXDE for scientific machine learning, PINNs,
  DeepONet/operator learning, backend selection, training, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 2.1
---

# DeepXDE repo skill

Use this skill when a task involves **DeepXDE**, physics-informed neural networks (PINNs), scientific machine learning for ODE/PDE/IDE/FPDE problems, DeepONet/operator learning, or DeepXDE backend/training troubleshooting.

This skill is self-contained for future use: it distills the package source, docs, examples, and verified PyTorch CPU inspection into bundled routes, references, and smoke scripts. It does not require the original repository checkout.

## Verified baseline

- Package/distribution: `DeepXDE`, import name `deepxde`.
- Python: package metadata requires Python `>=3.9`.
- Base package dependencies: `matplotlib`, `numpy`, `scikit-learn`, `scikit-optimize>=0.10.2`, and `scipy`.
- Tensor backend requirement: install at least one DeepXDE backend package before use.
- Runtime verified by this construction: **PyTorch backend on CPU** for import, simple PDE assembly, `FNN`, `Model.compile`, one-step `Model.train`, and `Model.predict`.
- Optional/alternative paths that require target-environment verification: TensorFlow 1.x compatibility, TensorFlow 2.x + TensorFlow Probability, JAX + Flax + Optax, PaddlePaddle, GPU, Horovod/MPI, and long training examples.

## Minimal installation and import check

For a CPU-safe DeepXDE setup, install DeepXDE plus PyTorch in an isolated Python environment, then select the backend **before** importing DeepXDE:

```bash
python -m pip install deepxde torch
DDE_BACKEND=pytorch python - <<'PY'
import deepxde as dde
print(dde.__version__)
print(dde.backend.backend_name)
PY
```

Use package-manager-appropriate PyTorch wheels for CPU, CUDA, ROCm, or MPS in the target environment. Do not treat a CPU import as proof of GPU or Horovod correctness.

## Route by task

| If the user asks to... | Read |
| --- | --- |
| install DeepXDE, choose `DDE_BACKEND`, debug missing TensorFlow/JAX/Paddle/PyTorch packages, check GPU visibility, set dtype/autodiff/random seed/XLA/parallel scaling | [sub-skills/backend-and-configuration/SKILL.md](sub-skills/backend-and-configuration/SKILL.md) |
| build a forward or inverse PINN for an ODE/PDE/IDE/FPDE, define geometry, BC/IC/point-set constraints, residuals, gradients, hard constraints, or adaptive points | [sub-skills/pinn-problem-setup/SKILL.md](sub-skills/pinn-problem-setup/SKILL.md) |
| compile/train a `dde.Model`, choose optimizers, callbacks, metrics, save/restore, predict residuals/outputs, fit functions/tabular data, or use multifidelity data | [sub-skills/training-workflows/SKILL.md](sub-skills/training-workflows/SKILL.md) |
| build DeepONet, POD-DeepONet, MIONet, PI-DeepONet, Cartesian-product operator data, function spaces, ZCS, or troubleshoot branch/trunk/data-shape errors | [sub-skills/operator-learning/SKILL.md](sub-skills/operator-learning/SKILL.md) |

## Cross-cutting references and scripts

- [references/backend-and-installation.md](references/backend-and-installation.md) summarizes backend packages, selection order, and the verified/unverified backend boundary.
- [references/troubleshooting.md](references/troubleshooting.md) triages common install, backend, PDE, training, plotting, data-shape, and optional hardware failures and routes to the owning sub-skill.
- [references/repo-provenance.md](references/repo-provenance.md) records the source commit, package version, dirty-state baseline, and evidence paths used to generate this skill.
- [scripts/smoke_deepxde.py](scripts/smoke_deepxde.py) is a safe PyTorch CPU diagnostic that imports DeepXDE and can optionally run a tiny PDE training smoke.

Run the root smoke before adapting a task when the environment is uncertain:

```bash
python scripts/smoke_deepxde.py --backend pytorch --train-steps 1
python scripts/smoke_deepxde.py --backend pytorch --json
```

## Operating rules for future agents

1. Set `DDE_BACKEND` before importing any DeepXDE module. Backend selection happens during import.
2. Use backend-native tensor operations inside residuals and operators; use `dde.grad.jacobian` and `dde.grad.hessian` for derivatives.
3. Keep problem definition separate from training: assemble `geometry`/`icbc`/`data` in the PINN or operator sub-skill, then use `training-workflows` for `Model.compile`, `train`, callbacks, and checkpoints.
4. Do not assume every example supports every backend. Many examples document supported backends; this skill distills the common PyTorch CPU-safe path and marks other paths optional.
5. Do not run long examples, notebooks, benchmarks, GPU/Horovod jobs, or data-download workflows as smoke tests unless the user explicitly requests that cost and the required backend/data are available.
6. If the package commit, public APIs, backend dependencies, or example layout differ from [repo provenance](references/repo-provenance.md), refresh this skill before relying on stale guidance.
