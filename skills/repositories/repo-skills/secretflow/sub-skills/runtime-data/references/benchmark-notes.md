# Benchmark notes

The repository includes a benchmark harness under `examples/benchmark/` that is
useful as evidence for multi-party execution shape, but it is not bundled as a
runtime helper.

## Why it is not bundled

- It expects multiple machines and SSH trust between them.
- It assumes a manually prepared test directory and log directory.
- It is a performance harness, not a normal user workflow.
- It is too environment-specific to become a safe default smoke helper.

## What it still tells us

- SecretFlow can be exercised in multi-party simulation mode.
- The benchmark flow uses the same core runtime concepts as the local quick
  start: parties, devices, object transfer, and `sf.init`.
- Long-running benchmarks should stay out of the main runtime skill and remain
  a reference only.
