# Model Export Workflows

Use these workflows to plan exports without immediately running heavy model loads, merges, conversions, downloads, or uploads.

## Preflight every export

1. Identify the checkpoint directory or remote checkpoint identifier.
2. For local checkpoints, verify the directory exists and has at least one of `adapter_config.json`, `config.json`, model/adaptor weight files, or `.gguf` files.
3. Verify tokenizer assets before any local export that should be reloadable: at minimum expect `tokenizer_config.json` or `tokenizer.json`; SentencePiece models may also need `tokenizer.model`.
4. Validate the output directory string: non-empty, no null/CR/LF characters, no `..` path segments, and no path component over 255 characters.
5. If using Hub, require `repo_id`, token source, and a private/public decision before starting.
6. For GGUF, check the requested quantization name and whether llama.cpp tooling (`llama-quantize`, converter scripts, and optionally `ollama`) is available or installable.

The bundled helper performs these static checks without importing Unsloth or loading a model:

```bash
python scripts/inspect_export_targets.py \
  --checkpoint ./outputs/my-run/checkpoint-100 \
  --output ./exports/my-run-gguf \
  --format gguf \
  --quantization q4_k_m
```

Add `--json` when another script should parse the result.

## Export LoRA adapter only

Choose LoRA export when the user wants the smallest artifact, plans to resume training, wants to share an adapter, or does not yet want to commit to a merged deployment format.

Python pattern:

```python
model.save_pretrained_merged("export-lora", tokenizer=tokenizer, save_method="lora")
```

CLI pattern:

```bash
unsloth export ./outputs/my-run ./exports/my-run-lora --format lora
```

Checklist:

- Confirm the source is a PEFT/LoRA checkpoint (`adapter_config.json` is a strong signal).
- Preserve tokenizer files next to the adapter so later loads do not silently fall back to incompatible base tokenizer metadata.
- For Hub upload, pass `--push-to-hub --repo-id namespace/model --private` only when the user has explicitly chosen those settings.

## Export merged 16-bit weights

Choose merged 16-bit when the user wants a broadly compatible full model, a clean deployment artifact, or an intermediate for GGUF conversion.

Python pattern:

```python
model.save_pretrained_merged("export-merged-fp16", tokenizer=tokenizer, save_method="merged_16bit")
```

CLI pattern:

```bash
unsloth export ./outputs/my-run ./exports/my-run-merged --format merged-16bit
```

Checklist:

- Ensure the checkpoint is a LoRA/PEFT model when using Studio/CLI merged export; non-PEFT models should use base-model export in Studio internals or direct `save_pretrained` style APIs.
- Plan disk space for full weights and possible shards. Keep `max_shard_size` explicit when downstream systems need a shard limit.
- Tune `maximum_memory_usage` conservatively when memory pressure is likely; Unsloth asserts it is greater than 0 and at most 0.95.
- Keep `safe_serialization=True` unless a specific backend requires otherwise.

## Export forced merged 4-bit weights

Choose forced merged 4-bit only as a final compact export. Unsloth deliberately rejects plain `merged_4bit` because later conversions can lose quality.

Python pattern:

```python
model.save_pretrained_merged("export-merged-4bit", tokenizer=tokenizer, save_method="merged_4bit_forced")
```

CLI pattern:

```bash
unsloth export ./outputs/my-run ./exports/my-run-4bit --format merged-4bit
```

Checklist:

- Warn the user not to use this as the source for GGUF or further merge workflows.
- Prefer merged 16-bit if the user is unsure.
- Preserve tokenizer files and config as with other exports.

## Export GGUF

Choose GGUF when the target runtime is llama.cpp, Ollama, local GGUF inference, or another GGUF-compatible runtime.

Python pattern:

```python
model.save_pretrained_gguf("export-gguf", tokenizer=tokenizer, quantization_method="q4_k_m")
```

CLI pattern:

```bash
unsloth export ./outputs/my-run ./exports/my-run-gguf --format gguf --quantization q4_k_m
```

Checklist:

- Require a tokenizer. Unsloth raises for GGUF save without one.
- Prefer `q4_k_m` for compact default deployment, `q8_0` for higher quality with larger files, and `f16`/`bf16` for high-fidelity large artifacts.
- Expect llama.cpp tooling to be checked or installed. This can take minutes and may need build dependencies.
- On WSL, Unsloth patches llama.cpp sudo checks in Studio export to avoid hanging on password prompts.
- Expect `.gguf` files to be relocated into the requested output directory by Studio export; a `Modelfile` may also be moved there.
- For vision/multimodal models, expect companion projection GGUF files and different llama.cpp usage from text-only models.
- Treat real conversion as expensive; do preflight first and run conversion only after the user accepts compute, disk, and time costs.

## Create or use an Ollama Modelfile

Unsloth may create an Ollama `Modelfile` during GGUF export when it recognizes a base model template.

Workflow:

1. Export GGUF locally.
2. Check whether `Modelfile` exists in the GGUF output directory.
3. If present, review the `FROM` path and template for the selected `.gguf` file.
4. Create the Ollama model only when the local Ollama server is intended to be used:

```bash
ollama create model-name -f ./exports/my-run-gguf/Modelfile
```

If no `Modelfile` is produced, explain that Unsloth did not have a template mapping for the base model and the user must create one manually or use llama.cpp directly.

## Push to Hugging Face Hub

Hub upload can be combined with local export through CLI/Studio or called through Python push helpers.

CLI pattern:

```bash
HF_TOKEN=... unsloth export ./outputs/my-run ./exports/my-run-merged \
  --format merged-16bit \
  --push-to-hub \
  --repo-id namespace/model-name \
  --private
```

Python GGUF pattern:

```python
model.push_to_hub_gguf(
    "namespace/model-name-GGUF",
    tokenizer=tokenizer,
    quantization_method="q4_k_m",
    token=hf_token,
    private=True,
)
```

Checklist:

- Do not embed tokens in reusable skill files, shell history examples, logs, issue templates, or generated code comments.
- Validate the repo id shape (`namespace/name`) for shared/team repos; Unsloth can infer username in some Python paths, but explicit repo ids are safer for agents.
- Set `private=True` only when requested. Treat public as a deliberate publishing action.
- For gated/private base models, pass a token for checkpoint load as well as upload so base-resolution and model loading do not fail after security preflight.

## Studio export backend flow

Use this when debugging the backend rather than teaching generic CLI syntax.

1. `POST /load-checkpoint` loads a selected checkpoint into the export subprocess.
2. Poll `GET /status` to inspect `current_checkpoint`, `is_peft`, `is_vision`, `is_export_active`, active/last op fields, and last output path/error.
3. Start one export endpoint: `/export/merged`, `/export/base`, `/export/gguf`, or `/export/lora`.
4. Stream `GET /logs/stream` or poll `GET /logs` with the returned cursor for live output.
5. Use `/cancel` to terminate an in-flight export subprocess without stopping training/inference subprocesses.
6. Use `/cleanup` to unload export memory.

Studio accepts absolute export write destinations for users who need a different drive, but read/scan endpoints stay rooted in configured safe roots. Do not confuse an allowed write path with permission to scan arbitrary local directories.

## Planning cases

### LoRA to merged 16-bit and GGUF with preflight only

- Run the helper once for `--format merged-16bit` and again for `--format gguf --quantization q4_k_m` using separate output directories.
- Confirm the checkpoint has adapter metadata and tokenizer files.
- Present the exact Python or CLI commands but mark the merge/GGUF conversion as expensive and wait for explicit approval before running.
- If the helper reports missing tokenizer assets, fix or locate the tokenizer before GGUF conversion.

### Unsafe path characters and missing tokenizer files

- Run the helper and inspect errors for null bytes, CR/LF, `..`, or very long path components.
- Replace unsafe output paths with a simple directory name under a known exports folder.
- Inspect checkpoint warnings for missing `tokenizer_config.json`, `tokenizer.json`, `special_tokens_map.json`, or `tokenizer.model`.
- For GGUF, block execution until tokenizer files are restored or a compatible tokenizer is intentionally supplied in Python.
