---
name: code-generation
description: "Choose Brian2 runtime and C++ standalone code-generation targets,
  manage builds and reusable runs, and recover compiler, cache,
  result-directory, and optional GSL failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Brian2 code generation

Use this route when the task names `prefs.codegen.target`, Cython, NumPy code
objects, `set_device`, `cpp_standalone`, a compiler/build directory, repeated
standalone runs, `run_args`, or GSL integration. This sub-skill is written for
Brian2 2.9.0 and Python >=3.12.

## Route quickly

1. **Ordinary runtime simulation:** keep the default `runtime` device. Start
   with `prefs.codegen.target = "auto"`; it prefers Cython when its test
   compilation succeeds and otherwise falls back to NumPy with a warning.
   Choose `"numpy"` explicitly when compiler setup is unavailable or a
   reproducible no-compiler fallback is more important than speed.
2. **Compiled runtime:** choose `prefs.codegen.target = "cython"` only after
   Cython and a working C++ compiler are available. The first use compiles and
   caches extensions; later compatible code can reuse the cache.
3. **Standalone project:** call `set_device("cpp_standalone")` before model
   construction. Use the default `build_on_run=True` for one final `run`; use
   `build_on_run=False` for multiple `run` statements or a build/reuse loop.
   `device.build` controls generation, compilation, and optional first
   execution: `compile=False` writes a project but cannot run it, while
   `run_args` is forwarded to that first execution. Read
   [standalone-workflows.md](references/standalone-workflows.md) before
   changing a runtime script.
4. **Reuse:** build once with `device.build(run=False)` and call
   `device.run(run_args=..., results_directory=...)` for subsequent full
   executions. `run_args` accepts `VariableView`/`TimedArray` mappings or
   command-line assignment lists; result directories are relative to the
   project and must be unique when outputs are retained or concurrent. The
   model and externally defined constants are not generally mutable after
   compilation; use equation variables with suitable flags and `run_args`
   instead.
5. **Optional GSL:** treat `method="gsl"` and the `gsl_*` methods as an
   optional native-library path. Runtime GSL needs Cython plus GSL; standalone
   also needs GSL headers and libraries. If unavailable, use a supported
   non-GSL state updater and record the numerical/feature limitation.

## Operating guardrails

- `get_device()` returns the active device and `device` is a proxy to it. A
  `set_device` call is global to the current process; restore the runtime
  device when a larger application continues after a standalone section.
- A CPU/package import check proves only Python/package readiness. It does **not**
  prove that Cython can compile or that a C++ standalone project can build and
  run. Treat compiler preparation and the final native build as separate gates.
- Standalone writes generated sources, a binary, and result files to a project
  directory. Use a fresh temporary or uniquely named directory for checks and
  never reuse a result directory concurrently. `device.delete(data=True, ...)`
  targets the active result directory; use a disposable project or explicitly
  remove older result directories as well.
- State arrays and synaptic indices whose values depend on executed code cannot
  be inspected during standalone setup. Access them after a successful run;
  use string expressions for dependent initialization where possible.
- GSL state-updater code is experimental, requires native GSL linkage, is not a
  NumPy runtime path, and rejects stochastic equations. A non-GSL updater is a
  functional but potentially non-equivalent fallback; do not claim GSL support
  without a tiny target-specific compile/run.
- Do not use this route to design neuron/synapse equations, schedule ordinary
  networks, or explain general preferences. Hand those requests to the
  corresponding modeling, simulation, or configuration route. Long benchmarks,
  multiprocessing studies, and large training runs are reference-only here.

## Bundled operating references

- [api-reference.md](references/api-reference.md): target, device, build, run,
  cache, and cleanup API facts.
- [runtime-targets.md](references/runtime-targets.md): runtime target selection,
  Cython prerequisites, NumPy fallback, and cache reuse.
- [standalone-workflows.md](references/standalone-workflows.md): one-run,
  multi-run, `run_args`, result directories, and standalone limitations.
- [optional-backends.md](references/optional-backends.md): GSL prerequisites,
  supported paths, and fallback boundaries.
- [troubleshooting.md](references/troubleshooting.md): install/import,
  optional-dependency, data/configuration, API, compiler/cache, and workflow
  failure recovery.

For a safe native smoke after the integrated skill has been prepared, run the
bundled script with `--help` first and then, only with an intentionally prepared
compiler, run the default tiny check:

```text
python scripts/standalone_smoke.py --help
python scripts/standalone_smoke.py
```

The script uses a temporary output directory, a tiny deterministic model, and
cleanup. It is not a substitute for a real project build of a user's model.
