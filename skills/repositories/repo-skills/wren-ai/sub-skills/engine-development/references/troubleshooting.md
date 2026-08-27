# Engine Development Troubleshooting

## Python import uses the published wheel

A normal package install may resolve `wren-core-py` from its published wheel.
After changing local Rust code, use the module's local build/overlay recipe and
verify the loaded version/path from the intended environment before testing.

## Rust stack or compile failure

Run focused Cargo commands with the documented Rust stack size when tests use
deep semantic planning. Check the owning crate's manifest and path dependencies
before changing versions.

## `load_mdl` or concurrent context errors

Serialize calls on one `SessionContext`; use separate contexts for independent
work. Register local files and load MDL in the documented two-phase order.

## WASM build failure

Check Rust/wasm-pack/LLVM/Node prerequisites, the no-zstd constraint, and the
single-threaded target configuration. Do not fix a browser build by adding a
native-only dependency that cannot compile for WASM.

## Validation guard proposal

Trace the actual input boundary. If the core parser has already enforced the
manifest schema, a second guard in a downstream caller is likely dead code. If
a user-supplied JSON/YAML object is dereferenced before core validation, that is
the place to validate and report the failure.
