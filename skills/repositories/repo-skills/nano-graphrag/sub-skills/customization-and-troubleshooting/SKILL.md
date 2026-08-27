---
name: customization-and-troubleshooting
description: "Customize nano-graphrag prompts, JSON repair, entity extraction,
  DSPy modules, and empty-graph failure recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# customization-and-troubleshooting

Use this sub-skill when nano-graphrag needs prompt changes, robust JSON parsing, custom entity extraction, DSPy extraction, or recovery from empty graph/entity failures.

## Read or run these first

- Read [references/entity-extraction.md](references/entity-extraction.md) when changing `entity_extraction_func`, `entity_extract_max_gleaning`, default entity/relation tuple output, merge behavior, or DSPy extraction modules.
- Read [references/prompts-and-json.md](references/prompts-and-json.md) when editing `nano_graphrag.prompt.PROMPTS`, `GRAPH_FIELD_SEP`, `convert_response_to_json_func`, or community-report JSON expectations.
- Read [references/troubleshooting.md](references/troubleshooting.md) when symptoms include `Leiden.EmptyNetworkError`, `Processed ... 0 entities`, malformed provider output, an Ollama context-window issue, a missing compiled DSPy module, or DSPy `BadRequestError` fallback.
- Run [scripts/json_repair_probe.py](scripts/json_repair_probe.py) on a raw model response when you need to verify whether nano-graphrag's default `convert_response_to_json` can recover a meaningful object before changing application code.

## Route away when needed

- For provider credentials, model client wiring, unsupported API kwargs, base URLs, or ordinary OpenAI-compatible/Ollama/Azure/Bedrock setup, use the sibling `provider-and-model-integrations` sub-skill; return here only when the provider response format breaks extraction or JSON repair.
- For basic `GraphRAG.insert`, `GraphRAG.query`, query modes, chunking lifecycle, and context-only retrieval, use the sibling `core-graphrag-workflows` sub-skill.
- For file, vector, graph, Neo4j, HNSW, or service backend setup, use the sibling `storage-backends` sub-skill unless the backend error is only a secondary symptom of extracting zero entities.

## Fast symptom triage

1. If insertion reports zero entities/relations or Leiden fails on an empty network, inspect entity extraction output format first; do not start by replacing storage.
2. If the community report or global-map step fails to parse JSON, probe the raw response with the bundled JSON repair script, then decide whether to tighten the prompt or supply a custom `convert_response_to_json_func`.
3. If DSPy extraction returns empty lists, check for provider request errors and compiled-module path configuration before assuming the text has no entities.
