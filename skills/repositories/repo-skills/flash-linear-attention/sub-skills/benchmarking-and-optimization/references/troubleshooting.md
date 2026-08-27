# Benchmarking and Optimization Troubleshooting

Use this when a gated benchmark, comparison run, profiler handoff, or saved JSON summary does not behave as expected.

## Gate fails

Symptom:

```text
GATE FAILED — correctness regressed. Not benchmarking.
```

Action:

1. Stop performance claims for this candidate.
2. Confirm whether the run used the full gate or a subset `--gate-k` signal.
3. Reproduce the failure with the frozen test path and no benchmark flags.
4. Treat NaNs as likely partial writes or uninitialized regions until proven otherwise.
5. Do not loosen tolerances, skip cases, change references, or change dtype/precision flags to get a green gate.

If the user asks for a benchmark number after a red gate, report that the number would be unverified and not promotable.

## Gate test path is missing

The gated driver derives a pytest file from the registry entry unless `test_file` is set. Some registry names differ from test names.

Action:

```bash
python -m benchmarks.ops.verify --op <op> --test-file tests/ops/test_<actual>.py
```

If this is a recurring target, update the registry entry's `test_file` field rather than relying on ad hoc commands.

## Op is not registered

Symptom:

```text
KeyError: Op '<name>' not registered
```

Action:

1. List targets: `python -m benchmarks.ops.verify --list`.
2. If the callable exists but is not registered, add an `OpConfig` with input tensor specs, shape transforms, category, and any explicit `test_file`.
3. Verify the registry only: `python -m benchmarks.ops.run --list`.
4. Then run the gated driver. Do not create a one-off timing script and treat it as equivalent to the registry sweep.

## Warmup or input generation fails

Likely causes:

- shape violates `dim_constraints`;
- required backend package is missing;
- optional external package such as flash attention is unavailable;
- OOM from a long shape or residual-source `L` axis;
- post-init callback cannot build a structured input;
- backend dispatch points at an unsupported path.

Action:

1. Check whether all shapes failed or only a subset.
2. For all-shape failures, validate package/backend installation and import path.
3. For subset failures, inspect constraints and custom shape fields such as `L`, `HQ`, `S`, or `block_size`.
4. Reduce scope only for diagnosis. Final promotion needs the affected full shape set, or an explicit accepted exclusion.

## `run.py` shows speedup but `verify.py` fails

`run.py` does not prove correctness. Treat the speedup as invalid for promotion. Fix correctness first, then rerun the gated driver.

## `--gate-k` passes but full gate fails

A subset gate is only a fast signal. Promote nothing until the full gate passes. Use the failing parametrization to identify the shape, dtype, or mode that the candidate broke.

## Noisy or inconsistent timings

Common causes:

- unlocked GPU clocks or thermal drift;
- cold autotune or stale autotune cache;
- different baseline/candidate environment variables;
- mixed backend dispatch state;
- insufficient benchmark repetition window;
- other processes on the accelerator.

Action:

```bash
export FLA_BENCH_WARMUP_MS=100
export FLA_BENCH_REP_MS=300
export FLA_BENCH_COOLDOWN_SEC=30
python -m benchmarks.ops.verify --op <op> --base main
```

For suspicious config-space changes, clear or isolate Triton's cache and rerun. For final claims, re-measure candidate versus baseline in one session; do not add speedups from separate historical runs.

## Baseline compare fails

`benchmarks.ops.run --base` uses a temporary worktree and reinstalls the package at the baseline ref. FLA's checkout-owned cross-commit comparison helper can check out and reinstall both refs, then restore the original ref; use it only for explicit repository-maintenance tasks in an active checkout.

Action:

- Ensure the baseline ref exists locally.
- Ensure the current worktree can create a temporary worktree.
- Confirm the selected op exists at both refs; missing targets produce unpaired rows.
- If the helper had to switch refs, verify the final checkout was restored before continuing development.

## Backend dispatch confusion

Benchmark what the task intends to benchmark. Record these variables when they matter:

| Variable | Debug use |
| -------- | --------- |
| `FLA_DISABLE_BACKEND_DISPATCH=1` | Force default paths to isolate dispatch effects. |
| `FLA_TILELANG=0/1` | Disable or enable TileLang-backed dispatch when installed. |
| `FLA_FLASH_KDA=0/1` | Disable or enable FlashKDA dispatch for supported KDA forward inference paths. |
| `FLA_INTRACARD_CP=0/1` | Control intra-card context-parallel dispatch for supported paths. |
| `FLA_CACHE_MODE` / `FLA_CONFIG_DIR` / `FLA_GPU_NAME` | Stabilize or override config-cache selection. |
| `FLA_CACHE_RESULTS` / `TRITON_CACHE_DIR` | Diagnose autotune cache reuse. |

Do not change dispatch or precision flags on only one side of a before/after claim.

## Profiling trace exists but does not explain the speedup

A profiler trace is evidence only if it connects the code change to the measurement. If the top kernel did not change, the target backend was not hit, or the bottleneck classification is still unknown, continue diagnosis before promotion.

For NVIDIA work, collect enough data to discuss memory throughput, occupancy/SOL, and hot instructions for a representative changed kernel. For Ascend work, classify the dominant pipe or UB/MTE issue and confirm the changed metric moved after optimization.

## JSON summarizer cannot match rows

The skill-owned summarizer matches comparison rows using every non-metric key such as `op`, `mode`, `B`, `T`, `H`, `D`, `L`, `HQ`, `S`, and `block_size`.

Common mismatch causes:

- base and head ran different custom shapes;
- op label includes backend suffix on one side only;
- one side skipped backward due to `skip_backward`;
- one side failed warmup or OOM and omitted rows;
- comparison JSON is from a different script format.

Action:

```bash
python scripts/summarize_benchmark_json.py \
  benchmark_results.json --threshold 5 --top 20
```

Review unmatched base/head counts before trusting geomean speedup.

## Visualization dependencies missing

Module and comparison visualization require plotting dependencies. If plots are optional, keep the benchmark JSON and text summary. If plots are required, install the benchmark extras or equivalent `matplotlib` and `pandas` into the active environment.

## Safe fallback when hardware is unavailable

Do not fabricate benchmark results. Provide:

- the exact command that should be run on the target backend;
- expected JSON output path;
- environment variables that must be fixed;
- the promotion/no-go criteria;
- a note that no performance claim is verified until the command succeeds on hardware.
