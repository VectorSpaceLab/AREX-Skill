---
name: triple-extraction
description: "Guide DeepKE PRGC, PURE, ASP, MT5, and cnSchema triple extraction workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DeepKE triple extraction

Use this sub-skill when a task asks for relational triple extraction or joint entity-relation extraction with DeepKE's PRGC, PURE, ASP, MT5/CCKS, or cnSchema triple workflows. It is for planning, configuring, validating, troubleshooting, and safely post-processing these workflows without assuming the original DeepKE checkout is still available.

## Route by intent

- **Choose PRGC, PURE, ASP, MT5, or cnSchema**: read [references/workflows.md](references/workflows.md) for the scenario decision table and end-to-end operating recipes.
- **Inspect dataset files, generated prediction files, or Hydra/DeepSpeed options**: read [references/data-and-config.md](references/data-and-config.md) before changing filenames, relation labels, or model paths.
- **Post-process MT5/CCKS predictions into JSONL with `kg` triples**: use [scripts/convert_mt5_predictions.py](scripts/convert_mt5_predictions.py). This is the safe bundled replacement for the source MT5 conversion helper.
- **Check local imports, CUDA visibility, and optional file paths without training**: run [scripts/check_triple_env.py](scripts/check_triple_env.py) before approving long native runs.
- **Debug dependency, CUDA, Apex, DeepSpeed, checkpoint, or malformed-output failures**: read [references/troubleshooting.md](references/troubleshooting.md).

## What this sub-skill owns

- **PRGC** joint relational triple extraction using potential relations plus global correspondence, usually over CMeIE/NYT/WebNLG-style `*_triples.json` files and `rel2id.json`.
- **PURE** staged entity extraction plus relation extraction using JSON data and BERT-style encoders.
- **ASP** autoregressive structured prediction for entity-relation extraction, including its CUDA/Apex-heavy runtime expectations.
- **MT5/CCKS** generative triple extraction with DeepSpeed and prediction conversion from `output` strings to `kg` triples.
- **cnSchema triple workflows** that combine DeepKE's Chinese schema-oriented NER/RE/triple examples and require preselected schema labels or checkpoints.

## What this sub-skill does not own

- Standard sentence-level RE, document RE, NER, AE, or EE outside a triple-extraction workflow; route those to the sibling `supervised-extraction` sub-skill.
- Generic data annotation, weak NER labeling, or distant RE labeling; route those to `data-preparation` unless the data is already in a triple-workflow-specific format.
- DeepKE-LLM instruction KGC, OneKE, CodeKGC, GPT/API prompting, or large-model LoRA/P-tuning; route those to `llm-workflows`.
- MCP server/client exposure of extraction predictors; route that to `mcp-tools`.

## Quick operating pattern

1. Identify whether the user has labeled triples, generated predictions, a pretrained checkpoint, or only a goal.
2. Pick the smallest workflow that matches the data and runtime: PRGC for classic joint extraction, PURE for staged entity/relation modeling, ASP for autoregressive structured prediction, MT5 for generative CCKS-style extraction, or cnSchema for Chinese schema inventories.
3. Run `python scripts/check_triple_env.py --task <prgc|pure|asp|mt5|cnschema>` to see which dependencies are present. Add `--data-dir`, `--pretrained-model`, `--checkpoint`, or `--require-cuda` only when those resources are part of the user's requested run.
4. Validate dataset and config names with [references/data-and-config.md](references/data-and-config.md) before launching a native training or prediction script.
5. Treat native PRGC/PURE/ASP/MT5 training, DeepSpeed inference, checkpoint downloads, Apex builds, and GPU-only runs as resource-dependent operations. Do not start them silently; confirm compute, data, and output paths first.
6. For MT5 prediction conversion, prefer the bundled converter and inspect a few `kg` rows before evaluating or submitting results.

## Safety and verification stance

The bundled scripts are safe diagnostics or format converters. They do not train models, call remote APIs, download checkpoints, build Apex, or mutate source config files. Full PRGC/PURE/ASP/MT5 native training remains reference-only because it requires user-provided data, model weights, compatible CUDA/runtime variants, and potentially long-running jobs.
