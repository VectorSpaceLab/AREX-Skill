# Checkpoints and model merging

This reference covers existing verl checkpoint trees, checkpoint content semantics, HuggingFace export, model merger usage, Megatron layout migration, and LoRA implications. It assumes verl is already installed and the user has an existing checkpoint directory.

## Terminology and path levels

- **Run root**: default training output root such as `checkpoints/${trainer.project_name}/${trainer.experiment_name}`.
- **Step root**: a child named `global_step_N` or `global_steps_N`, depending on the producing code path/version.
- **Role directory**: a child under a step root such as `actor`, `critic`, `ref`, `rollout`, or `reward_model`.
- **HuggingFace export tree**: a directory with artifacts such as `config.json`, tokenizer files, generation config, and weight files (`*.safetensors`, `pytorch_model*.bin`).
- **Native training checkpoint**: framework-native shards plus optimizer/extra state used for resume; this is not always directly loadable as a HuggingFace model.

Always identify which level the user provided. `verl.model_merger` expects a role directory for `--local_dir`, not the whole run root.

## Save/load contents

`checkpoint.save_contents` and `checkpoint.load_contents` accept combinations of:

- `model`: framework-native model state. For FSDP this means per-rank sharded model files. For Megatron this can mean `model/huggingface`, `model/dist_ckpt`, or both depending on bridge and dist-checkpoint settings.
- `optimizer`: optimizer state, sharded for FSDP and Megatron.
- `extra`: scheduler/RNG state and, for Megatron, serialized TransformerConfig when relevant.
- `hf_model`: full HuggingFace-format model export. Megatron requires an active mbridge/bridge object for this path.

For FSDP, non-`hf_model` contents are effectively coupled for normal training resume. If the user asks to save only one of model/optimizer/extra for FSDP, verify the current manager behavior before promising independent partial saves.

## FSDP role layout

A typical FSDP role directory contains:

```text
actor/
  huggingface/
  fsdp_config.json
  model_world_size_<W>_rank_<R>.pt
  optim_world_size_<W>_rank_<R>.pt
  extra_state_world_size_<W>_rank_<R>.pt
  lora_train_meta.json        # when LoRA metadata is available
```

Operational implications:

- `fsdp_config.json` records the FSDP world size and version used by the merger.
- `model_world_size_*_rank_*.pt` indicates sharded model state requiring merge for HF deployment.
- `huggingface/` may contain tokenizer/config and, when `hf_model` was saved, a deployable HF model.
- FSDP merger reconstructs tensors by loading rank shards on CPU and concatenating DTensor or ordinary shard placements. This can require significant CPU RAM and disk bandwidth.

FSDP merge command:

```bash
python -m verl.model_merger merge \
  --backend fsdp \
  --local_dir CHECKPOINT_STEP_ROLE_DIR \
  --target_dir MERGED_HF_DIR
```

Useful validation command after merge:

```bash
python -m verl.model_merger test \
  --backend fsdp \
  --local_dir CHECKPOINT_STEP_ROLE_DIR \
  --test_hf_dir MERGED_HF_DIR
```

The `test` operation compares against a reference HF directory; do not run it unless the environment can load the model.

## Megatron role layout

Current Megatron layout schema stores role contents under typed subdirectories:

```text
actor/
  checkpoint_contents_metadata.json
  transformer_config.json
  model/
    huggingface/
    dist_ckpt/
  optimizer/
    dist_ckpt/
  extra/
    dist_ckpt/
```

The metadata manifest is important. It includes the global step, backend flags, and a `contents` map whose entries have relative `path` fields. Its presence also indicates a completed save. Use it before guessing which subtree is authoritative.

Megatron backend flags are independent:

- `use_mbridge=True` builds a bridge that can save HF weights under `model/huggingface`.
- `use_dist_checkpointing=True` writes Megatron dist-checkpoint model shards under `model/dist_ckpt`.
- Both can be true to save resume-friendly Megatron shards and an HF export in one checkpoint.
- `use_dist_checkpointing=False` can make `model` and `hf_model` both refer to the same HF tree when mbridge is active.

Common save patterns:

- HF-only export: `save_contents=['hf_model']` with mbridge available.
- Pure Megatron sharded model: `use_mbridge=False`, `use_dist_checkpointing=True`, and `save_contents=['model', ...]`; later merge to HF.
- Hybrid resume plus export: `use_mbridge=True`, `use_dist_checkpointing=True`, and `save_contents=['model', 'hf_model', 'optimizer', 'extra']`.

Megatron merge command:

```bash
python -m verl.model_merger merge \
  --backend megatron \
  --local_dir CHECKPOINT_STEP_ROLE_DIR \
  --target_dir MERGED_HF_DIR
```

Add these flags when applicable:

- `--tie-word-embedding`: for Megatron models whose HF output should tie input/output embeddings.
- `--is-value-model`: for value-model checkpoints.
- `--trust-remote-code`: only when the model architecture requires custom Transformers code and the source is trusted.
- `--use_cpu_initialization`: for large models that cannot initialize on GPU.

For very large Megatron checkpoints, use distributed launch:

```bash
torchrun --nproc_per_node 1 --nnodes NUM_NODES --node_rank NODE_RANK \
  -m verl.model_merger merge \
  --backend megatron \
  --local_dir CHECKPOINT_STEP_ROLE_DIR \
  --target_dir MERGED_HF_DIR
```

## Older Megatron layouts

Older checkpoints may have a flatter layout without current `model/huggingface` and `model/dist_ckpt` subtrees. Current verl includes a Megatron checkpoint-layout migration utility in its source tree, but this skill intentionally does not bundle or wrap it because it mutates checkpoint directories. For production checkpoints, inspect the current repository implementation, back up the checkpoint, and get explicit user approval before running any layout migration.

## HuggingFace to Megatron and random model helper scripts

The repository contains source utilities for HF-to-Megatron conversion, Megatron LoRA merge, random-model initialization, and legacy checkpoint merging. Treat these as reference-only operational tools because they create or mutate large tensor checkpoint trees. Do not wrap them in a public skill unless the exact environment, model family, and desired output layout are known.

## LoRA merge/export notes

verl has explicit LoRA checkpoint handling:

- FSDP checkpoint manager can write `lora_train_meta.json` with LoRA rank/alpha/task metadata.
- FSDP LoRA utilities include a `merged_lora_context` that temporarily merges adapters and restores training state afterward.
- `collect_merged_lora_params` returns HF-format merged weights while filtering LoRA keys, FSDP wrapper prefixes, and flat parameters.
- Tests assert that LoRA layers are unmerged after collection and that repeated calls are stable.

When the user has “saved only sharded model and wants HF export”:

1. Identify backend and role directory using the inspector.
2. For FSDP, require `fsdp_config.json` and model rank shards; run `verl.model_merger merge --backend fsdp`.
3. For Megatron, require current layout metadata or migrated layout; if only `model/dist_ckpt` exists, run `verl.model_merger merge --backend megatron` with model-specific flags.
4. If LoRA was used, check for adapter metadata and whether the requested output should be base-only, adapter-only, or base-plus-merged adapter. Do not assume a sharded training checkpoint already contains a deployable merged HF model.

## Checkpoint retention and latest tracking

verl tracks the latest checkpoint in `latest_checkpointed_iteration.txt` at the run root. Checkpoint cleanup is designed to avoid deleting the only existing checkpoint before a new save succeeds:

- `max_ckpt_to_keep=0` keeps all checkpoints.
- `max_ckpt_to_keep=1` keeps the old checkpoint until the new save has completed and registered.
- `max_ckpt_to_keep>=2` may remove older checkpoints before save while preserving a safety buffer.

If latest tracking points to a missing step directory, inspect surviving `global_step_*` directories and update recovery instructions carefully rather than blindly editing the tracker.
