# Troubleshooting Model Management

Use this page for safe, non-destructive diagnosis. Start with records, metadata, and config before loading weights, downloading models, clearing caches, or deleting files.

## Quick Triage

| Symptom | Safe first checks | Avoid until authorized |
| --- | --- | --- |
| Model listed but cannot load | Check record `path`, missing-model listing, taxonomy fields, and whether the file exists. | Deleting/reinstalling the model. |
| Import returns unknown config | Inspect extension, root config files, safetensors metadata, and safe state-dict keys. | Loading pickle checkpoints or forcing class overrides. |
| Wrong model family/type | Check stale `base`, `type`, `format`, `variant`, `config_path`, and class-change update behavior. | Manually editing persisted records without validation. |
| Duplicate model error | Compare `key`, path uniqueness, and name/base/type uniqueness. | Removing the existing record without confirming intent. |
| Hash lookup mismatch | Confirm hashing algorithm, source file, and whether the model was moved/replaced. | Assuming equal names imply equal weights. |
| Missing model files | Decide whether to restore the file, update path, reidentify, or unregister only. | Bulk delete or unconditional deletion. |
| External model unavailable | Check provider id/model id, provider status, API key/base URL config, and capability matrix. | Retrying large paid requests repeatedly. |
| Cache/VRAM pressure | Inspect cache stats, device config, CPU-only settings, FP8 settings, partial loading, and RAM/VRAM limits. | Full generation stress tests. |
| LoRA does nothing or crashes | Match LoRA family/format/base/variant and confirm it is patched into a compatible base model. | Treating a LoRA file as a main model. |
| GGUF/quantized load fails | Check format support, optional dependencies, tensor type, backend, and config family. | Converting or downloading replacement weights. |

## Path and Source Problems

- Relative model paths are resolved under the configured models directory; absolute paths may represent registered-in-place models.
- A record path can be valid syntactically but stale if the underlying file moved externally.
- Missing-model scans intentionally report records without deleting them.
- Orphan scans report files under model storage that are not registered; registering/deleting orphans is a mutation.
- HF repo ids can be confused with local paths when the local path does not exist; confirm source type before import.

## Unknown or Invalid Configs

- Unknown fallback means no concrete config class matched, not necessarily that the file is corrupt.
- Invalid config errors often come from stale override fields or fields that are legal on one config class but illegal on another.
- Diffusers directories should usually expose `model_index.json` or component `config.json` files at the intended root.
- Single-file checkpoints depend on extension, state-dict keys, tensor shapes, and sometimes override hints such as base, variant, prediction type, or config path.
- External API model configs are never probed from disk.

## Pickle and Metadata Safety

- Prefer safetensors header inspection and JSON/YAML config parsing.
- Treat `.ckpt`, `.pt`, `.pth`, and `.bin` as potentially unsafe for diagnostic loading.
- Picklescan failures should block loading unless the user explicitly accepts the unsafe override already configured.
- Do not disable picklescan as a routine workaround.

## Backend and Hardware Issues

- CUDA-only features fail on CPU/MPS; MPS and CPU use different cache movement behavior.
- bitsandbytes quantization requires optional dependency and hardware compatibility.
- GGUF support requires the GGUF package and only supports operations implemented by the tensor wrapper.
- Diffusers/transformers/ONNX paths require their optional packages and compatible model schemas.
- FP8 storage is CUDA-only and deliberately skipped for several model/submodel types.
- CPU-only text encoder settings can reduce VRAM but surprise users expecting all components on GPU.

## Delete and Cleanup Safety

Use precise language with users:

- `unregister`: remove the database record; do not delete files.
- `delete`: remove the record and delete files only when InvokeAI considers them managed model files.
- `unconditionally_delete`: remove record and files without the managed-file safeguard.
- `empty_model_cache`: clear cached in-memory models; it does not remove model records or weights, but can interrupt active workflows if misused.
- Orphan cleanup and missing-model bulk actions are destructive or record-mutating and need explicit confirmation.

## When to Escalate Beyond Metadata

Ask for explicit user permission before:

- Loading large model weights just to classify a model.
- Loading pickle-based checkpoints.
- Running a full generation or regression script.
- Downloading from HF/URL sources.
- Converting quantized formats or writing new weight files.
- Clearing caches on an active server.
- Deleting, unregistering, or bulk-modifying model records.