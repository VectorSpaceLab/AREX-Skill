---
name: data-and-templates
description: "Use this sub-skill when working on LlamaFactory dataset_info
  entries, Alpaca/ShareGPT/OpenAI data rows, multimodal media columns, prompt
  templates, tool-calling fields, preprocessing validation, or data processor
  behavior. It covers v0 data loading/conversion/template/preprocessing issues
  and excludes launch, optimizer, export, API serving, and web UI operations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LlamaFactory Data And Templates

Use this sub-skill for LlamaFactory 0.9.6.dev0 v0 data preparation and prompt-formatting work. The v0 CLI entry points are `llamafactory-cli` and `lmf`; v0 is the default unless `USE_V1=1` is set.

## Route The Task

- For `dataset_info.json` entries, local/remote dataset selection, column mappings, ranking flags, and media columns, read `references/data-formats.md`.
- For `template:`, `tool_format`, thinking flags, prompt construction, processor selection, packing, and tokenization behavior, read `references/templates-and-processing.md`.
- For common failure modes such as undefined datasets, missing registry files, wrong columns/tags, ranking mismatch, media-token mismatch, and `tokenized_path` confusion, read `references/troubleshooting.md`.
- To statically check a registry entry and optional tiny row file without importing LlamaFactory, run `python scripts/validate_dataset_entry.py --help`.

## Boundaries

This sub-skill owns data registry/schema/template/preprocessing diagnosis. Hand off training launch, optimizer, LoRA, distributed, and YAML orchestration decisions to `training-and-configs`; model loading, quantization, adapters, and export to `model-loading-and-export`; and service/API/web UI operations to `inference-and-serving` or `webui-and-ops`.

## Fast Workflow

1. Identify the dataset name listed in `dataset:` or `eval_dataset:` and verify a matching top-level key exists in `dataset_info.json` under `dataset_dir`.
2. Determine load source precedence: hub URL keys first, then script, cloud file, then local `file_name`.
3. Confirm `formatting` is `alpaca`, `sharegpt`, or code-backed `openai`, and verify the declared `columns` and `tags` match representative rows.
4. Check task/stage compatibility: reward-modeling expects `ranking: true`; most non-RM stages reject ranking datasets.
5. Check `template:` supports the model family and any multimodal placeholders present in the data.
6. Run the bundled validator for early static issues before trying a full train command.
