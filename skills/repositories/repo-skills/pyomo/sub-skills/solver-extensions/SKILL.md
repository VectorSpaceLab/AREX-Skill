---
name: solver-extensions
description: "Guides Pyomo users through optional solver, analysis, GUI, and
  compiled-extension workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Solver Extensions

Use this sub-skill when the task depends on an optional Pyomo extension rather
than the base package alone.

## What this sub-skill covers

- APPSI solver interfaces and solver configuration.
- FBBT and expression-bound tightening.
- PyNumero and interior-point tooling.
- Community detection, simplification, and the model viewer.

## What to route elsewhere

- Base model syntax and inspection go to `modeling-basics`.
- Data loading and `AbstractModel` workflows go to `data-and-io`.
- `pyomo` CLI help, solver selection, and tiny solve smokes go to
  `solve-and-cli`.
- GDP, DAE, network, MPEC, and units go to `structured-modeling`.

## Read these references

- `../../references/solver-extensions.md` for verified extension facts,
  optional dependencies, and backend notes.
- `../../references/troubleshooting.md` for install, import, solver, GUI, and
  compiled-extension failure modes.
- `../../references/core-modeling.md` when the extension still needs a base
  model to operate on.

## Use this helper

- `../../scripts/check_import.py` for a fast environment sanity check before you
  debug an optional extension.
- `../../scripts/check_optional_backends.py` when you need a quick import report
  for optional scientific, GUI, or Pyomo extension dependencies.

## Typical workflow

1. Confirm which optional extension family the user needs.
2. Check whether the required extras or solver backends are installed.
3. Run the smallest safe extension import or API smoke.
4. Only then move on to the specific solver, GUI, or analysis action.

## Common request patterns

- "Why does APPSI not see my solver?"
- "How do I tighten bounds before solving?"
- "How do I use PyNumero or an interior-point helper?"
- "Why does the model viewer say Qt is unavailable?"
- "How do I detect communities or simplify an expression?"

## Common failure modes

- Missing `numpy`, `scipy`, or another numerical dependency.
- Missing solver backend executable or Python wrapper.
- Missing `networkx`, `python-louvain`, `pint`, or `qtconsole`.
- Missing Qt binding for the model viewer.
- CMake or compiler prerequisites missing for extension-build paths.

## Practical guidance

- Distinguish importability from backend readiness.
- Use the smallest possible optional dependency set for the selected task.
- Do not claim GUI or advanced solver readiness from a plain base-package
  import.
- Keep compiled-extension workflows separate from pure-Python analysis.

## Examples of what belongs here

- APPSI solver selection and configuration.
- FBBT bounds tightening on a nonlinear model.
- PyNumero build or import troubleshooting.
- Community detection or simplification on a Pyomo model.
- Viewer startup problems or Qt dependency gaps.

## Examples of what does not belong here

- Basic model syntax.
- Data-file loading.
- The general `pyomo solve` command line.

## Related routes

- Move to `structured-modeling` when the optional solver is only part of a GDP,
  DAE, network, or MPEC workflow.
- Move to `solve-and-cli` when the optional backend error is actually a solver
  invocation problem.
