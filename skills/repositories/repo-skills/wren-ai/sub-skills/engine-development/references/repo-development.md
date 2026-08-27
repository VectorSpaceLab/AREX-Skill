# Repository Development

## When to read

Read this when changing WrenAI source or selecting a focused test/build command.

## Ownership and setup

In a WrenAI checkout, identify the owning package from its package/Cargo
metadata before selecting a command:

- The Python CLI/SDK package uses Python 3.11+, `uv`, Hatchling, Typer, and pytest.
- The PyO3 binding uses Maturin plus Rust/Python tests.
- The semantic core and shared manifest crate use Cargo.
- The browser package uses Cargo, wasm-pack, Node, and TypeScript.
- Framework SDK packages use Hatchling and pytest.

For ordinary Python-side work, use the module's locked install path. Use the
local-core overlay only when changing the Rust engine/binding and needing the
Python CLI to load the local wheel.

## Contribution bar

- Reproduce the problem before claiming a fix.
- Label changes as fixes only when a user-visible failure is demonstrated.
- Tests must call the changed behavior and assertions must be capable of
  failing.
- Keep one mechanical change in one reviewable change rather than duplicating
  PRs across files.
- Respect documented decisions and keep the branch current.

## Validation boundary

The semantic manifest is validated at the core deserialization boundary. Do not
add repeated type guards after a successful core parse. Validate external/user
inputs before dereferencing them, especially imported MDL JSON, project YAML,
and API responses.

## Safe test selection

Prefer focused unit tests for CLI/context/engine behavior. Service-backed
connector tests, publishing scripts, benchmarks, browser deploys, and full Rust
or WASM builds are separate gates; record their prerequisites and do not present
an unrun optional path as verified.
