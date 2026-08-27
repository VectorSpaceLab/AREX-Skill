---
name: scikit-opt
description: "Use scikit-opt to solve GA, DE, PSO, SA, AFSA, routing, and
  objective-speedup workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# scikit-opt

Use this repo skill for the `scikit-opt` / `sko` Python package when the task is about heuristic optimization, route/permutation search, objective-function shaping, or run-mode acceleration.

## Install and import

- Install the published package with `pip install scikit-opt`.
- Check the import with `python -c "import sko; print(sko.__version__)"`.
- If you are working from a local checkout during maintenance, see `references/troubleshooting.md` for the editable-install caveat; the runtime skill itself stays package-centric.

## Read this first when unsure

- Read `references/package-overview.md` for the family map: GA, DE, PSO, SA, AFSA, TSP/routing, built-in demo functions, and run-mode helpers.
- Read `references/troubleshooting.md` for install/import issues, optional dependencies, the `PSO_TSP` caveat, and common runtime failures.
- Read `references/repo-provenance.md` when you need to know whether this skill still matches the current repository snapshot.
- Run `scripts/check_scikit_opt_env.py` when you want a quick environment sanity check without opening the source repository.

## Route to the right sub-skill

- `genetic-algorithms` — GA, EGA, RCGA, integer or mixed-precision search, continuation runs, and custom operators via `register()`.
- `continuous-optimizers` — DE, PSO, SA schedules, and AFSA for continuous or constrained real-valued problems.
- `routing-and-combinatorial` — GA_TSP, SA_TSP, ACA_TSP, IA_TSP, fixed-endpoint route recipes, and permutation validation.
- `objective-functions-and-speedups` — objective shape contracts, built-in benchmark functions, `set_run_mode`, cached/vectorized/threaded modes, and optional GPU/plotting dependencies.

## Minimal routing rules

1. If the task is about GA-style discrete or mixed-precision optimization, go to `genetic-algorithms`.
2. If the task is about a continuous objective, pick `continuous-optimizers`.
3. If the task is about permutations, routes, or TSP, pick `routing-and-combinatorial`.
4. If the task is about objective shape, demo functions, run modes, caching, or optional acceleration, pick `objective-functions-and-speedups`.

## Package facts to remember

- The import package is `sko`.
- The package version captured in this skill snapshot is `0.6.6`.
- Core package dependencies are NumPy and SciPy.
- Plotting, Pandas, Joblib, and PyTorch are optional surfaces that belong to specific workflows rather than the core package import.
- `PSO_TSP` is a version-specific caveat in this snapshot and should not be treated as a reliable default route solver.

## When to use the shared helpers

- Use `scripts/check_scikit_opt_env.py` before a handoff when you want an import/signature sanity check.
- Read `references/package-overview.md` before choosing a sub-skill if the user only names a problem shape, not a class.
- Read `references/troubleshooting.md` before investigating a failure so you can separate install/import problems from algorithm-specific issues.
