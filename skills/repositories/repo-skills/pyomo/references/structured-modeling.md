# Structured Modeling

## Purpose

Read this when a Pyomo task uses structured modeling objects rather than only
basic sets, variables, and constraints.

## What it covers

- Generalized Disjunctive Programming (`pyomo.gdp`).
- Dynamic models and discretization (`pyomo.dae`).
- Network models with ports and arcs (`pyomo.network`).
- Complementarity / MPEC models (`pyomo.mpec`).
- Units of measure in expressions and constraints.

## GDP

Key objects:

- `Disjunct`
- `Disjunction`
- `TransformationFactory('gdp.bigm')`
- `TransformationFactory('gdp.hull')`

Useful pattern:

```python
from pyomo.gdp import Disjunct, Disjunction
import pyomo.environ as pyo

m = pyo.ConcreteModel()
m.x = pyo.Var(bounds=(0, None))
m.y = pyo.Var(bounds=(0, None))
# define disjuncts and a disjunction, then transform
```

Notes:

- `gdp.chull` is deprecated in this checkout.
- Classic GDP examples often use binary switching, logic, or mutually exclusive
  process choices.

## DAE

Key objects:

- `ContinuousSet`
- `DerivativeVar`
- `Integral`
- `Simulator`

Common transforms:

- `TransformationFactory('dae.finite_difference')`
- `TransformationFactory('dae.collocation')`

Useful options seen in the code/tests/docs:

- `wrt=...`
- `nfe=...`
- `ncp=...`
- `scheme=...`

Practical notes:

- DAE models are not ready to solve until every `ContinuousSet` has been
  discretized.
- The simulator is available, but its practical use depends on optional
  numerical packages.

## Network modeling

Key objects:

- `Port`
- `Arc`
- `SequentialDecomposition`

Common transform:

- `TransformationFactory('network.expand_arcs')`

Important patterns:

- `Port.Equality` is the default port-member rule.
- `Port.Extensive` is used for flow-like quantities that split or mix.
- `SequentialDecomposition.run()` is for ordered evaluation of a network
  model after the arcs have been expanded.

## MPEC and complementarity

Key objects:

- `Complementarity`
- `complements`
- `ComplementarityList`

Use this when modeling orthogonality or equilibrium-style relationships in a
Pyomo model.

## Units

Pyomo units are based on `pint`.

Useful import pattern:

```python
from pyomo.environ import units as u
```

Key helpers:

- `assert_units_consistent`
- `assert_units_equivalent`
- `check_units_equivalent`
- `u.get_units(expr)`

Important restrictions:

- Absolute temperature units are preferred inside algebraic expressions.
- Offset-unit arithmetic has limitations and can fail in non-obvious ways.

## When to use this sub-skill

- A request mentions GDP, DAE, network, MPEC, complementarity, arcs, ports,
  discretization, or units.
- A model needs structural transformations before solving.
- A user wants a routing guide for specialized model-building patterns.

## Common gotchas

- Forgetting the transformation step is the most common failure.
- DAE discretization errors often come from missing `wrt`, `nfe`, or `ncp`
  arguments.
- Network models usually need `network.expand_arcs` before the solver can see
  the constraints.
- GDP examples often fail if the disjunctive logic is encoded but never
  transformed.
- Unit errors usually mean the physical dimensions are inconsistent even if the
  algebraic form looks fine.

## Related references

- Read `core-modeling.md` for the base component types used in these models.
- Read `solver-extensions.md` for APPSI, PyNumero, and analysis helpers that
  sometimes sit beside these workflows.
- Read `troubleshooting.md` when a transformation or unit check fails.
