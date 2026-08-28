# Evaluation reference

FastVideo evaluation has dataset/metric registries, media input/output helpers,
worker/pool orchestration, and result types. Metrics can target video quality,
physics/semantic behavior, audio, or reference similarity depending on the
installed extras.

Useful CLI discovery:

```bash
fastvideo eval list
fastvideo eval run --help
```

Use the exact metric and dataset names reported by the installed CLI. VBench and
other large suites may need downloaded references, GPU models, and substantial
time. Judge-style metrics can require a remote API key; keep them separate from
local deterministic validation.

A quality regression should compare the same prompt/sample and fixed seed under
the baseline and candidate configuration. Report metric version, resolution,
frames, backend, and any missing reference/media files. Do not convert a skipped
GPU/remote metric into a passing score.
