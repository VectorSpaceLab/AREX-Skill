---
name: openllmetry
description: "Route OpenLLMetry Python SDK, GenAI instrumentation,
  semantic-convention, and repository-maintenance tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenLLMetry

Use this repo skill for the Python OpenLLMetry package suite: the Traceloop SDK, OpenTelemetry GenAI instrumentations, the `opentelemetry.semconv_ai` semantic-convention layer, and checkout-local package maintenance.

## Read this skill when

- You need to add OpenLLMetry tracing to a Python LLM, RAG, vector database, agent, MCP, or provider SDK application.
- You need to choose between `Traceloop.init(...)` and direct `OpenAIInstrumentor().instrument()`-style setup.
- You need exact OpenLLMetry semantic-convention constants, span attributes, event/message schemas, or legacy alias migration guidance.
- You need to troubleshoot missing optional target libraries, no emitted spans, content tracing, metrics/logging, VCR cassette replay, or Nx/uv test commands.
- You are editing an OpenLLMetry checkout and need package/test/source-script guidance.

## Fast install/import checks

For application use, start with the SDK:

```bash
pip install traceloop-sdk
```

For direct wrapper use, install the instrumentation package and the target client library it wraps. Many packages declare the target library in an `instruments` optional extra, for example:

```bash
pip install 'opentelemetry-instrumentation-openai[instruments]'
```

Minimal imports:

```python
from traceloop.sdk import Traceloop
from traceloop.sdk.decorators import workflow, task, agent, tool
from traceloop.sdk.instruments import Instruments
from opentelemetry.semconv_ai import SpanAttributes
```

Run [`scripts/check_openllmetry_env.py`](scripts/check_openllmetry_env.py) to check installed package metadata and safe imports without provider calls or network access.

## Route by task

| If the task is about... | Read |
| --- | --- |
| SDK bootstrap, exporters/processors, decorators, manual LLM spans, association properties, content tracing, prompt/dataset/experiment/guardrail client surfaces | [`sub-skills/sdk-and-tracing/SKILL.md`](sub-skills/sdk-and-tracing/SKILL.md) |
| Direct provider/vector/framework/protocol instrumentors, SDK `Instruments` selection, optional target clients, duplicate/no-span wrapper troubleshooting | [`sub-skills/instrumentations/SKILL.md`](sub-skills/instrumentations/SKILL.md) |
| `opentelemetry.semconv_ai`, GenAI message schemas, provider names, finish reasons, `LLM_*` to `GEN_AI_*` migration, semconv compliance checks | [`sub-skills/semantic-conventions/SKILL.md`](sub-skills/semantic-conventions/SKILL.md) |
| Nx/uv package maintenance, focused test selection, VCR cassettes, source scripts, release/codegen cautions, package discovery in a checkout | [`sub-skills/repo-development/SKILL.md`](sub-skills/repo-development/SKILL.md) |

## Shared references

- [`references/package-overview.md`](references/package-overview.md) explains the package family, selected scope, distribution categories, and prerequisites.
- [`references/troubleshooting.md`](references/troubleshooting.md) covers cross-cutting install/import/export/content issues before routing to sub-skill-specific troubleshooting.
- [`references/repo-provenance.md`](references/repo-provenance.md) records the source snapshot used to generate this skill. Read it before deciding whether a checkout needs `refresh-repo-skill`.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json) is structured router metadata for managed repo-skill imports.

## Operating rules

- Prefer no-network smoke checks and in-memory exporters before live provider calls.
- Treat cloud/provider keys, VCR re-recording, vector services, local Ollama daemons, and model downloads as explicit prerequisites, not default verification steps.
- Do not assume a missing provider client is an OpenLLMetry bug; many instrumentor modules require the target client package at import time.
- Use `TRACELOOP_TRACE_CONTENT=false` to suppress prompt/completion/entity content when privacy matters.
- In a checkout, use Nx for workspace orchestration and `uv` for package-local Python commands.
