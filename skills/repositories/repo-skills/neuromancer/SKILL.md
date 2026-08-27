---
name: neuromancer
description: "Guide NeuroMANCER 1.5.6 differentiable scientific machine-learning
  workflows for constrained optimization, dynamics modeling, data and training,
  predictive control, simulation, and structured operators."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# NeuroMANCER

Use this repo skill when a task names NeuroMANCER or asks for PyTorch-based
scientific machine learning involving symbolic constraints, differentiable
programming, neural ODE/PDE/SDE models, system identification, predictive
control, PSL simulation, or structured linear operators.

## First route by the user's deliverable

- **Formulate a constrained or symbolic problem** — read
  [`sub-skills/symbolic-problems/SKILL.md`](sub-skills/symbolic-problems/SKILL.md).
  This owns `Variable`, objectives, constraints, aggregate losses, `Node`, and
  `Problem` graphs.
- **Prepare data or train/evaluate a model** — read
  [`sub-skills/data-training/SKILL.md`](sub-skills/data-training/SKILL.md).
  This owns dictionary/static/sequence/graph schemas, normalization, splits,
  collators, `Trainer`, Lightning, callbacks, and logging.
- **Construct a neural dynamical model** — read
  [`sub-skills/dynamics-modeling/SKILL.md`](sub-skills/dynamics-modeling/SKILL.md).
  This owns blocks, activations, ODE/SDE/PINN/DAE components, integrators,
  interpolation, and system-identification models.
- **Roll out a plant or build a control loop** — read
  [`sub-skills/control-simulation/SKILL.md`](sub-skills/control-simulation/SKILL.md).
  This owns `System`, preview and moving-horizon wiring, PSL simulators,
  signals, emulators, and bounded DPC/control recipes.
- **Choose a structured map or differentiable operator solver** — read
  [`sub-skills/structured-operators/SKILL.md`](sub-skills/structured-operators/SKILL.md).
  This owns pure-Python SLiM maps, structured RNNs, projection/iterative
  solvers, and dimension restrictions.

For a request that spans routes, establish the data/time/key contract first,
then combine the smallest set of sibling routes. Keep symbolic objective and
constraint construction separate from model, data, and rollout construction.

## Installation and first check

The public distribution is `neuromancer==1.5.6` and requires Python `>=3.9`.
Install it in an isolated environment:

```bash
python -m pip install neuromancer
python -c "import neuromancer; print(neuromancer.__version__)"
```

The package declares PyTorch, TorchDiffEq, TorchSDE, Lightning, CVXPY,
CVXPYLayers, CasADi, NumPy/SciPy, and plotting dependencies. Install only the
optional packages needed by the selected route. PSL imports `requests` in this
release even when package metadata does not list it; if PSL import fails with
that missing module, install `requests` in the isolated target environment.

Run the bundled environment diagnostic before a larger workflow:

```bash
python scripts/check_environment.py --help
python scripts/check_environment.py --run
```

The diagnostic reports package imports, dependency availability, and whether a
CUDA device can be probed. A CUDA-enabled PyTorch import is not proof that a
NeuroMANCER GPU workflow runs; use CPU as the portable baseline and read the
route-specific backend warnings.

## Shared operating rules

1. Use module-qualified imports such as `neuromancer.constraint`,
   `neuromancer.dataset`, `neuromancer.dynamics.ode`,
   `neuromancer.modules.blocks`, `neuromancer.psl`, and `neuromancer.slim`.
2. Make tensor rank and dictionary keys explicit. Ordinary node calls use
   `(batch, features)`; rollouts normally use `(batch, time, features)`;
   sequence datasets emit past/future keys and a collated `name`.
3. Give nodes, objectives, and constraints unique names. Keep output keys
   intentional when a graph uses recurrent overwrites.
4. Start with a tiny CPU fixture and assert output shapes, finite values, loss
   keys, and gradient behavior before adding data, long training, plotting,
   external files, or GPU execution.
5. Treat network downloads, credentials, large datasets, long experiments,
   multi-GPU execution, and the native Butterfly factor extension as explicit
   optional work, not as hidden smoke-test steps.

Read [`references/installation-and-overview.md`](references/installation-and-overview.md)
for the package mental model and route selection, and
[`references/troubleshooting.md`](references/troubleshooting.md) for
cross-cutting installation, key/shape, backend, data, and optional-dependency
failures. Check [`references/repo-provenance.md`](references/repo-provenance.md)
before deciding whether this skill matches a changed NeuroMANCER checkout.
