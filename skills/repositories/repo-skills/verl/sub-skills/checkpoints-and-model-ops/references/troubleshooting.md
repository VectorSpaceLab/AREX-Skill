# Troubleshooting checkpoint and model operations

Use this reference for practical diagnosis after a user reports a failing resume, merge/export, LoRA export, checkpoint retention surprise, or profiling/performance issue.

## First checks

Run the bundled inspector first:

```bash
python sub-skills/checkpoints-and-model-ops/scripts/inspect_checkpoint_path.py CHECKPOINT_DIR --pretty
```

Then verify:

- Is the supplied path a run root, step root, role directory, or HF export tree?
- Which backend is likely: FSDP, Megatron, HF-only, or unknown?
- Does the latest tracker point to an existing step directory?
- Does the role directory contain tokenizer/config files needed for HF export?
- Does a Megatron role directory have `checkpoint_contents_metadata.json`?

## Symptom: “model_merger cannot find config”

Likely causes:

- `--local_dir` points at the run root or step root instead of the role directory.
- FSDP role lacks `huggingface/config.json` or associated tokenizer/config artifacts.
- Megatron current layout expects HF config at `model/huggingface`, not top-level `huggingface`.
- Older Megatron layout has not been migrated.

Actions:

1. Point `--local_dir` to `global_step_N/actor` or the specific role being exported.
2. For FSDP, check for `fsdp_config.json` and `huggingface/config.json`.
3. For Megatron, check `checkpoint_contents_metadata.json` and `model/huggingface/config.json`.
4. If Megatron has old flat paths, migrate a backup with the repository migration script before merging.

## Symptom: “saved only sharded model and wants HF export”

Backend-specific plan:

- **FSDP**: require rank shard files and `fsdp_config.json`; run `python -m verl.model_merger merge --backend fsdp --local_dir ROLE_DIR --target_dir TARGET_DIR`.
- **Megatron with `model/dist_ckpt`**: use `python -m verl.model_merger merge --backend megatron --local_dir ROLE_DIR --target_dir TARGET_DIR`, adding `--tie-word-embedding`, `--is-value-model`, `--trust-remote-code`, or `--use_cpu_initialization` only when justified.
- **Megatron HF-only**: if `model/huggingface` is complete, do not re-merge dist shards unless the user needs a fresh conversion.
- **LoRA**: confirm whether the output should include merged adapter weights. Sharded training checkpoints and adapter metadata alone are not a guarantee of base-plus-LoRA HF output.

## Symptom: Megatron `hf_model` save fails or is missing

Facts to check:

- Megatron `hf_model` requires an active bridge/mbridge object; dist-checkpointing alone is not enough.
- `use_mbridge` and `use_dist_checkpointing` are independent.
- With both enabled and `save_contents` including `model` and `hf_model`, the checkpoint can contain both `model/dist_ckpt` and `model/huggingface`.
- With dist-checkpoint only and no bridge, `hf_model` should be considered unsupported.

Suggested fix:

- If deployable HF export is required during training, configure mbridge and include `hf_model` in save contents.
- If only dist shards exist, use the Megatron model merger after training.

## Symptom: resume picks wrong or missing step

Checks:

- Inspect `latest_checkpointed_iteration.txt` at the run root.
- Confirm the referenced `global_step_N` or `global_steps_N` directory exists.
- Confirm the requested `resume_from_path` includes a specific global-step directory when required.
- For dataloader resume, check for per-DP `data_<rank>.pt` files if the training path expects them.

Do not delete or rewrite checkpoint directories as a first response. Provide a recovery plan and ask before mutating production checkpoint state.

## Symptom: unexpected old-checkpoint deletion

Facts:

- `max_ckpt_to_keep=0` means unlimited retention.
- `max_ckpt_to_keep=1` should keep the previous checkpoint until the new checkpoint successfully registers.
- With values greater than one, older checkpoints may be removed before or after a successful save to maintain capacity.

Actions:

- Inspect surviving directories and tracker file.
- Check whether the failed save happened before registration.
- Avoid manually pruning until the latest valid checkpoint is confirmed.

## Symptom: FSDP merge OOM or very slow

Causes:

- FSDP merger loads per-rank shards on CPU and reconstructs full tensors.
- Large world sizes and large models can require high CPU RAM and I/O.
- Target filesystem throughput can dominate merge time.

Mitigations:

- Merge on a node with sufficient CPU RAM and local scratch space.
- Ensure the target directory has enough free space for a full HF model plus temporary files.
- If the checkpoint already contains a complete `huggingface` export, use that instead of re-merging.
- Avoid running profiling and large merges on the same constrained node.

## Symptom: Megatron merge errors around architecture or tied embeddings

Checklist:

- Confirm HF config exists under `model/huggingface` for current-layout checkpoints.
- Add `--tie-word-embedding` only for models that require tied embeddings in HF output.
- Add `--is-value-model` for value-model checkpoints.
- Add `--trust-remote-code` only when the model family requires custom Transformers code and the code source is trusted.
- For very large models, use distributed `torchrun` merge or `--use_cpu_initialization` when appropriate.

## Symptom: LoRA output has adapter keys or FSDP wrapper artifacts

Known desired behavior from verl tests:

- Merged LoRA HF params should not contain `lora_` keys.
- FSDP wrapper prefixes such as `_fsdp_wrapped_module` should be stripped.
- FSDP flat parameters should not leak into HF-format merged output.
- LoRA layers should be unmerged after extraction so training state is restored.

If these invariants fail, inspect the FSDP LoRA merge utilities before adding ad-hoc key rewrites.

## Symptom: profiler produces too much data or slows run severely

Fixes:

- Use `global_profiler.steps: [single_step]` first.
- Profile only one or a few ranks with `all_ranks: False` and `ranks: [...]`.
- Drop expensive PyTorch profiler contents such as `memory`, `shapes`, and `stack` unless they are needed.
- For Agent Loop rollout, keep discrete mode on and profile a narrow token window when possible.
- Keep Nsight reports on local node storage unless central collection is required.

## Symptom: rollout throughput is low

Checklist:

- Enable rollout stats logging.
- Tune `gpu_memory_utilization` conservatively first.
- Increase `max_num_seqs` or `max_num_batched_tokens` when KV/cache utilization is low.
- Revisit rollout tensor parallel size; smaller TP can increase replica count but consumes more KV cache.
- Use dynamic batch sizing and token limits for training-side bottlenecks, not as a substitute for rollout-engine tuning.

## Hard synthetic usability cases

Use these when verifying this sub-skill without large tensors:

1. **Ambiguous step path**: Given a directory tree with `global_step_1/actor/fsdp_config.json`, rank shard filenames, and `latest_checkpointed_iteration.txt`, identify that the backend is FSDP, `--local_dir` should be the actor directory, and HF export requires `verl.model_merger merge --backend fsdp` unless `huggingface/` is already complete.
2. **Megatron shards only**: Given `global_step_20/actor/checkpoint_contents_metadata.json` showing `model/dist_ckpt` but no HF weight files under `model/huggingface`, recommend Megatron merge for HF export and explain why `hf_model` was not saved during training unless bridge/mbridge was enabled.
