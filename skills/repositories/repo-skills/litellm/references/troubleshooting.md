# Cross-cutting Troubleshooting

## Import and Install Failures

- `ModuleNotFoundError` for proxy/server packages usually means the base SDK is installed without the proxy extra. Install `litellm[proxy]` for server workflows.
- `ModuleNotFoundError` for MCP or A2A packages usually means optional tool/agent dependencies are missing. Install only the extras required by that workflow.
- Python version issues should be checked against LiteLLM’s supported range: Python `>=3.10,<3.14`.
- If imports succeed from a source checkout but fail in a clean environment, verify distribution metadata with `python -m pip show litellm` and run the root `scripts/check_litellm_environment.py` helper.

## Credentials and Provider Selection

- Missing provider API keys surface as auth errors, provider errors, or model/provider resolution failures. Confirm the environment variable or explicit `api_key` before changing code.
- Unknown provider errors usually mean the model prefix, `custom_llm_provider`, `api_base`/`base_url`, or proxy alias is wrong.
- Azure workflows often require both a deployment-style model name and `api_version`; do not treat Azure model strings exactly like OpenAI model strings.
- Proxy callers use virtual keys; provider keys belong in proxy config, environment variables, secret managers, or credential stores.

## Network and Runtime Calls

- Timeouts can come from provider latency, proxy routing, streaming iteration errors, or service networking. Check direct SDK calls separately from proxy calls.
- Streaming responses must be consumed as iterators/async iterators. A non-streaming parser will not see chunks correctly.
- Live provider calls may cost money and require credentials. Prefer LiteLLM mock responses or bundled offline validators when a task only needs code migration or config validation.

## Optional Dependencies and Services

- Full proxy features may require FastAPI server dependencies, database/prisma support, Redis, object storage clients, guardrail packages, observability SDKs, or provider-specific libraries.
- Do not install all optional extras by default. Pick the smallest set for the selected workflow.
- Database-backed proxy operations require schema/migration readiness; config-only and help checks do not prove DB-backed endpoints work.

## When to Refresh This Skill

Refresh this skill if the LiteLLM checkout has a different package version, major API signature changes, moved proxy config schemas, new endpoint families, changed router semantics, or substantial changes under the evidence paths listed in `repo-provenance.md`.
