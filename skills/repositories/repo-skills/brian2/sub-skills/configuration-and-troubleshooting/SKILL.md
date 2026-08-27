---
name: configuration-and-troubleshooting
description: "Install and validate Brian2 2.9.0 environments, configure
  preferences, caches, and logging, and triage import, compiler,
  optional-dependency, and common runtime failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Configuration and troubleshooting

Use this route when Brian2 cannot be imported, a package/compiler prerequisite
is unclear, a preference unexpectedly changes the code-generation or cache
configuration, or a log is needed to classify a failure. This route covers
Brian2 2.9.0 with Python >=3.12 and the `brian2` import root.

## Route quickly

1. **Establish identity and baseline.** From the directory containing this
   sub-skill's bundled `scripts/` directory (or by passing that script's
   relative path), run `python scripts/check_brian2_env.py`. Confirm Python
   >=3.12, distribution `Brian2==2.9.0`, every declared base dependency and
   version constraint, and that an incomplete source checkout is not shadowing
   the intended installation. The checker is read-only and does not reveal
   executable or cache paths.
2. **Repair installation before configuration.** Follow
   [installation](references/installation.md) in an isolated environment. Do
   not mix a checkout import with a separately installed distribution. If the
   checker reports a required import or version failure, fix that first and
   retest in a fresh interpreter.
3. **Inspect effective preferences and cache state.** Read
   [preferences and cache](references/preferences-and-cache.md) before changing
   `prefs.codegen.target`, compiler settings, or Cython cache settings. The
   current-directory preference file overrides the user preference file.
4. **Capture evidence and classify the first failure.** Use
   [troubleshooting](references/troubleshooting.md) to preserve the exception,
   Python/package versions, target, compiler names, relevant preferences, and
   Brian debug-log information before retrying or clearing a cache.
5. **Choose the smallest validation.** A NumPy-target tiny model checks core
   Python execution. A Cython or C++ build is a separate native gate and can
   write cache/project files; run it only as an explicitly approved local
   check.

## Scope and routing boundaries

This route owns installation, importability, required package presence,
compiler/Cython prerequisite diagnosis, preference-file precedence and
validation, cache ownership/permissions, logging diagnostics, and generic
failure triage. It does **not** own detailed code-generation target selection,
generated-code APIs, standalone project design, model equations, scheduling,
or workflow-specific failures. After recording environment facts here, route
those details to [code-generation](../code-generation/SKILL.md),
[modeling](../modeling/SKILL.md),
[simulation-and-recording](../simulation-and-recording/SKILL.md),
[recording](../recording/SKILL.md),
[spatial-models](../spatial-models/SKILL.md), or
[units-and-equations](../units-and-equations/SKILL.md), respectively.

Optional packages are capability boundaries, not automatic requirements:

- SciPy is required for selected NumPy spatial/multicompartment operations;
  Matplotlib is for plotting; Pandas is for state import/export formats;
  IPython/Jupyter is for interactive notebooks; and `brian2tools` is a separate
  visualization/analysis package.
- GSL support means a native GSL installation with headers/libraries as well as
  Brian's integration; a Python import or library-name probe alone cannot prove
  it. Route GSL state-updater/code-generation use to code-generation.
- `pytest>=8` is the test extra needed by `brian2.test()`. A full test run is
  not the default response to a user-model failure.

## Safety and acceptance

- Do not install packages, use network commands, compile extensions, clear
  caches, delete standalone output, or edit preference files during a
  read-only diagnosis.
- Treat `import brian2` as necessary but insufficient: target, compiler,
  optional capability, cache access, and requested workflow need separate
  evidence.
- Treat an unknown version, failed required import, old Python, unavailable
  compiler for a compiled target, unreadable cache, invalid preference file,
  and unresolved optional native dependency as explicit unresolved limits.
- `brian2.test()` resets preferences while it runs and restores them afterward;
  use a narrow target/marker selection when diagnosing rather than launching
  the complete suite by default.

## Bundled operating files

- [installation.md](references/installation.md): package identity, baseline
  dependencies, pip/Conda installation, compiler prerequisites, and optional
  capability boundaries.
- [preferences-and-cache.md](references/preferences-and-cache.md): preference
  access, file syntax and precedence, effective target/cache inspection,
  cache-clearing safeguards, and NFS/process guidance.
- [troubleshooting.md](references/troubleshooting.md): install/import,
  compiler/Cython, optional dependency, configuration/data, API, logging, and
  workflow triage with routing boundaries.
- [check_brian2_env.py](scripts/check_brian2_env.py): non-mutating compact or
  JSON environment report. Use `--help` first; `--strict` gates required
  Python/package/import/version checks, and `--require-compiler` adds a
  compiler-name gate.

The script reports compiler names and capability states, not local paths,
Python prefixes, or cache locations.
