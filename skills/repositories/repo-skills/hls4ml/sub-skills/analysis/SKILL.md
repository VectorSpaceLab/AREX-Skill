---
name: analysis
description: "Tune generated hls4ml designs with profiling, automatic precision
  inference, bit-exact propagation, resource knobs, FIFO depth, BramFactor, and
  optimization API guardrails."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# hls4ml analysis sub-skill

Use this sub-skill after a model has already been converted, or after a frontend sub-skill has produced an `hls_config` that needs tuning. It helps future agents profile numerical ranges, choose or validate precisions, reason about bit-exact conversion, tune resource/latency knobs, and avoid overclaiming hardware results.

## Route by task

- **Weights/activation profiling, layer-by-layer numerical comparison, or trace setup:** read `references/profiling.md`.
- **`Precision: auto`, `granularity='name'`, quantizer-derived precision, or `bit_exact`:** read `references/precision-and-bit-exact.md`.
- **`ReuseFactor`, `Strategy`, FIFO depth optimization, `BramFactor`, or resource/latency tradeoffs:** read `references/resource-tuning.md`.
- **Hardware-aware pruning or weight-sharing workflows:** read `references/optimization-api.md` before importing optimization APIs.
- **Unexpected accuracy/resource behavior or missing optional dependencies:** read `references/troubleshooting.md`.
- **Quick config inspection:** run `scripts/inspect_precision_config.py` to print a tiny `granularity='name'` config and the paths where precision/reuse keys live.

## Boundaries and guardrails

- Do **not** perform first-time model conversion work here; route conversion mechanics, frontend dependencies, serialization, and CLI conversion to the `frontends` sub-skill.
- Do **not** run or claim vendor synthesis/build results from this sub-skill. FIFO-depth optimization and resource reports require backend toolchain and co-simulation evidence; route execution and report parsing to `backends`.
- Do **not** author custom layers, parser handlers, optimizer passes, or plugins here; route extension authoring to `extensions`.
- Treat CPU `compile()`/`predict()` parity as numerical evidence only. It is not synthesis evidence, resource utilization evidence, or FIFO-deadlock evidence.
- The profiling extra was available during drafting; the model-optimization optional extra was not fully available because its pinned `ortools` dependency did not resolve for Python 3.11. See `references/optimization-api.md` for the safe runtime interpretation.
