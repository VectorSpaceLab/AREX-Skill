---
name: training-and-adapters
description: "Prepare and reason about DeTikZify training, pretraining,
  refinement, sketchification, TikZero adapter workflows, checkpoints, and
  distributed GPU launch patterns."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training and Adapters

Use this sub-skill when the task is about fine-tuning, pretraining, refinement, sketchification, TikZero adapter work, distributed GPU launch patterns, or checkpoint recovery in DeTikZify.

Route away from this sub-skill when the task is only about one-off inference, the browser UI, or evaluation metrics.

## Fast Path

1. Confirm the package and GPU environment are healthy:
   ```bash
   python scripts/api_smoke.py
   ```
2. Read the workflow reference before starting a long run:
   ```text
   references/workflows.md
   ```
3. Check the training-specific failure modes if the launch uses DeepSpeed, TRL, or adapter checkpoints:
   ```text
   references/troubleshooting.md
   ```

## What This Sub-Skill Owns

- standard fine-tuning on DaTikZ-style data
- projection pretraining on large figure datasets
- GRPO / self-feedback refinement workflows
- sketchification and sketch-augmented training data generation
- TikZero adapter pretraining and end-to-end adapter fine-tuning
- checkpoint resumption, `WORLD_SIZE`, `RANK`, and distributed GPU launch concerns
- DeepSpeed and gradient-checkpointing choices

## Common Decisions

- Use `torchrun --nproc_per_node gpu` for the repo's GPU-first training scripts.
- Use `deepspeed` only when the job needs it; do not add it to every run by default.
- Use `gradient_checkpointing` when memory pressure matters more than speed.
- Watch the output directory handling: some flows resume from the last checkpoint unless `overwrite` or a fresh directory is chosen.
- Keep the dataset requirements explicit: DaTikZ, ArxivCap, SPIQA, OpenMoji, adapter checkpoints, and sketch/parquet artifacts are workflow-specific.
- Treat `examples/refine.py` as the most dependency-heavy path because it needs TRL vision support plus compile-backed rewards.

## Bundled References

- [references/cli-reference.md](references/cli-reference.md): command-line arguments, launch patterns, and output behavior.
- [references/workflows.md](references/workflows.md): end-to-end training, pretraining, refinement, and TikZero recipes.
- [references/troubleshooting.md](references/troubleshooting.md): long-run failures, missing dependencies, checkpoint, and distributed training issues.

## Guardrails

- These workflows are intentionally expensive. Use them only when the user actually wants to train or refine a model.
- Do not assume CPU fallback is adequate for the repo's training paths.
- Do not start from the UI or inference sub-skill when the task is mainly about gradients, checkpoints, or dataset transforms.
