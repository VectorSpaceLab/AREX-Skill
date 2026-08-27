---
name: specialized-parsers
description: "Guides Logparser workflows that need import shims, compilers,
  GPU/torch stacks, or API credentials."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Specialized parsers

Use this sub-skill for parser workflows that do not fit the ordinary
`LogParser` path cleanly.

## Include here

- SHISO import shims and parse runs.
- SLCT compile-and-run workflows that need GCC flag adjustments.
- LogCluster's Perl-backed parser path.
- MoLFI's `deap`-based evolutionary workflow.
- NuLog's torch / CUDA runtime and its output quirks.
- DivLog's API-backed parsing and embedding-related dependencies.

## Exclude from here

- The common Drain/AEL/IPLoM-style parsing path; use `../parsing/SKILL.md`.
- Benchmark evaluation; use `../benchmarking/SKILL.md`.

## Read these references

- `references/special-parsers.md` for parser-by-parser notes.
- `references/backend-and-dependency-matrix.md` for the dependency map.
- `references/troubleshooting.md` for import, compile, CUDA, and API issues.

## Run these scripts

- `scripts/run_shiso_with_import_shim.py` — SHISO with the installed-package
  path shim.
- `scripts/run_slct_safe.py` — compile SLCT with relaxed GCC flags and run a
  tiny parse.
- `scripts/run_nulog_smoke.py` — run a tiny NuLog smoke with the pinned NumPy
  and pandas versions.

## When to route here

Choose this sub-skill when the request says things like:

- "use SHISO"
- "compile SLCT"
- "run LogCluster"
- "use NuLog"
- "run DivLog"
- "I need the API key / torch / CUDA / perl / GCC path"

## Working notes

- Check `scripts/check_install.py` first when the environment has not been
  inspected yet.
- If the user asks for a live DivLog run, confirm the credentials and network
  first.
- If the user asks for SHISO or SLCT, prefer the bundled wrappers rather than
  trying to coerce the source demos directly.
