---
name: llm-extraction-services
description: "Use Marker LLM enhancement services and structured extraction safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Marker LLM Extraction Services

Use this sub-skill when a task needs Marker’s `--use_llm` hybrid mode, provider selection, LLM-assisted table/form/equation/page correction, or `ExtractionConverter` structured JSON extraction.

## Read first

- Pick and dry-run provider config with [references/llm-services.md](references/llm-services.md) and [scripts/llm_config_probe.py](scripts/llm_config_probe.py).
- Build and validate extraction schemas with [references/structured-extraction.md](references/structured-extraction.md) and [scripts/validate_extraction_schema.py](scripts/validate_extraction_schema.py).
- Decide which LLM processors matter with [references/llm-processors.md](references/llm-processors.md).
- Diagnose failures with [references/troubleshooting.md](references/troubleshooting.md).

## Fast routing

- For ordinary non-LLM conversion, output formats, `PdfConverter`, `TableConverter`, `marker_single`, and batch CLI basics, route to `../conversion-cli-api/`.
- For custom non-LLM processors/renderers/providers or class-path debugging beyond LLM service paths, route to `../configuration-extension/`.
- For FastAPI, Streamlit, or deployment concerns, route to `../server-deployment/`.

## Core rules

- Always set `use_llm` / `--use_llm`; Marker’s `ConfigParser.get_llm_service()` returns `None` without it, even if `llm_service` is supplied.
- Default LLM backend is `marker.services.gemini.GoogleGeminiService`; pass provider-specific keys/config in CLI flags, `config_json`, or API `config`.
- Do not put API keys in skill files, shared logs, or examples. Use environment injection or local config files managed outside the skill.
- Run bundled scripts only for dry-run inspection; they validate config/schema shape and never call LLM APIs.
