# Checkpoint export troubleshooting

Use this guide when the inspector, merger, or post-export validation fails. The actor checkpoint directory should be the `actor/` directory under a `global_step_<N>/` checkpoint.

## Preflight failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `No model shard files matched model_world_size_<N>_rank_<R>.pt` | The path points at the save root, a `global_step_<N>` parent, the `huggingface/` child, or an incomplete copy. | Repoint to `global_step_<N>/actor`. If the checkpoint was copied, copy the model shard `.pt` files too. |
| `rank 0 is missing` | The merger starts from rank 0 to infer world size and DTensor layout. | Restore `model_world_size_<W>_rank_0.pt` from the original checkpoint. Without rank 0, export cannot proceed. |
| `missing ranks` or `non-contiguous ranks` | Some `model_world_size_<W>_rank_<R>.pt` files are absent or renamed. | Restore all ranks `0..W-1` for a full EasyR1 actor checkpoint. Do not rename shards manually. |
| `multiple model world_size groups` | Files from different training runs or world sizes were mixed into one actor directory. | Separate the checkpoint directories and export only one world-size group at a time. |
| `actor directory itself is named huggingface` | The output metadata folder was passed instead of the actor directory. | Pass its parent actor directory. The merger writes output into the existing `huggingface/` child. |
| `huggingface/config.json missing` | Rank 0 did not save model metadata, or the metadata folder was not copied with the checkpoint. | Restore `actor/huggingface/config.json`; model shards alone are not enough to choose the correct Transformers auto class. |
| `generation_config.json is invalid JSON` | Metadata file is truncated or manually edited. | Restore it from the checkpoint, or remove it only if default generation settings are acceptable. |
| `LoRA adapter_config.json missing base_model_name_or_path` | LoRA export requires the base model id/path so the adapter can be merged into dense weights. | Edit or regenerate the adapter config with the correct base model reference, then ensure that model is available locally or from the Hub. |

## Merger runtime failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `No model file with the proper format` | No rank-0 shard matched the expected filename. | Run the inspector and fix the actor path or shard names before retrying. |
| `Unsupported mesh_dim_names` | The checkpoint was saved with a distributed layout other than plain FSDP or DDP+FSDP. | Use an EasyR1-supported FSDP export checkpoint, or write a custom merger for the actual mesh. |
| `FSDP + TP is not supported yet` | The loaded DTensor mesh includes tensor-parallel dimensions. | Re-save/export without TP if possible, or implement a TP-aware merge that understands the tensor layout. |
| `Partial placement is not supported yet` | A DTensor parameter uses partial placement, which the merger cannot reduce. | Use a checkpoint layout with shard or replicate placements, or extend the merger to reduce partial tensors correctly. |
| `Cannot find key ... in rank ...` followed by merge errors | Shards are inconsistent or not from the same global step/world size. | Recopy a complete actor directory from one checkpoint step; do not mix shards from multiple steps. |
| Unknown or unsupported architecture | `config.json` does not have an `architectures[0]` containing `ForCausalLM`, `ForConditionalGeneration`, or `ForTokenClassification`. | Confirm the model family. For unsupported Transformers classes, adapt the auto-class selection before merging. |
| Out-of-memory during CPU merge | The merger loads checkpoint shards and, for LoRA, the base model on CPU. | Move to a machine with more RAM, reduce concurrent memory pressure, or export a smaller checkpoint. CPU merge does not mean low-memory merge. |
| LoRA base model download/auth error | `base_model_name_or_path` points to a gated, private, unavailable, or network-only model. | Configure the required Hugging Face token, use a local base model path, or set an approved mirror endpoint before retrying. |
| PEFT/LoRA config field error | The adapter config contains fields from a different PEFT version or incompatible LoRA setup. | Use a PEFT version compatible with the checkpoint, or normalize the adapter config fields to the installed PEFT schema. |

## Generation config problems

EasyR1's merger intentionally preserves an existing `huggingface/generation_config.json`. If decoding settings changed after export:

1. Compare the pre-export and post-export `generation_config.json` files.
2. Confirm the merger used the preservation helper rather than a raw `save_pretrained()` call.
3. Check list-valued fields such as `eos_token_id`; they should not collapse to scalar defaults from `config.json`.
4. If the file was absent before export, Transformers may generate one from model defaults; that is expected and is not proof of a checkpoint-specific generation config.

## LoRA edge cases

- `lora_adapter/adapter_config.json` is the signal that the merger should perform a dense LoRA merge.
- `base_model_name_or_path` is required. Without it, the merger cannot load the base model and must fail.
- `adapter_model.safetensors` is commonly saved for adapter reuse, but the EasyR1 dense merge path primarily relies on the model checkpoint state dict plus adapter config.
- Multimodal LoRA models may require excluding visual modules during training for downstream vLLM compatibility. Export can still produce weights, but serving compatibility depends on the target inference stack.
- If the desired output is adapter-only, do not use the dense merge path as the final artifact; preserve the `lora_adapter/` folder separately.

## Upload failures and safety checks

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Hugging Face authentication error | No token or insufficient permissions. | Authenticate with an approved token before retrying upload. |
| Network timeout or connection error | Hub access is blocked or slow. | Retry later, use an approved mirror endpoint, or skip upload and keep the local `huggingface/` output. |
| Repository visibility surprise | The distilled EasyR1 upload behavior creates the repository with `private=False`. | Do not use the built-in upload path for private models; create/configure the Hub repo separately and upload with explicit privacy settings. |
| Upload includes stale files | The output folder already existed from a previous merge. | Inspect or clean the `huggingface/` output before uploading if stale files are possible. |

## Checkpoint tracker pitfalls

- `checkpoint_tracker.json` lives in the save root, not in the actor directory.
- `last_global_step` is portable; reconstruct `global_step_<last_global_step>/actor` from it.
- `last_actor_path` can become stale after moving checkpoints because it records the path at save time.
- Retention via `save_limit` can remove older checkpoint directories; absence of old steps is not necessarily an error.
- If `find_last_checkpoint` fails because the tracked step directory is gone, choose an existing `global_step_<N>` directory manually.

## Backend limitation reminders

- The inspector is CPU-safe and metadata-only; it does not prove the model shards are loadable by PyTorch.
- Native CPU tests can validate checkpoint tracker helpers and generation-config preservation, but they do not prove full EasyR1 training.
- Full training and checkpoint creation need CUDA plus flash-attn, vLLM, Ray, and the full EasyR1 runtime stack.
- Merge/export may run on CPU, but large checkpoints still require substantial RAM and model-family dependencies.

## Fast diagnostic order

1. Run [the inspector](../scripts/easyr1_checkpoint_inspector.py) on the actor directory.
2. Fix file layout, rank continuity, and metadata JSON errors first.
3. For LoRA, verify `base_model_name_or_path` and base-model access before loading shards.
4. Run the merger only after preflight passes.
5. Validate `huggingface/config.json`, `generation_config.json`, and output weight files before any upload.
