# Installation and operating overview

## When to read

Read this reference when the task is new to NeuroMANCER, combines multiple
sub-skills, or needs a dependency/backend decision before code is written.

## Package mental model

NeuroMANCER is a PyTorch differentiable-programming library organized around
three user-facing patterns:

- **Learning to optimize (L2O):** a neural or algorithmic `Node` produces
  decision variables; symbolic `Variable` expressions define objectives and
  constraints; a loss aggregator evaluates the resulting `Problem`.
- **Learning to model (L2M):** blocks, ODE/SDE/PINN/DAE components, integrators,
  and physics modules map data or states to predictions. `System` can roll a
  model forward over a horizon.
- **Learning to control (L2C):** a policy and plant are composed in a closed
  loop, often with `System`, PSL emulators, preview references, and symbolic
  constraints/objectives.

A robust multi-route plan normally follows this order:

1. Define raw data and the `(batch, features)` or `(batch, time, features)`
   convention using `data-training`.
2. Construct a model or plant using `dynamics-modeling` or
   `control-simulation`.
3. Wire nodes and key names; use `symbolic-problems` for objectives,
   constraints, and aggregate losses.
4. Run a tiny CPU forward/rollout and inspect keys/shapes.
5. Add a bounded Trainer or Lightning run only after the preceding contracts
   are stable.

## Dependency choices

The package metadata declares these runtime families: `torch`, `torchdiffeq`,
`torchsde`, `lightning`, `cvxpy`, `cvxpylayers`, `casadi`, NumPy/SciPy,
matplotlib, `pyts`, `networkx`, `pydot`, and related support packages. They are
not all needed for every request:

| Need | Prefer | Extra caution |
|---|---|---|
| Symbolic graph and CPU model smoke | base package plus PyTorch | Graph image output may additionally need the Graphviz executable |
| ODE/integrator construction | base package plus TorchDiffEq | The integrator module imports both TorchDiffEq and TorchSDE in this release |
| SDE or LatentSDE | TorchSDE and compatible PyTorch | Avoid claiming SDE training from a shape-only smoke |
| Lightning training | Lightning and its compatible PyTorch stack | Start with CPU, short epochs, and `save_weights=False` |
| Differentiable convex projection | CVXPY and CVXPYLayers | Solver availability and problem differentiability are separate checks |
| PSL/file emulation | NumPy/SciPy/Torch plus `requests` | Local files are safer than download-backed systems |
| Structured pure-Python maps | PyTorch and `neuromancer.slim` | Native Butterfly factor multiplication is outside the baseline |

Install from the public package rather than relying on an editable source
checkout. If a task uses a versioned local checkout, keep that checkout as
construction evidence and still validate the installed distribution and
import module separately.

## Backend policy

CPU is the required baseline for this operating graph. CUDA, multi-GPU
Lightning, external data, and native C++/CUDA operators are optional and must
be verified with their actual runtime before being described as supported. On
a shared machine, `torch.cuda.is_available()` can be true while a tiny
allocation fails because of memory or device contention; report that as an
unverified GPU path and continue with CPU if the task allows it.
