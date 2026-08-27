---
name: "training-recipes"
description: "Operate x-transformers training recipe examples safely: catalog
  scripts, dependencies, data assumptions, and CPU-friendly copy-task smoke
  adaptation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Training Recipes

Use this sub-skill when you need to choose, adapt, or smoke-test the repository's `train_*.py` examples without reopening the source checkout.

## Fast decision path

1. For a safe local check, run the bundled copy-task smoke:

   ```bash
   python scripts/copy_task_smoke.py --steps 1 --device cpu
   ```

   It is synthetic, CPU-friendly, and derived from the copy recipe. It verifies a tiny forward/backward/generate loop; it does **not** prove task convergence.
2. For recipe selection, read [references/recipe-catalog.md](references/recipe-catalog.md). It lists every training script, required extras, data expectations, CLI style, and run-safety tier.
3. If a recipe fails to start or stalls, use [references/troubleshooting.md](references/troubleshooting.md) before increasing hardware, installing extras, or enabling online logging.

## Boundaries

- This sub-skill covers recipe cataloging, command patterns, dataset/source notes, dependency variants, and the bundled copy-task smoke.
- For core model construction APIs, route to `../core-models/SKILL.md`.
- For wrapper behavior and sequence workflow internals, route to `../sequence-workflows/SKILL.md`.
- Treat the native training scripts as examples, not reusable libraries: several execute training at module import time, assume `data/enwik8.gz`, or force CUDA/logging-heavy defaults.
