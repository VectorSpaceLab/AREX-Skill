# CLI reference

PySR exposes a small command wrapper through `python -m pysr`. Use it for help text and selected native test subsets, not for ordinary model fitting.

Important: `python -m pysr` imports the PySR package before displaying help, so it can trigger JuliaCall/SymbolicRegression first-import setup. If you need a no-import check, use `scripts/pysr_environment_probe.py --skip-import` instead.

## Commands

```bash
python -m pysr --help
python -m pysr install --help
python -m pysr test --help
```

`install` is deprecated; Julia dependencies are installed or resolved at import time. Do not call `python -m pysr install` as a modern setup step.

## Test command shape

```bash
python -m pysr test TESTS [-k PATTERN ...]
```

`TESTS` is a comma-separated list chosen from:

| Test name | What it covers | Runtime expectation |
| --- | --- | --- |
| `cli` | Click command help behavior | Lightest, but still imports package through `python -m pysr`. |
| `startup` | startup warnings, registry fallback, notebook/import behavior | Can initialize Julia; selected `-k` patterns are preferred. |
| `main` | core PySRRegressor behavior and small fits | Can compile and run actual searches. |
| `jax` | JAX export helpers | Requires JAX CPU dependency. |
| `torch` | PyTorch export helpers | Requires PyTorch dependency. |
| `autodiff` | optional autodiff backend behavior | Optional backend packages; can be expensive. |
| `dev` | development/backend behavior | For maintainers or source checkouts. |
| `slurm` | Slurm cluster-manager integration | Requires a Slurm service/allocation; do not run on ordinary hosts. |

`-k` uses shell-style pattern matching against test ids. Quote patterns so the shell does not expand `*`.

## Useful commands

Help-only CLI smoke:

```bash
python -m pysr --help
python -m pysr test --help
```

Run CLI unit tests:

```bash
python -m pysr test cli
```

Startup-warning behavior without running the whole startup suite:

```bash
python -m pysr test startup -k '*bad_startup_options*'
```

A tiny core fitting candidate, when first import/compile time is acceptable:

```bash
python -m pysr test main -k '*linear_relation*'
```

Optional export-helper subsets when the dependencies are installed:

```bash
python -m pysr test jax -k '*sympy2jax*'
python -m pysr test torch -k '*sympy2torch*'
```

Do not run `python -m pysr test slurm` unless a Slurm test service or allocation is intentionally available.

## Interpreting results

- Exit code `0`: selected tests passed.
- Exit code `1`: at least one selected test failed.
- Import-time Julia setup messages before test output are expected in fresh environments.
- Missing optional dependency failures for JAX, Torch, autodiff, TensorBoard, or Slurm do not block base PySR runtime readiness unless the user specifically needs that feature.

## Safe probe integration

Use the bundled probe first:

```bash
python scripts/pysr_environment_probe.py --skip-import --json
```

Then use the optional CLI check only after deciding that package import is acceptable:

```bash
python scripts/pysr_environment_probe.py --json --check-cli
```

The probe never runs a model fit. The CLI test subsets may run actual tests depending on which subset is selected.
