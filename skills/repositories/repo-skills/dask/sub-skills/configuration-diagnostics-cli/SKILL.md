---
name: configuration-diagnostics-cli
description: "Use this Dask sub-skill for configuration files and environment
  variables, the `dask` command line interface, local
  diagnostics/profiling/progress, callbacks/cache, scheduler/deployment
  documentation routing, install extras troubleshooting, and development/test
  command lookup."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Configuration, Diagnostics, and CLI

Use this sub-skill when the task involves Dask configuration, local runtime diagnostics, the `dask` CLI, install extras, or contributor validation commands.

## Route By Task

- **Configuration values:** Start with `references/configuration.md` for `dask.config.get`, `set`, YAML search paths, environment variables, schema defaults, and import-time config caveats.
- **CLI workflows:** Use `references/cli-reference.md` for `dask --help`, `dask config ...`, `dask docs`, `dask info versions`, entry-point registration, and safe smoke checks.
- **Progress and profiling:** Use `references/diagnostics-and-performance.md` for `ProgressBar`, `Profiler`, `ResourceProfiler`, `CacheProfiler`, `Callback`, and `Cache`.
- **Development commands:** Use `references/development-and-testing.md` for pixi, pytest, lint, doctest, and targeted validation commands.
- **Failures and caveats:** Use `references/troubleshooting.md` for `DASK_CONFIG`, YAML parse errors, missing config keys, optional diagnostics dependencies, distributed-vs-core scheduler confusion, browser-opening CLI behavior, and warnings-as-errors.

## Boundaries

- Route array-specific settings such as chunking, rechunking, slicing, array backends, and array query planning to the array workflow sub-skill after checking the generic config mechanics here.
- Route dataframe-specific settings such as shuffle, parquet, string conversion, dataframe backends, and dataframe query planning to the dataframe workflow sub-skill after checking the generic config mechanics here.
- Route task graph, delayed, compute, persist, annotations, and scheduler API design to the core graphs/schedulers sub-skill; use this sub-skill only for selecting or troubleshooting scheduler/config surfaces.
- Do not require the original repository checkout at runtime; use bundled references and `scripts/dask_cli_smoke.py` for CLI smoke validation.

## Safe Smoke Script

Run the bundled smoke script against the active Python environment when you need a quick, side-effect-light CLI check:

```bash
python scripts/dask_cli_smoke.py --help
python scripts/dask_cli_smoke.py
```

The default script run checks `dask --help`, `dask config get temporary-directory`, `dask config list`, and `dask info versions` without writing configuration files or opening a browser.
