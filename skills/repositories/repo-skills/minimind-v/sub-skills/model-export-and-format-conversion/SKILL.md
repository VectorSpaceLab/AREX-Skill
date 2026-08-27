---
name: model-export-and-format-conversion
description: "Routes MiniMind-V checkpoint export, Transformers layout
  inspection, and reverse conversion limitation tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model Export and Format Conversion

Use this sub-skill when a user asks how to convert MiniMind-V native PyTorch `*.pth` checkpoints into a Transformers-style directory, inspect an exported directory without loading large weights, diagnose export metadata, or understand reverse conversion limits.

## Route here for

- Native MiniMind-V `out/*.pth` checkpoint to Transformers export plans.
- Dense versus MoE export naming and `VLMConfig` choices.
- Export directory inspection: `config.json`, tokenizer files, weight shards, `auto_map`, `model_type`, `tie_word_embeddings`, and Transformers 5 metadata.
- Reverse conversion from a Transformers directory to a PyTorch `state_dict`.
- Explaining why a Transformers directory may load as a text model while still lacking a usable image encoder for VLM inference.

## Route elsewhere

- Running or serving exported models: `inference-and-serving`.
- Resource acquisition or environment setup: `data-and-resources`.
- Architecture internals: `model-architecture-and-api`.
- Training that produces native weights: `training`.

## Read order

1. Read [conversion workflows](references/conversion-workflows.md).
2. Read [export layout](references/export-layout.md) before inspecting or packaging an export.
3. Read [troubleshooting](references/troubleshooting.md) for conversion/load/tokenizer/vision issues.
4. Run [`inspect_transformers_export.py`](scripts/inspect_transformers_export.py) for safe static inspection without loading weights.

## Safety

Full conversion needs actual checkpoint weights, tokenizer files, MiniMind-V model classes, and the SigLIP2 vision encoder in the user's checkout. Do not claim conversion has run unless those resources were present and the command actually executed.
