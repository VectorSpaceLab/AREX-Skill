---
name: deepke
description: "Route DeepKE knowledge extraction workflows across supervised
  extraction, data prep, triples, LLMs, and MCP tools."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DeepKE repo skill

Use this skill when a task asks how to use, configure, validate, or troubleshoot DeepKE for knowledge extraction: named entity recognition, relation extraction, attribute extraction, event extraction, relational triple extraction, instruction/LLM knowledge graph construction, data conversion, weak/distant supervision, or the local DeepKE MCP wrapper.

## First route the request

| User intent | Read/use |
| --- | --- |
| Standard/few-shot/multimodal/cross-domain NER, standard/few-shot/document/multimodal RE, AE, EE, or cnSchema quick-load extraction | [sub-skills/supervised-extraction/SKILL.md](sub-skills/supervised-extraction/SKILL.md) |
| Annotation export conversion, NER BIO files, RE/AE CSV files, weak NER dictionary labeling, or distant RE labeling | [sub-skills/data-preparation/SKILL.md](sub-skills/data-preparation/SKILL.md) |
| PRGC, PURE, ASP, MT5/CCKS, cnSchema triple workflows, or MT5 prediction-to-`kg` conversion | [sub-skills/triple-extraction/SKILL.md](sub-skills/triple-extraction/SKILL.md) |
| DeepKE-LLM, InstructKGC, OneKE, LLMICL/API prompting, UnleashLLMRE, CodeKGC, CPM-Bee, LoRA/P-tuning/OpenDelta | [sub-skills/llm-workflows/SKILL.md](sub-skills/llm-workflows/SKILL.md) |
| DeepKE MCP server/client wrapper, local tool exposure, stdio server diagnostics, or MCP TSV conversion | [sub-skills/mcp-tools/SKILL.md](sub-skills/mcp-tools/SKILL.md) |
| Unsure whether DeepKE is installed or which broad area is available | Run [scripts/check_deepke_core.py](scripts/check_deepke_core.py), then route to a focused sub-skill. |

## Core operating rules

1. **Classify the task before running anything**: data conversion, training, prediction, post-processing, API/LLM call, MCP deployment, or troubleshooting each has a different safety profile.
2. **Use bundled references/scripts instead of the original checkout**: this generated skill is self-contained. Do not require the original repository tree just to answer workflow questions or run safe converters/checkers.
3. **Treat long runs as explicit operations**: BERT/CLIP/T5/MT5/OneKE fine-tuning, DeepSpeed, Apex, multimodal training, and API calls need user approval for compute, downloads, credentials, and runtime.
4. **Validate data before blaming models**: check filenames, JSONL versus JSON array shape, labels, offsets, schema size, train/dev/test splits, and parsed outputs.
5. **Keep credentials and private paths out of shared files**: API keys, endpoint tokens, local checkpoint paths, and environment prefixes belong in local runtime configuration only.
6. **Report backend limits honestly**: CPU diagnostics can prove import and converter behavior, but not CUDA/Apex/DeepSpeed/large-model runtime readiness.

## Safe top-level diagnostic

From this skill directory, run:

```bash
python scripts/check_deepke_core.py --json
```

This imports representative DeepKE modules and common dependencies and reports CUDA visibility. It does not train, download, load model weights, call APIs, or mutate configs. Use focused checkers in the sub-skills for task-specific path and dependency checks.

## Focused bundled scripts

- `sub-skills/supervised-extraction/scripts/check_supervised_env.py`: safe import/data/checkpoint diagnostics for NER/RE/AE/EE/cnSchema workflows.
- `sub-skills/data-preparation/scripts/convert_supervised_data.py`: labeled JSON/DOCX/XLSX to DeepKE NER TXT or RE/AE CSV.
- `sub-skills/data-preparation/scripts/prepare_weaksupervised_data.py`: dictionary-based NER weak supervision.
- `sub-skills/data-preparation/scripts/ds_label_data.py`: RE distant supervision from triples.
- `sub-skills/triple-extraction/scripts/check_triple_env.py`: safe PRGC/PURE/ASP/MT5/cnSchema dependency/path diagnostic.
- `sub-skills/triple-extraction/scripts/convert_mt5_predictions.py`: MT5/CCKS prediction conversion into JSONL records with parsed `kg` triples.
- `sub-skills/llm-workflows/scripts/check_llm_workflow_env.py`: safe DeepKE-LLM package/API/CUDA/path diagnostic.
- `sub-skills/llm-workflows/scripts/convert_ie_instruction.py`: simple standalone IE/KG record to instruction JSONL converter.
- `sub-skills/mcp-tools/scripts/check_mcp_env.py`: MCP wrapper import/env diagnostic without launching the server.
- `sub-skills/mcp-tools/scripts/convert_text_to_tsv.py`: event-extraction text-to-TSV helper adapted from the MCP tools.

## Repo-level references

- [references/repo-overview.md](references/repo-overview.md): capability map, environment families, and known coverage limits.
- [references/troubleshooting.md](references/troubleshooting.md): cross-cutting dependency, backend, data, and safety troubleshooting.
- [references/repo-provenance.md](references/repo-provenance.md): source evidence, version, verification baseline, and refresh notes.
