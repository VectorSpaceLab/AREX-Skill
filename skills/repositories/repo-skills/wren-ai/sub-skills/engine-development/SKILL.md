---
name: engine-development
description: "Guide Wren core engine, wren_core Python bindings, Rust and PyO3
  development, WASM maintenance, module test selection, validation boundaries,
  and WrenAI contribution policy."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Wren Engine Development

Use this sub-skill for repository maintenance, `wren_core` APIs, Rust semantic
engine changes, PyO3 binding work, WebAssembly builds, module-specific tests, or
contribution-policy questions.

## First Decision: User Workflow or Repository Change?

- For an installed-package query/project task, route to `cli-projects` or
  `query-engine` rather than compiling the repository.
- For a checkout change, identify the owning module before choosing commands:
  - the Python CLI/SDK package;
  - the Rust semantic core;
  - the shared manifest-data-model crate;
  - the Python/PyO3 binding; or
  - the browser/WASM package.
  Inspect the checkout's package or Cargo metadata to confirm the module before
  editing; this skill does not require a fixed source-tree layout.

## Core Python Binding

`wren_core.SessionContext` supports a no-MDL construction path and a
manifest-backed path. Its public methods include `transform_sql`, `query`,
`dry_run`, `register_csv`, `register_parquet`, `load_mdl`, `list_tables`,
`get_available_functions`, and `pushdown_limit`.

For physical-file workflows, register files and then load the MDL that refers
to them. Do not overlap `load_mdl` with other calls on the same context.

## Module Commands

Use module-local instructions for actual development. Typical commands are:

```bash
# Rust core
cargo check --all-targets
RUST_MIN_STACK=8388608 cargo test --lib --tests --bins

# Python binding
just install
just develop
just test-py

# Browser package
just build
just test
just typecheck
```

Only run builds/tests that match the edited module and environment. Rust/WASM
builds are not package-user smoke checks.

## Contribution Rules

Reproduce the behavior before claiming a fix. Classify a change honestly,
exercise code with real assertions, respect documented decisions, avoid duplicate
work, and keep the branch current. Place validation at an actual input boundary;
do not add defensive type checks after the core has already validated a manifest.

## References and Helper

- Read `references/python-binding.md` for `SessionContext` lifecycle and APIs.
- Read `references/rust-core.md` for Rust architecture and limitations.
- Read `references/wasm-maintenance.md` for browser-package build constraints.
- Read `references/repo-development.md` for module ownership, test selection,
  and contribution policy.
- Read `references/troubleshooting.md` for ABI, build, concurrency, and test
  issues.
- Run `scripts/inspect_wren_core.py` for safe binding capability inspection.

## Route Elsewhere

- CLI project and MDL user workflows: `../cli-projects/SKILL.md`.
- Query API and connector behavior: `../query-engine/SKILL.md`.
- Browser runtime consumption or GenBI/MCP operation: `../genbi-mcp-wasm/SKILL.md`.
