# Model Export Troubleshooting

Start with static preflight, then move to model-loading or conversion only when the paths, format choice, tokenizer files, and credentials are coherent.

## Quick diagnosis matrix

| Symptom | Likely cause | What to check | Fix |
| --- | --- | --- | --- |
| `No checkpoints found` from CLI | Outputs directory is wrong or run lacks `config.json`/`adapter_config.json` | Run `unsloth list-checkpoints --outputs-dir ...`; inspect for `checkpoint-*` directories | Point to the actual training output root or the specific checkpoint directory. |
| `No model loaded. Please select a checkpoint first.` | Studio export called before `load_checkpoint` or export subprocess died | Studio `/status`, export logs, CLI output after `Loading checkpoint` | Load checkpoint again; fix load error before export. |
| `This is not a PEFT model` for merged/lora export | User selected adapter-only or merged-PEFT path for a full/base model | `adapter_config.json`, Studio `is_peft` field | Use base-model export/direct `save_pretrained`, or select a LoRA checkpoint. |
| `This is a PEFT model. Use 'Merged Model' export type instead.` | User selected base export for a LoRA adapter | `adapter_config.json`, Studio `is_peft` field | Use merged or LoRA export. |
| Plain `merged_4bit` raises | Unsloth protects against quality loss before later conversions | Save method string | Use `merged_4bit_forced` only as final artifact, otherwise choose `merged_16bit`. |
| GGUF export says tokenizer required | `tokenizer` argument is `None` or files are missing | Python call, checkpoint tokenizer files | Pass the tokenizer object and keep tokenizer files next to local artifacts. |
| GGUF conversion fails after tool setup | llama.cpp converter/quantizer unavailable, drifted, failed to build, or disk is insufficient | Logs around install, converter, quantizer, output file creation | Install/update llama.cpp tooling through Unsloth path, free disk, use a smaller model, or save merged 16-bit first and convert separately. |
| Ollama `Modelfile` missing | Base model has no recognized Ollama template mapping | GGUF output directory, export logs | Use llama.cpp directly or write a manual Modelfile. |
| Hub upload fails with repo/token error | Missing `repo_id`, missing/invalid token, gated base load needs token, or wrong private flag | CLI flags, `HF_TOKEN`, Python `token`, repo id shape | Provide explicit `namespace/name`, pass token for load/upload, choose `private` deliberately. |
| Export path rejected | Empty path, null bytes, CR/LF, `..`, long component, or unsafe read path | Run bundled preflight helper | Use a simple output directory. Remember write paths can be absolute, but read/scan paths are restricted. |
| UnicodeDecodeError on Windows during GGUF/subprocess output | Text-mode subprocess decoded child UTF-8 bytes with a local legacy encoding | Export logs, Windows locale, conversion subprocess | Current Unsloth pins UTF-8 with replacement for text subprocess calls; upgrade if the installed version regressed. |
| Tokenizer EOS changes after save | Tokenizer metadata got reset by merge/save path | `tokenizer_config.json` `eos_token` before/after export | Use current Unsloth patched saving; verify processor-tokenizer wrappers and prefixed tokenizer configs. |
| SentencePiece special tokens break GGUF | `tokenizer.model` or `tokenizer.json` inconsistent or missing | Presence of `tokenizer.model`, `tokenizer.json`, added special tokens | Use current Unsloth GGUF path, which attempts a robust `fix_sentencepiece_gguf`; restore missing tokenizer assets before conversion. |
| Export runs out of memory | Full merge, `safe_serialization`, or shard staging needs more RAM/VRAM than available | Model size, `maximum_memory_usage`, shard size, temporary directory disk | Lower `maximum_memory_usage`, increase disk space, choose LoRA export, reduce model size, or use larger hardware. |

## Missing checkpoint

Local Studio/CLI discovery treats a training run or checkpoint as meaningful when it has `adapter_config.json` or `config.json`. Nested checkpoints are usually named `checkpoint-N` and may include `trainer_state.json` for loss display.

Checklist:

- Confirm the path exists and is a directory.
- For a LoRA adapter, look for `adapter_config.json` and adapter weights such as `adapter_model.safetensors`.
- For a merged/base model, look for `config.json` and `.safetensors` or `.bin` weight files.
- For a GGUF artifact, look for `.gguf` files; use runtime loading/inference skills instead of export if it is already converted.
- If only the parent outputs root is known, run `unsloth list-checkpoints --outputs-dir OUTPUTS_ROOT`.

## Wrong format selection

Use this routing:

- `lora`: user wants adapter-only artifacts, smallest output, or future merge/resume.
- `merged-16bit` / `merged_16bit`: user wants full weights or a source for later conversion.
- `merged-4bit` CLI or `merged_4bit_forced` Python: user wants final compact bitsandbytes output and accepts quality/compatibility tradeoffs.
- `gguf`: user wants llama.cpp/Ollama/GGUF runtime artifacts.
- Base export/direct `save_pretrained`: source is already a non-PEFT full model.

When the user asks for both merged and GGUF, create separate output directories. Do not overwrite a merged directory with GGUF intermediates.

## Path and shell safety

Unsloth’s save and export paths are designed to avoid command injection and unsafe traversal:

- The Studio save-directory schema rejects null bytes, CR/LF, `..`, and path components over 255 characters.
- Export write paths may be external absolute paths; read/scan paths are contained under configured roots.
- GGML/GGUF subprocess calls should pass argv lists and avoid `shell=True` for user-controlled paths.
- Text-mode subprocess calls should pin `encoding="utf-8"` and `errors="replace"` so non-ASCII converter output does not crash on Windows.

If a user reports path-related failure, run the bundled helper and simplify the output path before attempting conversion.

## Tokenizer preservation

Tokenizer preservation is not optional for reliable export:

- `tokenizer_config.json` stores EOS and other runtime metadata.
- Processor wrappers may hold the real tokenizer at `.tokenizer`; Unsloth’s patch handles both direct tokenizers and processor tokenizers.
- SentencePiece models may need `tokenizer.model`; Unsloth tries to preserve or recover this file and robustly patch special-token typing before GGUF conversion.
- A missing tokenizer may still allow some adapter saves, but GGUF export should be blocked until the tokenizer is supplied.

When debugging tokenizer issues, compare exported tokenizer files with the source checkpoint and confirm the intended EOS token did not revert to a base default such as `<eos>` when the trained model expects a model-specific turn token.

## Hub upload issues

Before upload:

- Require `repo_id` for CLI/Studio `--push-to-hub`.
- Pass token through `HF_TOKEN`, CLI `--hf-token`, or Python `token`, but do not persist it in reusable files.
- Use `private=True`/`--private` only when the user requests a private repo.
- For gated/private source or base models, use the token during checkpoint load too; otherwise base-model resolution can pass preflight but fail at actual load.
- For GGUF push helpers, expect local conversion before upload; upload failure may leave local temporary artifacts or converted files depending on options.

## Memory, sharding, and temporary files

- `maximum_memory_usage` must be `> 0` and `<= 0.95`; defaults vary by save path.
- `safe_serialization=True` can use more RAM and may be slow on very low-CPU systems; keep it unless there is a concrete reason to change.
- Use `max_shard_size` when downstream hosting or upload needs smaller shards.
- Keep `temporary_location` on a volume with enough free space; constrained environments may need a different temp/output directory.
- If GGUF conversion fails after creating temporary directories, clean only clearly generated temp folders and avoid deleting user-owned checkpoint directories.

## Studio logs and cancellation

Studio export logs are forwarded from the export subprocess and support both SSE and JSON polling. If the browser appears stuck behind a buffering tunnel, use the JSON log endpoint with the cursor. Canceling export terminates only the export worker; it should not stop training or inference subprocesses.

Useful fields from `/status`:

- `is_export_active`: whether load/export/cleanup is still running.
- `active_op_kind`: current operation, such as `load_checkpoint` or `export_gguf`.
- `last_op_status`, `last_op_error`, `last_op_output_path`: final outcome when a request times out or the UI disconnects.
