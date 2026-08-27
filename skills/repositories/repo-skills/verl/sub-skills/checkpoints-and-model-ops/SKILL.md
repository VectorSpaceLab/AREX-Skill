---
name: checkpoints-and-model-ops
description: "Operate verl checkpoints, model merging/export, LoRA checkpoint
  handling, and profiling diagnostics without changing training setup or data
  schema."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# checkpoints-and-model-ops

Use this sub-skill when a task involves an existing verl run or checkpoint tree: identifying whether a checkpoint is FSDP, Megatron, or already HuggingFace-format; planning `verl.model_merger` usage; diagnosing save/load contents; handling LoRA export implications; or enabling profiling/performance diagnostics after training is already configured.

Do not use this for initial installation, environment setup, training command assembly, reward/data schemas, or choosing datasets. Route those to the root skill or the training/data sub-skills.

## Fast path

1. Inspect the checkpoint directory without loading tensors:
   ```bash
   python sub-skills/checkpoints-and-model-ops/scripts/inspect_checkpoint_path.py CHECKPOINT_DIR --pretty
   ```
2. If the path is a run root, choose a `global_step_*` directory and then the role directory, usually `actor`.
3. If the role directory is FSDP, merge with `python -m verl.model_merger merge --backend fsdp --local_dir ROLE_DIR --target_dir TARGET_DIR`.
4. If the role directory is Megatron, inspect `checkpoint_contents_metadata.json` first; merge with `--backend megatron` only when model shards or HF config artifacts are present as expected.
5. If the role directory already contains a complete HuggingFace tree, prefer copying/validating that tree over re-merging large shards.

## References

- [Checkpoint layouts, save contents, and model merging](references/checkpoints-and-merging.md)
- [Performance tuning and profiling operations](references/performance-and-profiling.md)
- [Checkpoint/model-ops troubleshooting](references/troubleshooting.md)

## Bundled script

- [Safe checkpoint path inspector](scripts/inspect_checkpoint_path.py): directory-only argparse helper that detects likely run roots, step roots, FSDP role directories, Megatron role directories, HuggingFace exports, and next-action suggestions. It does not import verl, torch, or load checkpoint tensors.

## Native verification anchors

Relevant upstream CPU or focused tests for future maintainers include checkpoint-engine global-step propagation, checkpoint cleanup retention, Megatron checkpoint manager behavior, and FSDP LoRA merge semantics. Treat GPU-heavy LoRA/FSDP tests as native candidates only when the requested environment has the needed accelerators.
