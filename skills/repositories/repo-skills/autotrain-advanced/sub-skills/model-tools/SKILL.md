---
name: model-tools
description: "Operate AutoTrain Advanced utility commands for LLM adapter
  merging and Kohya LoRA conversion."
disable-model-invocation: true
metadata:
  disco-role: operating
  parent-skill: autotrain-advanced
license: Apache 2.0
---

# AutoTrain model tools

Use this sub-skill for `autotrain tools` commands and standalone model-artifact utilities.

## Supported commands

```bash
autotrain tools merge-llm-adapter --help
autotrain tools convert_to_kohya --help
```

Tool workflows:

- `merge-llm-adapter` loads a base causal LM, loads a PEFT adapter, merges it, then saves locally and/or pushes to Hub.
- `convert_to_kohya` converts a safetensors LoRA state dict through PEFT format into Kohya format.

## Bundled helper scripts

- `scripts/merge_llm_adapter.py` — source-derived standalone wrapper for the merge function.
- `scripts/convert_to_kohya.py` — source-derived standalone wrapper for Kohya conversion.

Use the package CLI when the installed `autotrain` command is available; use the bundled scripts when a future agent needs a clear self-contained copy of the core tool logic.

## Command templates

```bash
autotrain tools merge-llm-adapter \
  --base-model-path base/model-or-path \
  --adapter-path adapter/model-or-path \
  --output-folder merged-model \
  --token "$HF_TOKEN"
```

```bash
autotrain tools convert_to_kohya \
  --input-path adapter_model.safetensors \
  --output-path adapter_kohya.safetensors
```

## Safety notes

- Adapter merge loads model weights and can consume significant CPU/GPU memory.
- Merge requires either `--output-folder` or `--push-to-hub`.
- Private models/adapters require a valid token.
- Kohya conversion expects a safetensors LoRA state dict, not a full model directory.

## References

- `references/workflows.md` — exact inputs/outputs and script/CLI mapping.
- `references/troubleshooting.md` — load, memory, token, output, and conversion failures.
