# WASM Package Maintenance

## When to read

Read this when modifying the browser package, not when merely consuming the
published TypeScript SDK.

## Build and test commands

```bash
just build          # WASM release build plus TypeScript distribution
just build-wasm     # WASM only
just build-dist     # package distribution from existing artifacts
just test           # SDK integration tests after dist exists
just typecheck
just serve          # local examples server
just size
just clean
```

The package is deliberately separate from the Rust core workspace to avoid
DataFusion dependency conflicts.

## Runtime/build constraints

- Browser execution is single-threaded.
- The package avoids zstd because its native dependency cannot compile into the
  targeted WASM configuration.
- The binary is large; distribute through a compatible host/bundler and test
  a loading state.
- The TypeScript wrapper uses camelCase JavaScript APIs around wasm-bindgen
  output. Preserve overload and byte-view behavior for CSV/Parquet inputs.
- Browser examples and Node tests need generated dist artifacts. Do not treat a
  source-only TypeScript check as a browser runtime pass.

## Scope discipline

Do not add an unrelated release/deployment workflow when the task is a core API
change. Do not use a local browser build to claim package support for external
data sources or Wren memory; the browser runtime is a separate surface.
