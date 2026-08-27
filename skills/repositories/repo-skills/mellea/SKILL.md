---
name: mellea
description: "Use Mellea to build, test, serve, evaluate, instrument, and extend
  typed generative Python programs across provider backends and agent
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Mellea

Mellea is a Python library for **generative programs**: typed functions and
components become model calls, schemas constrain outputs, requirements validate
meaning, and sampling can repair or select candidates. Use this repo skill when
a task names Mellea, `generative`, `MelleaSession`, `mellea.stdlib`, `m serve`,
`m eval`, Granite adapters, Mellea plugins, or a Mellea-compatible provider.

## Fast route map

Choose the smallest route that owns the work:

- [generative-programming](sub-skills/generative-programming/SKILL.md): typed
  generation, sessions, contexts, components, requirements, repair, async,
  streaming, MObjects, and `mify`.
- [backends-and-models](sub-skills/backends-and-models/SKILL.md): Ollama,
  OpenAI-compatible, Hugging Face, Watsonx, LiteLLM/Bedrock, model options,
  multimodal inputs, Granite formatters, and adapters.
- [tools-and-agents](sub-skills/tools-and-agents/SKILL.md): tool calls,
  interpreters, shell safety, MCP, ReAct, context compaction, and agent
  integrations.
- [sampling-and-evaluation](sub-skills/sampling-and-evaluation/SKILL.md):
  rejection/majority/feedback sampling, verifiers, unit-test evaluation,
  LLM-as-judge, metrics, and `m eval`.
- [serving-and-cli](sub-skills/serving-and-cli/SKILL.md): `m` commands, Mellea
  HTTP serving, model routing, response formats, streaming endpoints,
  decomposition, and safe CLI inspection.
- [observability-and-extensions](sub-skills/observability-and-extensions/SKILL.md):
  plugins, hooks, logging, metrics, tracing, OpenTelemetry, custom components,
  and extensions.

If a request crosses routes, start here, select an owner for each phase, and
keep the backend, safety, evaluation, serving, or telemetry boundary explicit.

## Install and inspect

Mellea requires Python 3.11 or newer. For a normal application install:

```bash
uv pip install mellea
```

Add only the extra for the selected surface, for example:

```bash
uv pip install 'mellea[hf]'          # local Hugging Face backend
uv pip install 'mellea[server,cli]'  # HTTP service and m CLI
uv pip install 'mellea[tools]'       # MCP/tool integrations
uv pip install 'mellea[telemetry]'   # OpenTelemetry and hook telemetry
```

Do not install `all` merely to fix an import. Provider credentials, Ollama,
model checkpoints, cloud SDK configuration, and servers are separate runtime
prerequisites. Read [troubleshooting](references/troubleshooting.md) before
changing dependencies. For source-version alignment, inspect
[provenance](references/repo-provenance.md).

Minimal base import check:

```bash
python -c "import mellea; print('mellea import ok')"
```

## Operating rules

1. Establish the backend and credential/service boundary before writing a real
   generation call; use a dummy or mocked backend for deterministic checks.
2. Treat type annotations as output shape, not proof of semantic correctness;
   combine schemas with requirements and explicit validators.
3. Make session/context ownership explicit. Choose independent contexts for
   concurrency and a chat context only when history is intentional.
4. Keep tool execution, generated-code execution, network calls, checkpoint
   downloads, and exporters disabled in dry-run or parser checks.
5. Separate deterministic unit assertions from qualitative model-output claims.
6. Preserve usage metadata and paired lifecycle hooks when instrumenting spans;
   a completion-only hook can feed a metric but cannot open and close a span.

## Self-contained helper boundary

Bundled helpers live under the owning route's `scripts/` directory. They are
safe diagnostics or validators, not replacements for a model provider:

- `backends-and-models/scripts/check_backends.py` checks imports and optional
  device state without provider calls.
- `generative-programming/scripts/inspect_api.py` prints verified signatures.
- `tools-and-agents/scripts/audit_tool_request.py` audits JSON tool requests
  without executing them.
- `sampling-and-evaluation/scripts/validate_eval_config.py` validates a small
  eval config without running an evaluator.
- `serving-and-cli/scripts/check_cli_surface.py` inspects CLI help/static
  structure without starting a server.
- `observability-and-extensions/scripts/check_telemetry_install.py` checks
  telemetry imports without creating exporters.

Read the nearest sub-skill before running a helper; do not pass secrets or
large payloads to diagnostics.
