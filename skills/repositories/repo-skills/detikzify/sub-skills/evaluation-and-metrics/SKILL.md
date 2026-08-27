---
name: evaluation-and-metrics
description: "Evaluate DeTikZify outputs with metric wrappers, score generated
  TikZ programs, and reason about the repository's evaluation pipeline."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluation and Metrics

Use this sub-skill when the task is about `examples/eval.py`, metric wrappers, score computation, comparison against references, or the evaluation side of compiled TikZ generation.

Route away from this sub-skill when the task is mostly about producing one new program, launching the web UI, or changing training loops.

## Fast Path

1. Confirm the package and compile helpers are available:
   ```bash
   python scripts/api_smoke.py
   python scripts/tikz_smoke.py
   ```
2. Read the metric reference before trying a scoring run:
   ```text
   references/metrics.md
   ```
3. Read the workflow reference if you need the model-input and caching behavior:
   ```text
   references/workflows.md
   ```

## What This Sub-Skill Owns

- the `detikzify.evaluate` metric wrappers
- score aggregation over generated and reference TikZ
- `ImageSim` and the perceptual scoring path
- `ClipScore`, `CrystalBLEU`, `DreamSim`, `KernelInceptionDistance`, and `TexEditDistance`
- redacted compile / rasterize metrics and token-efficiency style summaries
- the repo's evaluation pipeline and its compile-backed checks

## Common Decisions

- Use `ImageSim` / model-based scoring when you want perceptual similarity.
- Use the faster compiler-diagnostics path when you only need a cheap evaluation pass.
- Remember that some metrics are lazily imported and need optional dependencies.
- Keep the compile/rasterize path in mind: evaluation is not just string comparison.
- If the task asks about redacted outputs, inspect the compileable document and the redaction step separately.

## Bundled References

- [references/metrics.md](references/metrics.md): metric roles, lazy dependencies, and scoring behavior.
- [references/workflows.md](references/workflows.md): the evaluation pipeline, model-input choices, cache behavior, and scoring stages.
- [references/troubleshooting.md](references/troubleshooting.md): missing metric deps, compile issues, and evaluation-specific failure modes.

## Guardrails

- A metric import succeeding does not prove the model or render path works.
- Do not ignore compile failures when the score depends on compiled TikZ.
- Do not assume optional metric dependencies are present in a minimal install.
