---
name: evaluation-and-performance
description: "Guides FastVideo media metrics, benchmark configuration, quality regression checks, and honest performance comparisons."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluation and performance

Use for registered metrics, video/image/audio evaluation, benchmark requests,
latency/memory comparisons, and regression interpretation.

## Workflow

1. Fix model revision, prompt/data sample, seed, dimensions, FPS, steps,
   backend, precision, and output policy.
2. Decide whether the operation is a metric run, a server benchmark, a quality
   regression, or a component profile. Read [evaluation reference](references/evaluation.md)
   and [performance reference](references/performance.md).
3. Install only the metric extra required by the selected dataset/metric. Some
   judge metrics call remote APIs and need credentials; do not enable them in a
   safe local smoke.
4. Warm up compiled or kernel-backed runs, exclude startup/download/compile
   time, and compare steady-state runs with identical shapes.
5. Preserve raw outputs, config, metric versions, and failure/skipped reasons.

The CLI exposes `fastvideo eval list`, `fastvideo eval run`, and `fastvideo
bench` for benchmark-server workloads. Use [evaluation troubleshooting](references/troubleshooting.md)
when metrics, codecs, references, or server connectivity fail. Run the bundled
[metric inspector](scripts/inspect_metrics.py) for a read-only registry listing
when the package is installed.
