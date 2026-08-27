# Core Modeling

## Purpose

Read this when you need to build or inspect a Pyomo model from first
principles: components, expressions, values, blocks, and simple solve-backed
smoke checks.

## What it covers

- `ConcreteModel` and the basic component containers.
- `Set`, `RangeSet`, `Param`, `Var`, `Constraint`, `Objective`, `Block`,
  `Expression`, and `Suffix`.
- `value()`, `pprint()`, `display()`, and component traversal helpers.
- Tiny self-contained models that do not depend on data files.

## Verified API facts

The following objects are importable from `pyomo.environ` in this checkout:

- `ConcreteModel(*args, **kwds)`
- `Set(*args, **kwds)`
- `Param(*args, **kwds)`
- `Var(*args, **kwds)`
- `Constraint(*args, **kwds)`
- `Objective(*args, **kwds)`
- `Block(*args, **kwds)`
- `Expression(*args, **kwds)`
- `Suffix(*args, **kwargs)`
- `RangeSet(*args, **kwds)`
- `value(obj, exception=True)`
- `SolverFactory(name=None, **kwds)`

## Minimal model pattern

```python
import pyomo.environ as pyo

m = pyo.ConcreteModel()
m.x = pyo.Var(within=pyo.Binary)
m.c = pyo.Constraint(expr=m.x <= 1)
m.obj = pyo.Objective(expr=m.x, sense=pyo.maximize)
```

Useful inspection calls:

```python
m.pprint()
print(pyo.value(m.x))
for comp in m.component_objects(pyo.Var, active=True):
    print(comp.name)
```

## Typical workflow

1. Import `pyomo.environ`.
2. Build the model container.
3. Declare sets, parameters, variables, objectives, and constraints.
4. Assign initial values or bounds when needed.
5. Inspect the model with `pprint()` or `display()`.
6. Use `SolverFactory(...)` only after the model is structurally valid.

## Common gotchas

- `None` values are allowed during construction but not in every expression.
- Domain or bounds mismatches usually surface as warnings or `TypeError`
  messages when values are assigned.
- `Suffix` objects are only useful when a solver or transformation reads them.
- Recursive expressions can trigger `RecursionError`-style warnings in deep
  expression trees.
- `ConcreteModel` constructs immediately; `AbstractModel` belongs in
  `data-and-io`.

## Related references

- Read `data-and-io.md` when the model comes from `.dat`, `.tab`, Excel, YAML,
  or JSON inputs.
- Read `solve-and-cli.md` when you want to verify a tiny model with a solver.
- Read `troubleshooting.md` when component construction, values, or domain
  validation behave unexpectedly.
