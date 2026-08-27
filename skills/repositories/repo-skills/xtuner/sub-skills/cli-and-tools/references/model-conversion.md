# Legacy XTuner model conversion reference

The generated skill does not bundle XTuner's converter implementations. Treat the commands below as reference plans and run them only in an environment that contains the legacy XTuner tools, compatible PyTorch/HuggingFace dependencies, and the required local model/checkpoint assets.

## Converter decision table

| Goal | Legacy command shape | Required inputs | Outputs |
|---|---|---|---|
| Convert legacy `.pth` checkpoint to HuggingFace format | `xtuner convert pth_to_hf CONFIG PTH_MODEL SAVE_DIR [--fp32] [--max-shard-size SIZE] [--safe-serialization] [--save-format xtuner|official|huggingface] [--cfg-options KEY=VALUE ...]` | Legacy config name or config file, `.pth` model checkpoint path, output directory. | HuggingFace-style save directory plus a copy of the legacy config as `xtuner_config.py`. |
| Merge PEFT adapter into a base LLM | `xtuner convert merge LLM ADAPTER SAVE_DIR [--max-shard-size SIZE] [--safe-serialization] [--device cuda|cpu|npu|auto]` | Base LLM path or snapshot id, PEFT adapter path, output directory. | Merged model weights and tokenizer/processor files. |
| Merge visual encoder adapter into a CLIP model | `xtuner convert merge CLIP ADAPTER SAVE_DIR --is-clip [--safe-serialization] [--device cuda|cpu|npu|auto]` | CLIP/visual-encoder snapshot path, visual adapter path, output directory, explicit `--is-clip`. | Merged CLIP weights and image processor files. |
| Split a HuggingFace `.bin` sharded model into smallest tensor shards | `xtuner convert split SRC_DIR DST_DIR` | Source HF directory containing `pytorch_model.bin.index.json` and referenced `.bin` shards. | Destination HF directory with one tensor per shard and copied non-weight files. |

## `pth_to_hf` planning checklist

Use this when the input is an XTuner legacy training checkpoint, not a PEFT adapter directory.

1. Confirm `CONFIG` is either a real config file or a legacy config name resolvable in that environment.
2. Confirm `PTH_MODEL` points to the checkpoint file expected by the legacy config.
3. Confirm enough CPU/GPU memory to build the model and load state dicts.
4. Decide precision and sharding:
   - default saves LLM weights in fp16;
   - `--fp32` keeps fp32;
   - `--max-shard-size 2GB` is the default sharding limit for LLM saves;
   - `--safe-serialization` requests safetensors-style saving where supported.
5. For LLaVA-style models, choose `--save-format xtuner`, `official`, or `huggingface`.
6. Use `--cfg-options` only for explicit, reviewable overrides such as model paths; quote nested/list values carefully.

Common failure modes:

- Config name is not present in the installed config map. Use `scripts/find_legacy_configs.py` against an explicit config root and pass a copied config file instead.
- Checkpoint keys do not match the config's model graph.
- QLoRA or quantized configs may not support meta initialization and may require more memory.
- Required packages such as `accelerate`, `mmengine`, model-specific remote-code modules, or file backends are missing.
- Remote/private storage paths need credentials; avoid passing secrets unless the user explicitly scopes credential handling.

## `merge` planning checklist

Use this when the input is a PEFT adapter that must be merged into a base model or visual encoder.

Required pieces:

- **Base path (`LLM` or `CLIP`)**: a local HuggingFace snapshot directory or a resolvable model id containing the base config and weights.
- **Adapter path (`ADAPTER`)**: a PEFT adapter directory that matches the base model architecture and target modules.
- **Save path (`SAVE_DIR`)**: an empty or intended output directory for merged weights and tokenizer/processor files.
- **Optional `--is-clip`**: required when the adapter is for the CLIP visual encoder instead of the LLM.

Why the difficult merge case needs all of these:

- The adapter stores deltas, not a complete model, so the base LLM/CLIP snapshot is needed to materialize full weights.
- The adapter path identifies the trained low-rank weights and PEFT metadata to load.
- The save path prevents accidental in-place modification and is where the merged model is written.
- `--is-clip` switches from causal-LM/tokenizer loading to CLIP vision/image-processor loading; using the wrong mode gives architecture or processor errors.

Useful options:

- `--device cuda|cpu|npu|auto`: select where the model is loaded. CPU may be safer but slow and memory-heavy; GPU/NPU needs adequate accelerator memory.
- `--max-shard-size SIZE`: shard large LLM outputs.
- `--safe-serialization`: save in a safer serialization format where supported.

Common failure modes:

- Adapter/base mismatch: hidden size, tokenizer, model family, target modules, or CLIP-vs-LLM mode do not match.
- Adapter directory is actually a merged model, or lacks PEFT metadata/weights.
- Base path is a checkpoint file rather than a HuggingFace snapshot directory.
- Offline environment cannot resolve model ids; pre-download snapshots and pass local paths.
- `trust_remote_code`-style model loading may execute model code from the snapshot; review untrusted snapshots before use.
- Insufficient memory during `merge_and_unload` or save.

## `split` planning checklist

Use this only for old HuggingFace `.bin` sharded models. The legacy splitter expects:

- `SRC_DIR/pytorch_model.bin.index.json`;
- all `.bin` shard files referenced by the index;
- enough memory to load each shard in turn;
- a destination directory where copied metadata/config/tokenizer files and new one-tensor shards can be written.

Do not use it for safetensors-only models unless the environment provides a compatible converter. If the source model has a single unindexed weight file, this legacy splitter is the wrong tool.

## Execution policy

- Prefer producing an execution plan and validation checklist over running converters automatically.
- Before execution, record the exact input paths, output path, device, precision, sharding option, and whether network access is allowed.
- Run with local paths where possible; avoid implicit downloads for large models and benchmark assets.
- After conversion, verify expected output files exist before deleting checkpoints or adapters.
