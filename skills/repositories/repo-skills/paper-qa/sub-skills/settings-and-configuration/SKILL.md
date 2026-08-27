---
name: settings-and-configuration
description: "Configure PaperQA Settings, named configs, LLM providers,
  embeddings, vector stores, prompts, callbacks, and optional dependencies."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PaperQA Settings and Configuration

Use this sub-skill when the task is to choose, validate, or troubleshoot PaperQA configuration rather than run a query or build an index.

## Route here for

- Loading or adapting named `Settings` configs such as `fast`, `high_quality`, `debug`, clinical-trials configs, `contracrow`, `wikicrow`, `openreview`, or OpenAI tier-limit configs.
- Setting all PaperQA model roles: `llm`, `summary_llm`, `agent.agent_llm`, and parser enrichment LLMs.
- Choosing embedding providers, hybrid/sparse/local embeddings, vector stores, embedding cache behavior, and Qdrant prerequisites.
- Writing or checking PaperQA settings JSON, nested settings dictionaries, prompt templates, LiteLLM router configs, rate limits, and callback-related settings.
- Diagnosing API-key/provider mismatches, optional extras, prompt variable validation, and `gpt-5`/`o1` temperature behavior.

## Route elsewhere

- To actually ask questions, call `Docs.aquery`, gather evidence, or use callbacks during a run, use `../agentic-rag/`.
- For `pqa` commands, manifest/index operation, and search-index lifecycle, use `../cli-and-indexing/`.
- For parser function selection, PDF/media parsing, Office parsing, and chunking details, use `../docs-and-parsing/`.
- For ClinicalTrials.gov, OpenReview, Zotero, and metadata-provider semantics, use `../metadata-and-sources/`.

## Operating workflow

1. Start from `Settings()` or `Settings.from_name("<config>")`; use [settings-reference.md](references/settings-reference.md) to decide which fields belong in root, `answer`, `parsing`, `prompts`, or `agent`.
2. If changing providers, update every active model role together: `llm`, `summary_llm`, `agent.agent_llm`, `embedding`, and parser `enrichment_llm` when multimodal enrichment is on. Use [model-and-embedding-config.md](references/model-and-embedding-config.md).
3. Validate settings JSON before a run with `scripts/validate_settings_json.py`; print bundled config summaries with `scripts/print_named_settings.py`.
4. If validation or provider setup fails, use [troubleshooting.md](references/troubleshooting.md) before changing query code.

## Bundled safe helpers

- `scripts/print_named_settings.py` prints concise summaries of installed bundled settings without calling LLMs, embeddings, network services, or external automation.
- `scripts/validate_settings_json.py` validates a PaperQA settings JSON file and reports provider/key, prompt-variable, router-shape, temperature, and optional-extra warnings without calling LLMs or embeddings.
