---
name: model-management
description: "Manage InvokeAI model taxonomy, records, install/load/cache
  diagnostics, LoRA/GGUF format triage, and safe metadata checks without full
  generation runs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Model Management

Use this sub-skill when the task involves InvokeAI model identity, registration, installation, search, deletion semantics, loading/cache behavior, model metadata diagnostics, LoRA or quantized format triage, or external provider model records.

## Read First

- For model enum values, config tags, and identification rules, read [model taxonomy](references/model-taxonomy.md).
- For model records, install/import/register/delete/search semantics, read [model install and records](references/model-install-records.md).
- For load, RAM/VRAM cache, CPU-only, FP8, and picklescan behavior, read [model loading and cache](references/model-loading-and-cache.md).
- For LoRA, ControlLoRA, GGUF, and bitsandbytes quantized formats, read [LoRA and quantization](references/lora-and-quantization.md).
- For error triage and safe diagnostic order, read [troubleshooting](references/troubleshooting.md).

## Safe Helper Scripts

- Run `python scripts/summarize_model_taxonomy.py --json` to print bundled taxonomy values without importing InvokeAI.
- Run `python scripts/summarize_model_taxonomy.py --live --configs` only when InvokeAI is importable and you need live enum/config tags.
- Run `python scripts/classify_model_metadata.py <metadata.json|metadata.yaml|model_index.json|config.json>` to classify safe metadata/config files without loading weights.
- Run `python scripts/inspect_model_file.py <model-file-or-dir>` for size, extension, safetensors header metadata, GGUF header hints, and pickle-risk warnings.

## Routing Boundaries

- Stay here for taxonomy, config records, model install/register/import/search/delete semantics, missing-file diagnostics, loader/cache behavior, LoRA format mismatch, GGUF/quantized model triage, and external provider model-record issues.
- Route model loader invocation field authoring to [workflow nodes](../workflow-nodes/SKILL.md).
- Route default workflows or queue behavior involving model nodes to [workflows and queues](../workflows-queues/SKILL.md).
- Route server config, root/model/cache path settings, device selection, RAM/VRAM limits, and external provider API key/base URL setup to [operations config](../operations-config/SKILL.md).

## Safety Rules

- Do not delete model files, unregister records, clear caches, or run destructive cleanup unless the user explicitly authorizes the exact action.
- Prefer metadata/config inspection before any operation that loads weights; never load pickle-based `.ckpt`, `.pt`, `.pth`, or `.bin` files just to identify a model unless the user accepts the risk.
- Treat full generation, regression image comparisons, downloads, conversions, and GPU-heavy smoke runs as out of scope unless explicitly authorized.
- Distinguish `unregister` from `delete`: unregister removes only the database record; delete may remove files managed under InvokeAI's models directory; unconditional deletion is a stronger destructive operation.