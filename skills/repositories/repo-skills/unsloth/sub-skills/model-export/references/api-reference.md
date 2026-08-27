# Model Export API Reference

This reference summarizes Unsloth export surfaces for future agents. It is self-contained and avoids depending on the source checkout.

## Python saving surfaces

### Patched model methods

Unsloth patches supported model/tokenizer objects with save helpers during model setup. The most common calls are:

| Goal | Python method | Key arguments | Notes |
| --- | --- | --- | --- |
| Save LoRA adapter | `model.save_pretrained_merged(path, tokenizer, save_method="lora")` or `unsloth.save.unsloth_save_model(..., save_method="lora")` | `safe_serialization`, `max_shard_size`, `push_to_hub`, `token`, `private` | Fastest and smallest. Preserves adapter config and tokenizer assets for later merging/loading. |
| Save merged 16-bit weights | `model.save_pretrained_merged(path, tokenizer, save_method="merged_16bit")` | `maximum_memory_usage`, `temporary_location`, `max_shard_size`, `safe_serialization` | Preferred intermediate for general deployment and GGUF conversion. Requires enough RAM/VRAM and disk. |
| Save merged 4-bit weights | `model.save_pretrained_merged(path, tokenizer, save_method="merged_4bit_forced")` | same as merged save | Unsloth intentionally errors on plain `merged_4bit`; use the forced name only when it is the final intended export because it can reduce quality for later conversions. |
| Save GGUF locally | `model.save_pretrained_gguf(path, tokenizer, quantization_method="q4_k_m")` | `quantization_method`, `first_conversion`, `maximum_memory_usage`, `temporary_location` | Requires tokenizer, prepares/uses llama.cpp conversion tools, writes `.gguf` files and may write an Ollama `Modelfile`. |
| Push GGUF to Hub | `model.push_to_hub_gguf(repo_id, tokenizer, quantization_method="q4_k_m", token=..., private=...)` | `repo_id`, `token`, `private`, `max_shard_size`, `revision` | Converts locally first, uploads `.gguf`, config, Modelfile when present, and README metadata. |

Installed API evidence confirmed `unsloth.save.unsloth_save_model(model, tokenizer, save_directory, save_method="lora", push_to_hub=False, token=None, max_shard_size="5GB", safe_serialization=True, private=None, revision=None, temporary_location="_unsloth_temporary_saved_buffers", maximum_memory_usage=0.9, datasets=None, ...)`.

### `save_method` values

- `lora`: saves adapters/tokenizer only. Use for resuming training, sharing adapters, or delaying merge.
- `merged_16bit`: merges LoRA into FP16/BF16-style full weights. Use before deployment, conversion, or high-compatibility local inference.
- `merged_4bit_forced`: forcibly saves a compact 4-bit merged model. Use only as a final artifact; avoid before GGUF or repeated conversions.
- Plain `merged_4bit` intentionally raises with guidance to use `merged_4bit_forced` if the user accepts the risk.

### GGUF quantization names

Useful public choices include:

| Name | Meaning |
| --- | --- |
| `not_quantized` | Alias for full precision output; large and slow but highest fidelity. |
| `fast_quantized` | Alias for `q8_0`; faster conversion with acceptable size/quality tradeoff. |
| `quantized` | Alias for `q4_k_m`; smaller recommended quantized output. |
| `f16`, `bf16`, `f32` | Full/near-full precision GGUF variants; high disk and memory cost. |
| `q8_0` | 8-bit quantization; good compatibility and quality. |
| `q4_k_m`, `q5_k_m` | Common recommended K-quants. |
| `q2_k_l` | Unsloth preset: q2_k with output/token embedding tensors kept at q8_0 for quality. |
| `q3_k_l`, `q3_k_m`, `q3_k_s`, `q4_0`, `q4_1`, `q4_k_s`, `q5_0`, `q5_1`, `q5_k_s`, `q6_k` | Additional llama.cpp quantization variants supported by Unsloth. |

`iq2*` variants are not supported by the Unsloth GGUF path described here even if some external llama.cpp builds know about them.

## CLI export surface

The installed console entry point is `unsloth = unsloth_cli:app`.

### `unsloth list-checkpoints`

```bash
unsloth list-checkpoints --outputs-dir ./outputs
```

- Scans training runs under the outputs directory.
- A run is discoverable when it contains `adapter_config.json` or `config.json`.
- Nested `checkpoint-*` directories are listed when they contain `adapter_config.json` or `config.json`.
- Loss is read from `trainer_state.json` when available.

### `unsloth export`

```bash
unsloth export CHECKPOINT OUTPUT_DIR --format merged-16bit
unsloth export CHECKPOINT OUTPUT_DIR --format merged-4bit
unsloth export CHECKPOINT OUTPUT_DIR --format lora
unsloth export CHECKPOINT OUTPUT_DIR --format gguf --quantization q4_k_m
```

Key options:

| Option | Values/defaults | Notes |
| --- | --- | --- |
| `--format`, `-f` | `merged-16bit`, `merged-4bit`, `gguf`, `lora`; default `merged-16bit` | Dispatches to Studio export backend methods. |
| `--quantization`, `-q` | CLI advertises `q4_k_m`, `q5_k_m`, `q8_0`, `f16`; default `q4_k_m` | Used only for `--format gguf`; backend lowercases before calling Unsloth. |
| `--push-to-hub` | boolean | Requires `--repo-id`; also needs an HF token. |
| `--repo-id` | `namespace/name` | Required for Hub uploads. |
| `--hf-token` | option or `HF_TOKEN` env var | Do not echo this token in logs or generated files. |
| `--private` | boolean | Creates/uploads private Hub repos where supported. |
| `--max-seq-length` | default `2048` | Used when loading the checkpoint before export. |
| `--load-in-4bit / --no-load-in-4bit` | default `--load-in-4bit` | Controls checkpoint load mode before export. |

CLI export returns a 3-tuple from the backend `(success, message, output_path)`; future wrappers should preserve that contract.

## Studio export backend contracts

Studio export uses a persistent export orchestrator subprocess after checkpoint load. It keeps export workloads separate from training/inference subprocesses and streams stdout/stderr to export logs.

### Checkpoint load

`load_checkpoint(checkpoint_path, max_seq_length=2048, load_in_4bit=True, trust_remote_code=False, hf_token=None)`:

- Loads the checkpoint in a fresh subprocess.
- Detects LoRA/PEFT adapters through `adapter_config.json` and resolves base model metadata.
- Handles text, vision, and several audio model families through the appropriate Unsloth loaders.
- Applies malware and remote-code consent gates for remote/gated models when Studio security is active.
- Returns `(success, message)` and updates backend state (`current_checkpoint`, `is_peft`, `is_vision`).

### Export methods

| Method | Preconditions | Local behavior | Hub behavior |
| --- | --- | --- | --- |
| `export_merged_model(save_directory, format_type="16-bit (FP16)", ...)` | Loaded model and tokenizer; PEFT model required | Resolves export write path, saves `merged_16bit` or forced 4-bit, writes export metadata | Requires `repo_id` and token; pushes merged model and tokenizer. |
| `export_base_model(save_directory, ...)` | Loaded model and tokenizer; non-PEFT model required | Saves model/tokenizer directly or MLX merged path, writes export metadata | Requires local save directory, repo id, and token; uploads folder/model card. |
| `export_gguf(save_directory, quantization_method="Q4_K_M", ...)` | Loaded model and tokenizer | Creates a temporary model subdir, calls `save_pretrained_gguf`, relocates `.gguf` files and `Modelfile` into the requested output dir, writes metadata | Requires `repo_id` and token; calls `push_to_hub_gguf`. |
| `export_lora_adapter(save_directory, ...)` | Loaded PEFT model and tokenizer | Saves adapter plus tokenizer files | Requires `repo_id` and token; pushes adapter/tokenizer. |

### Path contracts

- Save-directory schemas reject empty strings, null bytes, CR/LF, `..` segments, and path components longer than 255 characters.
- Export write paths accept external absolute paths so users can write to another drive or mounted volume.
- Export read/scan paths are stricter and remain contained under configured output/export roots.
- External absolute export output paths may be registered for later Studio scans; contained exports are reported relative to the exports root.

## Output artifact expectations

| Export type | Expected local files |
| --- | --- |
| LoRA adapter | `adapter_config.json`, adapter weights such as `adapter_model.safetensors`, tokenizer files (`tokenizer_config.json`, `tokenizer.json`, `special_tokens_map.json`, and possibly `tokenizer.model`) |
| Merged/base | `config.json`, model weights such as `.safetensors` or `.bin` shards, tokenizer files, optional shard index JSON |
| GGUF | One or more `.gguf` files, optional multimodal companion GGUF files, optional `Modelfile`, `config.json`/metadata copied or generated around the conversion |
| Hub upload | Same logical files uploaded under a model repo; GGUF upload also publishes a README-style model card when using `push_to_hub_gguf` |

Tokenizer preservation is part of the export contract: Unsloth patches tokenizer saving to preserve EOS token metadata and SentencePiece assets when possible. GGUF export should be treated as invalid if the tokenizer is missing.
