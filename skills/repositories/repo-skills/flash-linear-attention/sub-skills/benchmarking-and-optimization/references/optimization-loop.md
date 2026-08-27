# Optimization Loop Reference

This reference defines the operating contract for Flash Linear Attention kernel optimization. It is designed to prevent accidental reward-hacking: a faster number only matters when the same frozen correctness contract still holds.

## Inviolable rule

The op's pytest gate and naive/reference implementation are frozen for the duration of a performance loop. Do not:

- edit the gate test file or reference implementation;
- loosen `assert_close` tolerances, skip parametrized cases, or narrow shapes to make a candidate pass;
- change numeric precision flags on only the candidate side;
- special-case the kernel for benchmark values;
- cache module-level tensors so the benchmark reuses warm or identical data;
- replace the operator with a whole-call vendor-library wrapper just to win latency;
- report speedup after a red or skipped gate.

A subset gate selected with `--gate-k` is a fast signal only. Final promotion requires the full gate.

## Task contract before code

Before editing a kernel, write a short local scratch contract for the operator under optimization. The contract should include:

| Item | Required content |
| ---- | ---------------- |
| Op and entry point | Registry name and public callable, for example `chunk_gla` in `fla.ops.gla`. |
| Target shapes | Shape ids or custom shape JSON, with the affected modes (`fwd`, `fwdbwd`). |
| Baseline | Git ref and hardware/backend used for comparison. |
| Allowed implementation language | Triton, Gluon, TileLang, CUDA/CuTe, Triton-Ascend, or other agreed backend. |
| Validation command | Usually `python -m benchmarks.ops.verify --op <op>`. |
| Benchmark command | Usually `python -m benchmarks.ops.verify --op <op> --base <ref>`. |
| Frozen scope | Test file, naive/reference implementation, public signature, tolerances, and expected dtype/precision. |
| Promotion criteria | Full gate green, repeatable same-hardware win, profiler explanation, minimal diff. |

Keep scratch logs and profiles outside the runtime skill tree and outside committed source unless explicitly requested.

## Three-phase loop

### Phase 1 — correct baseline

Run the full gated benchmark and record the current performance. For a new kernel, correctness comes first; no benchmark result is meaningful until the full gate is green.

```bash
python -m benchmarks.ops.verify --op <op> --base main
```

Record the machine line, baseline median latencies, affected modes, and shape ids.

### Phase 2 — profile-guided optimization

Use benchmark results to pick the hot shape/mode, then profile the active backend. Make one hypothesis at a time: memory traffic, register pressure, launch overhead, poor tiling, uncoalesced loads, backend dispatch miss, or a true algorithmic bound.

Useful handoff points:

- NVIDIA/Triton/Gluon/TileLang/CUDA: collect Nsight Compute evidence when available. Minimum MR-quality evidence is same-workload before/after plus a short explanation of memory throughput, SOL/occupancy, and hot instructions for representative changed kernels.
- Ascend/Triton-Ascend/NPU: collect with the generic NPU profiler/analyzer workflow, classify Cube/Vector/MTE/UB/scalar bottlenecks, then benchmark with synchronization after each change.
- Gluon porting: consider only when profiling shows that explicit layouts, async movement, TMA/WGMMA/TMEM, persistent scheduling, or register-budget control can address the bottleneck. A literal port is a parity scaffold, not a final win.

### Phase 3 — shape specialization

Specialize only if different shape regimes have different measured bottlenecks. Every dispatch bucket must have evidence:

| Bucket condition | Entry point | Baseline ms | Candidate ms | Speedup | Why this path |
| ---------------- | ----------- | ----------- | ------------ | ------- | ------------- |
| `T <= 1024` | Example small-shape path | measured | measured | measured | launch-bound, smaller tile wins |
| `T > 1024` | Example default path | measured | measured | measured | memory-bound, default tile wins |

Do not add a specialized branch when a single kernel serves the full shape set best.

## Iteration protocol

One iteration is exactly:

1. Make one kernel or benchmark-registry change.
2. Run the gated driver. If the gate fails, stop; do not benchmark that iteration.
3. Append one log row and preserve the candidate/revert decision before trying another direction.

Template:

```markdown
# Optimization log — <op>

Env: Machine: <gpu/backend> | PyTorch <version> | Triton <version> | <branch>[sha]
Baseline: <main median ms by target shape/mode>
Target: <speedup and modes>

| Iter | Direction | Gate | Bench | vs best | Status |
| ---- | --------- | ---- | ----- | ------- | ------ |
| 0 | baseline | pass | 1.934 ms | — | base |
| 1 | one tiling change | pass | 1.701 ms | +12% | keep |
| 2 | larger block | fail | — | — | drop |
```

Status values should be `base`, `keep`, `revert`, `drop`, or `floor`. A failed iteration still gets a row; the bench column stays empty because the gate failed.

## Logging and scratch artifacts

Use a local ignored workspace such as `profile/<op>-opt/`:

```text
profile/<op>-opt/
  docs/draft.md
  OPT_LOG.md
  dispatch.md
  TRAPS.md
  trace/
  reports/
```

Record enough evidence for a later session to reconstruct the loop:

- command line and environment variables;
- gate result and whether it was full or subset;
- benchmark rows or JSON path;
- baseline ref and candidate SHA;
- profiler summary and diagnosis;
- whether the change was kept, reverted, dropped, or declared floor.

Do not put local `.ncu-rep`, `.nsys-rep`, NPU profiler dumps, raw traces, or scratch logs into the runtime skill tree.

## Promotion bar

A candidate may be promoted only when all of these are true:

1. Full frozen gate passes, including forward and backward where supported.
2. Before/after benchmark uses the same hardware, workload, shape set, dtype, mode, backend dispatch, and precision flags.
3. Improvement is repeatable above expected noise, not just one lucky run.
4. Profiler or roofline evidence explains why latency improved.
5. No relevant shape/backend/mode regressed beyond the accepted threshold, or the trade-off is explicitly documented and accepted.
6. Diff is minimal and does not touch unrelated paths.

For final claims, include median/mean or quantile context when available, baseline ref, candidate SHA, GPU/backend identity, exact commands, and environment variables that influence dispatch or autotune.

## No-go bar

A no-go is also a conclusion and needs evidence. Do not declare no-go after one failed candidate. A defensible no-go requires:

- a recorded baseline number;
- at least one reasoned candidate attempt;
- a gate status for each attempt;
- benchmark evidence for every passing attempt;
- a named active bound or blocker, such as bandwidth saturation, launch overhead, timer resolution, compiler limitation, missing backend package, or unsupported shape.

After three consecutive non-`keep` iterations, stop and reassess before continuing: re-profile, review the log, and identify untried axes or the likely floor.

## Silent-bug and measurement traps

- NaN-poisoned tests catch partial writes. If a casual script passes but the frozen gate fails with NaNs, trust the gate.
- `assert_close` tolerances are part of the contract. Widening them turns a numeric regression into a hidden bug.
- TF32 or lower-precision accumulators can create one-sided wins. Keep numeric flags symmetric across baseline and candidate.
- Cast program IDs and grid-derived indices before large pointer/stride multiplications; overflow appears only on long shapes.
- Implausibly large speedups often mean a path was skipped, a shape was filtered, or a cheaper numeric path was selected.
- Autotune cache can be stale after config-space edits. Rewarm or clear cache when results are suspicious.
- Unlocked GPU clocks and thermal drift move absolute speedups. Re-measure the final candidate directly against the baseline in one session.

## Backend profiling handoff

### NVIDIA/Triton/Gluon/TileLang/CUDA

Minimum handoff:

```text
op=<op>
mode=<fwd|fwdbwd>
shape=<shape id or JSON>
baseline=<ref and median ms>
candidate=<sha and median ms>
backend=<triton|gluon|tilelang|cuda>
observed bottleneck=<memory|compute|register|launch|dispatch|unknown>
artifacts=<local profile directory, not committed>
```

Representative commands:

```bash
python -m benchmarks.ops.verify --op <op> --base main
python -m benchmarks.ops.verify --op <op> --profile
ncu --set full -k "regex:<kernel_regex>" -c 1 -o profile/<run>/reports/full_<tag> \
  python -m benchmarks.ops.run --op <op> --modes fwd
ncu --set source -k "regex:<kernel_regex>" -c 1 -o profile/<run>/reports/source_<tag> \
  python -m benchmarks.ops.run --op <op> --modes fwd
```

Use datacenter NVIDIA GPUs for final claims when possible; consumer or pre-sm80 numbers are reference-only.

### Ascend/Triton-Ascend/NPU

Minimum handoff:

```text
op=<op>
mode=<fwd|fwdbwd>
shape=<shape id or JSON>
baseline=<median ms>
candidate=<median ms>
metrics=<PipeUtilization and, if needed, MemoryUB>
bottleneck=<Cube|Vector|MTE|UB|scalar|fallback|grid>
```

Ascend performance work must keep the target backend semantically correct before optimization. Do not hide unsupported behavior behind a Torch fallback. NPU kernels do not use CUDA-style `num_warps` or `num_stages` launch tuning; tune tile, grid, layout, fusion/split, UB budget, and dispatch.
