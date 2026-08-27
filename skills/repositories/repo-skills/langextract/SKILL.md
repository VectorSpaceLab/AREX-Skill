---
name: langextract
description: "Use LangExtract to extract structured data from unstructured text,
  configure model providers, save/visualize grounded outputs, and author
  provider plugins."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# LangExtract Repo Skill

Use this skill when the user wants to use the `langextract` Python package for source-grounded structured extraction from natural language, provider/back-end configuration, JSONL/HTML result review, or custom provider plugin authoring.

LangExtract's central workflow is: define a prompt and examples, call `lx.extract()`, inspect grounded `AnnotatedDocument` results, optionally save JSONL, and generate interactive HTML visualization. It supports Gemini by default, OpenAI/GPT through the `openai` extra, Ollama/local models, Vertex AI batch processing, and third-party provider plugins.

## Install and smoke check

For ordinary package use:

```bash
python -m pip install langextract
python - <<'PY'
import langextract as lx
print(lx.__name__)
PY
```

For OpenAI provider support:

```bash
python -m pip install "langextract[openai]"
```

Cloud model calls require provider credentials such as `GEMINI_API_KEY`, `LANGEXTRACT_API_KEY`, or `OPENAI_API_KEY`. Ollama calls require a running Ollama service and a pulled local model.

## Route by task

| User task | Read next |
| --- | --- |
| Write or debug `lx.extract()` calls, examples, relationship attributes, output schemas, prompt validation, resolver params, long-document chunking, Unicode tokenization, or grounded span filtering. | [sub-skills/extraction/SKILL.md](sub-skills/extraction/SKILL.md) |
| Choose/configure Gemini, Vertex AI, OpenAI/GPT, OpenAI-compatible endpoints, Ollama/local models, provider kwargs, route resolution, retries, or batch APIs. | [sub-skills/providers/SKILL.md](sub-skills/providers/SKILL.md) |
| Save `AnnotatedDocument` outputs to JSONL, reload JSONL, inspect serialized data, or generate/write interactive HTML visualizations. | [sub-skills/visualization/SKILL.md](sub-skills/visualization/SKILL.md) |
| Create or troubleshoot a custom provider plugin package, entry point, router pattern, or schema adapter. | [sub-skills/provider-plugins/SKILL.md](sub-skills/provider-plugins/SKILL.md) |
| Need the public API map or version-sensitive refresh baseline. | [references/api-map.md](references/api-map.md) and [references/repo-provenance.md](references/repo-provenance.md) |
| Cross-cutting install/import/provider/schema troubleshooting. | [references/troubleshooting.md](references/troubleshooting.md) |

## Operating workflow

1. Identify whether the user's task is extraction design, provider configuration, output review, or provider extension.
2. Read the matching sub-skill before writing code. Read only sibling sub-skills when the request crosses boundaries, such as extraction plus visualization.
3. Keep secrets outside code. Use environment variables or caller-owned secret stores for provider API keys.
4. Start with short, literal text and `show_progress=False` while debugging. Scale to long documents, batch mode, multiple workers, or multiple passes only after examples and grounding look correct.
5. Treat `char_interval=None` as ungrounded output until diagnosed; visualization only highlights valid intervals.
6. Use bundled scripts as safe starters or diagnostics:
   - extraction examples: `sub-skills/extraction/scripts/`
   - provider route/Ollama checks: `sub-skills/providers/scripts/`
   - no-model JSONL/HTML smoke: `sub-skills/visualization/scripts/save_and_visualize.py`
   - provider plugin scaffold: `sub-skills/provider-plugins/scripts/create_provider_plugin.py`

## Do not do these

- Do not tell the user to run examples, tests, scripts, or docs from a source checkout as part of using this skill. Use the bundled references/scripts here or write fresh user-project code.
- Do not enable `fetch_urls=True` for untrusted URLs; fetch and sanitize content yourself, then pass literal text.
- Do not combine `output_schema` with `fence_output=True`, YAML output, or provider-native schema kwargs.
- Do not claim live Gemini/OpenAI/Vertex/Ollama verification unless those credentialed or service-backed checks actually ran in the user's environment.
- Do not put API keys, local Python paths, virtualenv names, conda prefixes, or other machine-specific details in generated user code or reports.

## Freshness

This skill was generated for LangExtract package version `1.6.0`. Before relying on version-sensitive details, read [references/repo-provenance.md](references/repo-provenance.md). If package metadata, provider entry points, public signatures, or major evidence paths differ from that snapshot, refresh the skill.
