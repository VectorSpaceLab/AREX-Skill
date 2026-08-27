# Installation and Configuration

## Install

Use an isolated Python 3.10, 3.11, or 3.12 environment. Install the OWL
artifact or checkout with its declared runtime dependencies, for example:

```bash
python -m pip install -e .
python -m pip check
python -c "import owl.utils; print('OWL utilities import')"
```

The repository metadata pins `camel-ai[owl]==0.2.84` and declares
`docx2markdown`, Gradio, MCP fetch/arXiv helpers, XML parsing, Firecrawl,
Crawl4AI, Mistral, and retry dependencies. Do not add every optional backend,
community-use-case requirement, browser binary, or Docker package unless the
selected workflow needs it. If CAMEL imports fail around `FastMCP`, inspect the
MCP release and use a compatible 1.x line in an isolated environment; confirm
with `pip check` and an actual import.

## Environment variables

The project template documents these groups:

- Model providers: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `QWEN_API_KEY`,
  `DEEPSEEK_API_KEY`, `GROQ_API_KEY`, `GEMINI_API_KEY`/the source's
  `GOOGLE_API_KEY` convention, Azure variables, PPIO, Novita, and VLLM
  endpoint/model variables.
- Search/tools: `GOOGLE_API_KEY`, `SEARCH_ENGINE_ID`, `CHUNKR_API_KEY`, and
  `FIRECRAWL_API_KEY`.

Only set the variables required for the chosen provider/tools. Read
[workforce-workflows](../sub-skills/workforce-workflows/SKILL.md) for provider
selection, [document-processing](../sub-skills/document-processing/SKILL.md)
for service-specific document behavior, and
[web-ui-and-deployment](../sub-skills/web-ui-and-deployment/SKILL.md) for
protected UI/Docker configuration. Never commit or print secret values.

## Backend boundary

OWL's selected package workflows are CPU-importable; provider APIs, browser
binaries, Docker, and GAIA data are optional operational resources. A visible
GPU does not turn an external provider workflow into a verified local GPU
capability. Verify each external service separately before claiming end-to-end
success.
