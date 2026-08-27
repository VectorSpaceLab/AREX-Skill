---
name: benchmarking-and-optimization
description: "Routes FLA correctness-gated op benchmarking, optimization loops,
  profiling handoffs, and benchmark summaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# benchmarking-and-optimization

Use this sub-skill for Flash Linear Attention performance work where the deliverable depends on trustworthy measurements: op microbenchmarks, before/after comparisons, optimization-loop discipline, profiler handoff, benchmark registry updates, and summarizing saved benchmark JSON.

## Use this route for

- Running a correctness-gated op benchmark before claiming a speedup.
- Listing or interpreting registered op benchmark targets.
- Comparing an op against a baseline ref and deciding whether a performance change is promotable.
- Planning a multi-iteration kernel optimization loop with frozen correctness gates and auditable logs.
- Handing NVIDIA or Ascend work to the appropriate profiling workflow after the benchmark identifies a hot path.
- Summarizing local JSON files produced by benchmark comparison or unified op benchmark runs.

## Do not use this route for

- Designing generic operator correctness coverage; use the correctness/testing route and return here for performance gates.
- Layer/model usage, training recipes, generation workflows, or checkpoint evaluation.
- Changing numerical tolerances, references, public APIs, or benchmark criteria to make a speedup pass.
- Running native tests or GPU benchmarks when the active task only asks for command construction or local JSON summarization.

## Read first

- `references/benchmarking.md` for command patterns, registry semantics, result formats, and benchmark environment variables.
- `references/optimization-loop.md` for the frozen-test contract, iteration log, promotion bar, no-go bar, and profiler handoffs.
- `references/troubleshooting.md` for red gates, missing registry entries, noisy measurements, backend dispatch, and JSON-summary failures.

## Skill-owned scripts

- `scripts/fla_verify_op_command.py` — builds and prints a safe `python -m benchmarks.ops.verify ...` command. It does not run tests or benchmarks.
- `scripts/summarize_benchmark_json.py` — summarizes local benchmark JSON without importing FLA or touching GPUs.

## Fast routing checklist

1. If the user asks for a command, build it with the skill-owned command builder and return the printed command.
2. If the user asks whether a result is usable, inspect the gate status first. A red or skipped gate means no speedup may be promoted.
3. If the user asks for optimization, require a task contract: op name, target shapes, baseline ref, allowed backend/language, validation command, benchmark command, and promotion criteria.
4. If benchmark JSON already exists, summarize it locally before asking for new hardware runs.
5. If profiler evidence is needed, route by backend: NVIDIA/Triton/Gluon/TileLang/CUDA to the NVIDIA profiling workflow; Ascend/Triton-Ascend/NPU to the Ascend profiling workflow.

## Minimal safe commands

```bash
# Discover benchmark targets.
python -m benchmarks.ops.verify --list

# Full frozen gate, then benchmark against a baseline.
python -m benchmarks.ops.verify --op chunk_gla --base main

# Fast signal only; do not promote from a subset gate.
python -m benchmarks.ops.verify --op chunk_gla --gate-k T8192 --modes fwd

# Print a command without running it.
python scripts/fla_verify_op_command.py \
  --op chunk_gla --base main --modes fwd fwdbwd

# Summarize saved JSON locally.
python scripts/summarize_benchmark_json.py \
  benchmark_results.json --threshold 5 --top 10
```

## Promotion rule

A performance change is promotable only when the full frozen gate passes, the same-shape before/after benchmark shows a repeatable improvement, and profiler or roofline evidence explains the mechanism. A faster number without a green gate, without same-hardware baseline, or without an explanation is a no-go or an unfinished loop.
