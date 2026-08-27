---
name: training
description: "Configure and safely operate PointLLM's two-stage training
  workflow, flags, checkpoints, and resource-sensitive validation without
  launching distributed training."
disable-model-invocation: true
metadata:
  disco-role: operating
license: CC BY-NC-SA 4.0
---

# PointLLM training

Use this sub-skill when a Researcher needs to configure, inspect, resume, or
troubleshoot PointLLM v1 training. It covers the repository's two stages and
its custom dataclass flags. It does **not** download data or weights, change an
environment, or launch `torchrun`.

## Route first

1. Establish local paths for an initial Hugging Face model directory, the
   point-cloud directory, its annotation JSON, and a writable output directory.
2. Choose exactly one stage:
   - **Stage 1** aligns the language model with PointBERT features. The shipped
     profile fixes the LLM and point backbone and tunes the point projector
     (new point-token input embeddings can also become trainable). It loads a
     separate point-backbone checkpoint.
   - **Stage 2** starts from the complete Stage-1 output, enables LLM tuning,
     uses the complex-instruction conversations, and keeps the point backbone
     in no-gradient/eval execution with the shipped `fix_pointnet=True`.
3. Run the bundled validator before editing a command or starting a job:

   ```bash
   python scripts/validate_training_config.py \
     --stage 1 --config training.json
   ```

   Add `--allow-missing` only for a path-planning dry run. The validator never
   invokes `torchrun`, imports the training entry point, or loads a checkpoint.
4. Read [workflows.md](references/workflows.md) for inert command templates and
   checkpoint/resume behavior. Read [configuration.md](references/configuration.md)
   before changing a flag. Use [troubleshooting.md](references/troubleshooting.md)
   when a check fails.

## Required stage invariants

- Stage 1: `stage_2=False`, `model_name_or_path` is the initial LLM/PointLLM
  directory, and `point_backbone_ckpt` points to the compatible PointBERT file.
- Stage 2: `stage_2=True`, `model_name_or_path` is the Stage-1 final output;
  do not point it at the initial directory unless intentionally restarting.
- Both stages require an annotation JSON and point-cloud directory. With
  `use_color=True`, each selected file is expected to be `(N, 6)` with XYZ in
  the first three columns and RGB in the final three columns.
- Keep `pointnum=8192` unless the model's PointBERT configuration and every
  `{object_id}_{pointnum}.npy` file have been changed together.
- Do not infer successful training from a created output directory. Confirm
  logs, loss progress, saved model state, and (when applicable) `point_proj.bin`.

## Resource and safety gates

- The reference profile uses one node and eight processes. This is a launch
  template, not an assertion that the current machine can run it.
- `bf16=True` requires a compatible accelerator and matching PyTorch/CUDA
  runtime. The inspection baseline supplied for this skill is Python 3.10,
  torch 2.0.1+cu117, Transformers 4.28.0.dev0 at commit `cae78c46`,
  tokenizers 0.12.1, and an A100 40GB (compute capability 8.0). Re-check the
  actual runtime rather than copying this baseline into a new environment.
- `train_mem.py` applies the repository's FlashAttention monkey patch before
  importing the model. A compatible compiled `flash-attn` is therefore a hard
  precondition for that entry point; `train.py` avoids that explicit patch but
  is not a performance or memory-equivalent fallback.
- Stage 2's `full_shard auto_wrap` and `LlamaDecoderLayer` settings use the
  source's experimental partially-frozen/FSDP path. Treat FSDP warnings,
  missing `use_orig_params` support, or backend/version mismatch as stop
  conditions; do not silently remove FSDP or unfreeze the point backbone.
- Stop before launch if the validator reports a stage contradiction, missing
  required input, incompatible point-backbone configuration, or unavailable
  required compiled backend. Stop after launch if the first batch cannot load,
  point-token counts disagree, or no trainable parameters receive loss.

## Outputs and handoff

The training code auto-resumes when `output_dir` already contains any
`checkpoint-*` directory. The templates set `save_strategy="no"`, so ordinary
runs do not create periodic checkpoints. `PointLLMTrainer` writes adapter state
under `point_proj/` for checkpoint saves and writes a final `point_proj.bin` when
adapter tuning is enabled; the final save also uses the Hugging Face model
serialization path. Preserve the output directory and trainer state together
when handing Stage 1 to Stage 2.

This sub-skill links only to its bundled references and validator. It records
source-derived behavior; it does not claim that a training run succeeded.
