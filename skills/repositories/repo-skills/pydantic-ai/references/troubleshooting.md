# Cross-Cutting Troubleshooting

Use this reference for package-level failures before routing to a deeper sub-skill.

## Import Fails

Symptoms:

- `ModuleNotFoundError: No module named 'pydantic_ai'`
- `ModuleNotFoundError` for `pydantic_graph`, `pydantic_evals`, or `clai`
- Console command `clai` or `pai` is unavailable

Actions:

1. Run `python scripts/check_environment.py` from the root of this skill.
2. Confirm the intended package is installed: `pydantic-ai`, `pydantic-ai-slim`, `pydantic-graph`, `pydantic-evals`, or `clai`.
3. If the error names a provider SDK such as `openai`, `anthropic`, `google-genai`, `groq`, or `mistralai`, route to `../sub-skills/models-and-providers/SKILL.md` and install the smallest provider extra.
4. If the error names `mcp`, `fastmcp`, `starlette`, `ag_ui_protocol`, `temporalio`, `dbos`, `prefect`, or `logfire`, route to `../sub-skills/mcp-and-integrations/SKILL.md`.

## Model String Does Not Resolve

Symptoms:

- Error says the model name is unknown or missing a provider.
- Code uses `'gpt-5.2'` instead of `'openai:gpt-5.2'`.
- OpenAI-compatible endpoints route to the wrong provider.

Actions:

1. Use provider-prefixed strings such as `openai:gpt-5.2`, `anthropic:claude-opus-4-6`, `google:gemini-3-pro-preview`, or `openrouter:google/gemini-3-pro-preview`.
2. Read `../sub-skills/models-and-providers/references/model-selection.md` for direct model/provider/profile class decisions.
3. Use `known_model_names()` only as a helper; do not assume every known model is accessible without credentials or current provider support.

## Live Provider Request Fails

Symptoms:

- Authentication errors, quota errors, 401/403/429/5xx responses.
- Provider SDK missing even though `pydantic_ai` imports.
- Native tool or structured output is accepted by one model but rejected by another.

Actions:

1. Separate package import, credential configuration, provider availability, and request-shape compatibility.
2. Run provider import diagnostics from `../sub-skills/models-and-providers/scripts/check_optional_provider.py`.
3. Use `TestModel` or `FunctionModel` to isolate application logic from provider behavior.
4. Do not record cassettes, run paid requests, or mutate cloud resources unless explicitly requested.

## Tool or Output Behavior Is Confusing

Symptoms:

- Tool does not receive `RunContext`, or receives it when it should not.
- Structured output returns plain text unexpectedly.
- A model calls a tool after text appears during streaming.
- Output tool history breaks a handoff to another agent.

Actions:

- Route tool schemas and `RunContext` decorator choices to `../sub-skills/tools-and-toolsets/SKILL.md`.
- Route structured output modes, output functions, and message-history serialization to `../sub-skills/outputs-and-messages/SKILL.md`.
- Route streaming run-mode choices to `../sub-skills/agent-core/SKILL.md`.

## CLI or Web UI Fails

Symptoms:

- `clai --help` works but a live prompt fails.
- `clai web` cannot bind a port.
- `--agent module:variable` cannot import an agent.
- Browser UI starts but model calls fail.

Actions:

1. Read `../sub-skills/cli-and-apps/SKILL.md`.
2. Run `python scripts/check_environment.py --cli` from the root of this skill.
3. Validate the custom agent import separately before starting the web UI.
4. Treat provider credentials and optional native tools as separate model/provider issues.

## Repository Checkout Seems Out of Sync

Symptoms:

- Current source/docs/tests disagree with this skill.
- Public APIs, docs, examples, package extras, or CLI behavior changed.
- `references/repo-provenance.md` commit differs from the checkout.

Actions:

1. Read `references/repo-provenance.md`.
2. If repository evidence changed materially, run `refresh-repo-skill` instead of editing this skill ad hoc.
3. For maintainer validation and cassette workflows, route to `../sub-skills/repo-development/SKILL.md`.
