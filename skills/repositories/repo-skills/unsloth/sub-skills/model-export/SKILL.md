---
name: model-export
description: "Save and export Unsloth checkpoints as LoRA adapters, merged
  weights, GGUF files, Ollama Modelfiles, or Hugging Face Hub artifacts with
  safe path and tokenizer preflights."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Model Export

Use this sub-skill when the user needs to save or export an already trained Unsloth checkpoint: LoRA adapters, merged 16-bit weights, forced merged 4-bit weights, GGUF quantizations, Ollama Modelfiles, or Hub uploads.

## Route first

- Route training setup, loading base models, LoRA configuration, and trainer code to [core-training](../core-training/SKILL.md).
- Route CLI-wide syntax, dry-run config validation, aliases, and non-export commands to [cli-workflows](../cli-workflows/SKILL.md).
- Route Studio server startup, auth, browser/API runtime, log streaming transport, and UI connectivity to [studio-runtime](../studio-runtime/SKILL.md).
- Stay here for export method choice, checkpoint/output preflight, Python save calls, `unsloth export`, Studio export backend behavior, GGUF/Ollama conversion planning, and export failures.

## Read or run

- Read [references/api-reference.md](references/api-reference.md) for Python save APIs, CLI export arguments, Studio export backend contracts, format names, quantization names, and output artifacts.
- Read [references/workflows.md](references/workflows.md) for safe LoRA, merged, GGUF, Ollama, CLI, Studio, and Hugging Face Hub export workflows.
- Read [references/troubleshooting.md](references/troubleshooting.md) when diagnosing missing checkpoints, wrong export type, tokenizer preservation, path safety, GGUF tools, Hub credentials, memory/sharding, or Unicode subprocess output.
- Run [scripts/inspect_export_targets.py](scripts/inspect_export_targets.py) before heavy exports to validate checkpoint/output paths, tokenizer files, format choices, quantization names, and Hub flags without loading a model or converting files.

## Safe default workflow

1. Identify the source checkpoint and whether it is a PEFT/LoRA adapter, full/base model, or existing GGUF artifact.
2. Run the bundled preflight helper with `--checkpoint`, `--output`, and `--format`; use `--json` when another tool will parse the result.
3. Choose `lora` for adapter-only sharing, `merged-16bit` before downstream conversion, `merged-4bit` only as a final compact bitsandbytes export, or `gguf` for llama.cpp/Ollama-style inference.
4. Keep tokenizer files with every local export; GGUF export requires a tokenizer and may create a `Modelfile` when Unsloth can map the base model to an Ollama template.
5. For Hub uploads, require an explicit repo id, token source, and private/public decision; never print tokens or embed them in scripts, logs, or reusable artifacts.
