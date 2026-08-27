---
name: backends
description: "Select hls4ml backends, generate backend configs, write or inspect
  projects, and parse build reports safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Backends

Use this sub-skill when the question is about backend selection, project layout,
build/report invocation, report parsing, backend defaults, or vendor tool
prerequisites.

## Route here
- backend choice and default config values
- `create_config(...)` backend options and board/part/clock settings
- `ModelGraph.write()`, `compile()`, and `build()`
- legacy CLI build/report compatibility and deprecation notes
- report parsing for existing synthesis outputs

## Route away
- model conversion and frontend parsing → `frontends`
- precision tuning, bit-exactness, FIFO sizing, or BramFactor strategy → `analysis`
- custom backend registration, plugins, or template authoring → `extensions`

## Safe workflow
1. Inspect the installed backend registry with `scripts/inspect_backends.py`.
2. Confirm the legacy CLI surface with `scripts/check_cli_help.py`.
3. Generate or update a project config with `hls4ml.utils.create_config(...)`.
4. Use `write()` to materialize files, `compile()` for local library builds, and
   `build()` only when vendor tools are available and synthesis is intended.
5. Parse existing reports with the `hls4ml.report` parser APIs instead of
   rerunning synthesis.

## Key constraints
- Treat `write()` and `compile()` as safe by default.
- Treat vendor synthesis as expensive and toolchain-bound.
- Prefer the Python API over the deprecated CLI.
- Do not fold precision/resource tuning advice into this sub-skill unless the
  question is specifically about build or report artifacts.

## References
- `references/backend-matrix.md`
- `references/build-and-reports.md`
- `references/generated-project-layout.md`
- `references/cli-reference.md`
- `references/troubleshooting.md`
