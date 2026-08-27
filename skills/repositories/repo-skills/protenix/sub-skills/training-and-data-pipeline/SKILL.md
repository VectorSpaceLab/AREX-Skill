---
name: training-and-data-pipeline
description: "Plan Protenix training data roots, custom CIF preprocessing, safe
  training and fine-tuning commands, DDP, W&B, checkpoints, and data-layout
  troubleshooting without launching expensive jobs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Protenix Training and Data Pipeline

Use this sub-skill when a task involves Protenix training or fine-tuning data roots, released or custom bioassembly data, CCD cache decisions, index CSVs, training command planning, DDP, W&B, checkpoints, or safe preflight checks.

## Start Here

1. Classify the task as data-root inspection, custom CIF preprocessing, CCD-cache planning, single-process training, multi-GPU/DDP training, or fine-tuning from checkpoints.
2. For data-root or index questions, run `scripts/check_training_data_layout.py`; it is read-only and uses only the Python standard library.
3. For custom CIF preprocessing, use `scripts/build_prepare_training_data_command.py` to print the command for later approval; read `references/preprocessing.md` before recommending the actual job.
4. For training or fine-tuning, use `scripts/build_training_command.py` to print a no-run command; read `references/training-workflows.md` and `references/configuration.md` before adapting overrides.
5. Treat full data downloads, CCD refreshes, MSA/template generation, preprocessing, and training as expensive operations that require explicit resource and side-effect approval.

## References

- `references/data-layout.md` explains `PROTENIX_ROOT_DIR`, released data components, MSA/template and RNA MSA directories, downloader modes, and safe root checks.
- `references/preprocessing.md` explains CIF-to-bioassembly preprocessing, cluster files, distillation mode, CCD cache handling, output `.pkl.gz` payloads, and index CSV schema.
- `references/training-workflows.md` explains train and fine-tune command anatomy, DDP with `torchrun`, W&B defaults, checkpoint behavior, kernels, output directories, and resource cautions.
- `references/configuration.md` explains Protenix config parsing, dot-notation overrides, required fields, dataset overrides, optimizer/scheduler settings, and validation order.
- `references/troubleshooting.md` maps common data, preprocessing, CUDA/DDP, W&B, checkpoint, config, and dependency failures to safe next actions.

## Bundled Tools

- `scripts/check_training_data_layout.py`: read-only checker for a `PROTENIX_ROOT_DIR`-style root and optional index CSV schemas.
- `scripts/build_prepare_training_data_command.py`: no-run builder for CIF preprocessing commands; it can include CCD-cache advisory text but does not refresh CCD data.
- `scripts/build_training_command.py`: no-run builder for training and fine-tuning commands with W&B disabled by default and optional `torchrun` launcher output.

## Route Elsewhere

- Single-job prediction, `protenix pred`, batch inference, and inference output interpretation belong to `../cli-and-inference/SKILL.md`.
- MSA/template search mechanics, input-prep CLI flows, and RNA MSA search details belong to `../msa-template-and-prep/SKILL.md`.
- Low-level kernels, model internals, advanced model config internals, and performance tuning beyond launch planning belong to `../advanced-model-configuration/SKILL.md`.

## Safety Rules

- Do not run data download, CCD refresh, CIF preprocessing, MSA/template search, or training commands as smoke tests.
- Default generated training commands to `--use_wandb false`; enable W&B only when the user confirms credentials, project naming, network policy, and non-interactive behavior.
- Prefer `python -m runner.train` for single-process training and `torchrun -m runner.train` for DDP command planning.
- Do not recommend `--triangle_attention deepspeed` unless the user has a compatible CUDA, DeepSpeed, Pydantic, and CUTLASS setup.
- Keep generated commands and notes portable: use user-supplied paths and placeholders, not local checkout paths or environment prefixes.
