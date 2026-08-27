---
name: benchmarking
description: "Validate and interpret CustomConcept101 benchmark artifacts for
  CLIP text alignment, CLIP image alignment, and DINO image alignment."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# CustomConcept101 benchmarking

Use this sub-skill when you need to validate generated sample layouts or interpret CustomConcept101 evaluation results.

It covers:

- `sample_root/samples/*.png` layout checks
- `sample_root/prompts.json` prompt-stem coverage
- `+`-separated `target_paths` parsing
- CLIP text alignment, CLIP image alignment, and DINO image alignment outputs

It does not cover image generation or retraining. Route those tasks to [`../inference/SKILL.md`](../inference/SKILL.md) and [`../training/SKILL.md`](../training/SKILL.md).

## Start here

1. Read [`references/data-formats.md`](references/data-formats.md).
2. Run [`scripts/validate_benchmark_layout.py`](scripts/validate_benchmark_layout.py) before any expensive metric run.
3. Read [`references/workflows.md`](references/workflows.md) for the evaluation contract.
4. Check [`references/troubleshooting.md`](references/troubleshooting.md) when PNG counts, prompt stems, CUDA, CLIP/DINO downloads, or pickle updates fail.

## Constraints

- The source evaluator is CUDA-only and may download CLIP/DINO weights.
- The validator is layout-only and does not load models.
- Benchmark target images stay external to the runtime tree.
