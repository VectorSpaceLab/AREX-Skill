# Benchmarking Reference

This reference distills the Flash Linear Attention benchmark system into a self-contained operating guide for correctness-gated performance work.

## Rule of use

Benchmark only after correctness is green. The gated driver runs the op's pytest file first, then measures latency only when the gate exits successfully. A speedup from an ungated run is a development signal, not a promotable result.

## Command map

The `benchmarks.*` commands in this section are for repository-maintenance tasks in an active FLA checkout. For package-only tasks, use the bundled command builder to prepare a command for the appropriate checkout instead of assuming benchmark modules are installed.

### Correctness-gated driver

Use this for optimization-loop iterations and final claims in an FLA checkout:

```bash
python -m benchmarks.ops.verify --list
python -m benchmarks.ops.verify --op chunk_gla --base main
python -m benchmarks.ops.verify --op chunk_gla --gate-k T8192 --modes fwd
python -m benchmarks.ops.verify --op fused_attnres --profile
```

Important flags:

| Flag | Meaning | Promotion status |
| ---- | ------- | ---------------- |
| `--list` | Print registered benchmark targets and their import paths. | Safe discovery. |
| `--op <name>` | Select one registered op. | Required for a real run. |
| `--base <ref>` | Add a baseline column by benchmarking a git ref through the unified runner. | Use for final before/after evidence. |
| `--gate-k <expr>` | Pass a pytest `-k` expression to run a subset of the frozen test file. | Fast signal only; never final promotion. |
| `--modes fwd fwdbwd` | Measure forward and/or forward+backward. | Include every affected mode before promotion. |
| `--profile` | Save a torch profiler trace for one registry shape after the gate and benchmark. | Useful handoff, not a replacement for backend profiler evidence. |
| `--test-file <path>` | Override the derived pytest file when the registry name and test filename differ. | Acceptable only as an explicit pointer to the frozen test. |
| `--no-gate` | Skip correctness. | Development only; never promote from it. |

### Unified op runner

Use this for direct timing, registry work, JSON output, or diff-based selection when a correctness gate is handled elsewhere:

```bash
python -m benchmarks.ops.run --list
python -m benchmarks.ops.run --op chunk_gla --base main --json results.json
python -m benchmarks.ops.run --op chunk_gla --modes fwd
python -m benchmarks.ops.run --op fused_attnres --backend gluon --base main
python -m benchmarks.ops.run --from-diff --diff-base main --diff-head HEAD
python -m benchmarks.ops.run --op chunk_gla --custom-shapes '{"tiny": {"B": 1, "T": 2048, "H": 16, "D": 128}}'
```

`run.py` measures latency and formats tables. It does not prove correctness. It can save `{"machine_info": ..., "results": [...]}` JSON. When `--base` is supplied, it creates a temporary git worktree, installs the baseline there, and compares the same registered shapes without stashing or changing the current worktree.

### Cross-commit comparison helper

For local branches or CI-style checks that need affected-op selection, regression thresholds, and optional plot generation, FLA's repository-maintenance workflow includes a checkout-owned comparison helper. Treat it as a checkout-specific native tool: use it only when the user is already maintaining an FLA checkout, and prefer `benchmarks.ops.verify --base <ref>` plus the bundled command builder for ordinary command construction.

When the comparison helper is used in a checkout, omitting explicit benchmark ops lets it map changed Python files to registered ops; shared op utility changes select all registered ops. Its JSON format contains `base_results`, `head_results`, `regressions`, `speedups`, and machine metadata.

## `verify.py` versus `run.py`

| Driver | First action | Measures latency? | Baseline compare? | Best use |
| ------ | ------------ | ----------------- | ----------------- | -------- |
| `benchmarks.ops.verify` | Runs the frozen pytest gate for the op. | Yes, only if the gate passes unless `--no-gate` is used. | Yes via `--base`. | Iteration and final claims. |
| `benchmarks.ops.run` | Imports the registered op and prepares registry inputs. | Yes. | Yes via `--base`; auto-detects `main` on feature branches. | Raw benchmark runs, JSON, registry debugging. |
| Checkout-owned comparison helper | Resolves refs and selected ops, then checks out/reinstalls both sides. | Yes. | Yes, explicit base/head. | CI-like regression detection and saved comparison JSON. |

## Benchmark registry semantics

Each registered op describes how to import the callable, generate inputs, and select shapes. Treat the registry as the source of benchmark shape identity; do not hand-roll a one-off benchmark and call it equivalent unless the shape, dtype, mode, backend, and input transforms match.

Core fields:

| Field | Meaning |
| ----- | ------- |
| `name` | Benchmark target, for example `chunk_gla`. |
| `import_path` / `func_name` | Module and callable used by the runner. `func_name` is used when the registry name differs from the function attribute. |
| `inputs` | Tensor specs mapping function arguments to shape helpers and transforms. |
| `extra_kwargs` | Constant keyword arguments passed to the op. |
| `output_is_tuple` | Whether the first tuple element is used for backward timing. |
| `skip_backward` | Removes `fwdbwd` mode for forward-only targets. |
| `post_init` | Custom input mutation, used for non-standard structures such as RWKV7 or sparse attention block indices. |
| `category` | Group label printed by `--list`. |
| `dim_constraints` | Shape filters, for example only allowing selected head dimensions. |
| `default_shapes` | Per-op shape sweep replacing the global shape list. |
| `test_file` | Explicit frozen pytest path used by the gated driver when derivation would be wrong. |
| `backend_env` | Backend selector mapping used by `--backend`, for example enabling a Gluon variant. |

Global shape sweep for ordinary B/T/H/D op targets:

| Shape id | B | T | H | D |
| -------- | -: | -: | -: | -: |
| `B1_T8192_H96_D128` | 1 | 8192 | 96 | 128 |
| `B2_T16384_H16_D128` | 2 | 16384 | 16 | 128 |
| `B4_T2048_H16_D128` | 4 | 2048 | 16 | 128 |
| `B4_T4096_H64_D128` | 4 | 4096 | 64 | 128 |
| `B8_T2048_H32_D256` | 8 | 2048 | 32 | 256 |
| `B8_T1024_H8_D64` | 8 | 1024 | 8 | 64 |

Representative registered targets:

| Target | Category / notes |
| ------ | ---------------- |
| `chunk_retention`, `chunk_linear_attn` | Simple q/k/v targets. |
| `chunk_gla` | Elementwise gate target with clamped log-sigmoid gate inputs. |
| `chunk_delta_rule` | Beta target; frozen gate file is explicitly mapped. |
| `chunk_gdn`, `chunk_kda` | Gate+beta targets with QK L2 normalization kwargs; `chunk_gdn` maps to the gated-delta-rule function. |
| `chunk_simple_gla` | Head-gate target. |
| `chunk_rwkv6`, `chunk_rwkv7` | RWKV targets; RWKV7 has custom small-positive `a`/`b` initialization. |
| `chunk_comba`, `chunk_dplr_delta_rule`, `chunk_lightning_attn` | Specialized op families with extra tensors or kwargs. |
| `parallel_attn`, `flash_attn` | Attention baselines; `flash_attn` requires the optional external package. |
| `fused_attnres`, `naive_attnres` | Layer-axis residual aggregation with an `L` dimension; `fused_attnres` declares a Gluon backend selector. |
| `parallel_nsa` | Native sparse attention with GQA and generated block indices; uses a custom shape sweep up to long contexts. |

## Measurement methodology

The unified runner uses `torch.bfloat16` benchmark inputs. For every valid shape, it first warms up forward+backward to trigger Triton autotuning, then measures with `triton.testing.do_bench` using median/p20/p80 quantiles. Input tensors and deterministic transforms are prepared before timing; the measured function is the op call plus backward only when `fwdbwd` is selected.

Benchmark rows include:

- `op`, `mode`, `B`, `T`, `H`, `D`, plus extra dimensions such as `L`, `HQ`, `S`, or `block_size` when present.
- `median_ms`, `p20_ms`, `p80_ms` for latency.
- Machine metadata such as GPU/backend, PyTorch, Triton, and git label when JSON is saved by the runner.

## Module, training, and generation benchmarks

Module benchmarks use Triton's `perf_report` style and the shared module runner to write CSV, PNG, and HTML outputs. They are useful for fused modules such as activations, convolution, norms, cross entropy, and token shift.

Training-throughput and generation benchmark scripts measure model-level throughput, peak memory, and optional torch-profiler traces. Keep them out of this sub-skill's core route unless the performance task explicitly crosses from an op into model-level throughput; this sub-skill focuses on op benchmarking and optimization discipline.

## Benchmark environment variables

Benchmark-only variables:

| Variable | Default | Effect |
| -------- | ------- | ------ |
| `FLA_BENCH_OP_WARMUP_ITERS` | `5` | Extra forward+backward warmup iterations per shape before timing. |
| `FLA_BENCH_WARMUP_MS` | `25` | Triton `do_bench` warmup window in milliseconds. |
| `FLA_BENCH_REP_MS` | `100` | Triton `do_bench` measurement window in milliseconds. |
| `FLA_BENCH_COOLDOWN_SEC` | `0` | Sleep between HEAD and BASE runs in the cross-commit compare helper to reduce thermal bias. |

Environment variables that can change what is measured:

| Variable | Effect |
| -------- | ------ |
| `FLA_DISABLE_BACKEND_DISPATCH` | Forces default Triton paths by bypassing optional dispatch when set. |
| `FLA_TILELANG`, `FLA_FLASH_KDA`, `FLA_INTRACARD_CP` | Enable or disable optional specialized dispatch paths when the needed packages/backends are installed. |
| `FLA_CACHE_MODE`, `FLA_CACHE_RESULTS`, `FLA_CONFIG_DIR`, `FLA_GPU_NAME` | Control FLA config-cache and autotune-cache behavior; document these when comparing numbers. |
| `FLA_USE_TMA`, `FLA_TRIL_PRECISION`, `FLA_USE_FAST_OPS` | Change selected hardware or numeric paths; do not change them on only one side of a before/after comparison. |
| `TRITON_CACHE_DIR` | Controls Triton's cache location; clearing or isolating it can diagnose stale autotune behavior. |
| `MPLBACKEND=Agg` | Useful for headless module benchmark visualization. |
