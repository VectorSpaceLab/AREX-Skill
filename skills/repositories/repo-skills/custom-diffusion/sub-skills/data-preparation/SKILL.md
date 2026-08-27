---
name: data-preparation
description: "Prepare instance images, prior-preservation bundles, and concept
  metadata for Custom Diffusion training."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Data preparation

Use this sub-skill when you need to stage and validate training inputs before a Custom Diffusion run.

It covers:

- instance image directories for one or more concepts
- generated or real-prior class image layouts
- `images.txt` / `caption.txt` / `urls.txt` bundles
- concept-list JSON manifests
- offline validation of regularization inputs

It does not cover training launch, sample generation, delta math, or benchmark evaluation. Route those tasks to:

- [`../training/SKILL.md`](../training/SKILL.md)
- [`../inference/SKILL.md`](../inference/SKILL.md)
- [`../checkpoint-tools/SKILL.md`](../checkpoint-tools/SKILL.md)
- [`../benchmarking/SKILL.md`](../benchmarking/SKILL.md)

## Start here

1. Read [`references/data-formats.md`](references/data-formats.md).
2. Run [`scripts/validate_regularization_layout.py`](scripts/validate_regularization_layout.py).
3. Read [`references/workflows.md`](references/workflows.md) if you need the end-to-end prep flow.
4. Check [`references/troubleshooting.md`](references/troubleshooting.md) when a manifest or layout fails.

## Network boundary

The real-prior retrieval helper is reference-only because it queries the LAION KNN service and downloads images. Do not make data-preparation depend on that network path when an offline bundle is available.
