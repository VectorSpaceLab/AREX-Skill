---
name: units-and-equations
description: "Use Brian2 physical units, equation declarations and flags,
  parser-supported expressions, stochastic terms, namespaces, state updaters,
  and unit-aware custom functions safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Brian2 units and equations

Use this route when a task is about dimensional correctness, equation-string
syntax, stochastic symbols, numerical integration method selection, namespaces,
or unit-aware custom functions. Load only the reference needed for the current
question:

- [Equation syntax](references/equation-syntax.md) for declarations, flags,
  special symbols, parser limits, namespaces, and integrated-form conversion.
- [Numerical methods](references/numerical-methods.md) for deterministic and
  stochastic state-updater choices and restrictions.
- [API reference](references/api-reference.md) for units, `Equations`,
  `check_units`, `Function`, and `implementation` boundaries.
- [Troubleshooting](references/troubleshooting.md) for classified failures.

For a quick, read-only probe of unit declarations and unit-aware functions, run
`python scripts/unit_equation_smoke.py --help`, then `--all` in an environment
where the `brian2` package imports successfully. The smoke script intentionally
checks both passing and failing dimensional cases; it is not a replacement for
model or device tests.

## Operating procedure

1. Write down the physical dimension of every state variable, parameter,
   derivative, and external value. In a differential declaration, the unit
   after `:` is the variable's unit; the right-hand side must be that unit per
   second.
2. Use Brian's base unit names in declarations (`volt`, `second`, `amp`,
   `metre`, etc.), including compound dimensions. Use scaled units (`mV`,
   `ms`, `nA`) for assigned values and external namespaces. Use `mmolar`/`mM`
   for molar concentration in equations.
3. Parse a minimal `Equations` object first. Then instantiate the owning group
   or call its unit check so unknown names, namespaces, flags, dependency cycles,
   and dimensional errors are actually validated. `Equations` construction
   alone does not perform all context-dependent checks.
4. Resolve external names explicitly with a group `namespace` or the
   `Network.run(..., namespace=...)` argument when reproducibility matters.
   Avoid relying on implicit locals/globals when a name could be shadowed.
5. Select `method` only after classifying the ODE (linear, conditionally linear,
   deterministic nonlinear, additive noise, or multiplicative noise). If a
   method rejects the equations, change the method or the equation form; do
   not hide the rejection by disabling unit checks.
6. For a custom function, declare argument and result units with
   `@check_units` (or a complete `Function`). Add target implementations only
   when the selected code-generation target needs them, and keep the
   `implementation` decorator outside the unit decorator. Test the Python/NumPy
   path separately from C++/Cython compiler integration.

The bundled smoke covers a valid and invalid dimensional operation, equation
flags and parser rejection, explicit namespaces, suffixed-noise rules, a
unit-checked `Function`, a NumPy `implementation`, exact versus Euler decay,
and finite additive noise. Treat `--all` as a bounded contract check, not as a
substitute for owner-specific synapse, linked-variable, or device tests.

Route high-level neuron/synapse construction to the modeling or
synapses-and-inputs routes. Route device, compiler, standalone build, and
backend installation problems to code-generation. Keep this route focused on
the contracts above.
