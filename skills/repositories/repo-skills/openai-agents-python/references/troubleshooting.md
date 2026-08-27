# Cross-Cutting Troubleshooting

Read this for package-level failures before diving into a sub-skill-specific troubleshooting file.

## Install Or Import Fails

Symptoms:

- `ModuleNotFoundError: No module named 'agents'`
- `import agents` imports an unexpected local module.
- `pip show openai-agents` reports a version different from the code or docs being used.

Checks:

```bash
python -m pip show openai-agents
python - <<'PY'
import agents
print(agents.__version__)
print(agents.__file__)
PY
python openai-agents-python/scripts/check_openai_agents_install.py --json
```

Likely causes and fixes:

| Cause | Fix |
| --- | --- |
| Package not installed in the active Python | Install with `pip install openai-agents` in that environment. |
| Running from an unrelated checkout or local file named `agents.py` shadows the package | Change working directory, rename the local file, or inspect `agents.__file__`. |
| Optional surface imported without its extra | Install only the matching extra, such as `openai-agents[voice]`, `openai-agents[redis]`, or `openai-agents[docker]`. |
| Source checkout changed but installed package is older | Reinstall editable for repo development, or refresh this skill if public APIs changed. |

## API Keys And Provider Credentials

Most real model calls need `OPENAI_API_KEY` or provider-specific credentials. The SDK can import and helpers can validate local config without credentials, but `Runner.run`, realtime sessions, hosted tools, MCP remote services, tracing export, or third-party providers may fail at first network call.

Do not print keys while debugging. Use `models-providers` for provider setup and `tracing-observability` for trace-export key separation.

## Optional Extras

| Symptom | Likely missing extra | Route |
| --- | --- | --- |
| `ImportError: numpy + websockets are required to use voice` | `openai-agents[voice]` | `realtime-voice` |
| `RedisSession` import fails | `openai-agents[redis]` | `sessions-memory` |
| `SQLAlchemySession` import fails | `openai-agents[sqlalchemy]` | `sessions-memory` |
| Docker sandbox client import or connection fails | `openai-agents[docker]` plus Docker daemon access | `sandbox-agents` |
| LiteLLM/any-llm adapter import fails | `openai-agents[litellm]` or `openai-agents[any-llm]` | `models-providers` |
| Visualization render fails | `openai-agents[viz]` plus system Graphviz when rendering images | `tracing-observability` |

## Feature Works On One Model Path But Not Another

OpenAI Responses models support SDK features that Chat Completions or third-party adapters may not support, including hosted tool search, certain hosted tools, Responses websocket transport, and some built-in tool payloads.

When a feature mismatch appears:

1. Confirm the effective model/provider under `models-providers`.
2. Check whether the feature is Responses-only.
3. Avoid forcing tool names or selectors that are unavailable on the active provider.
4. Use `strict_feature_validation=True` during development when early rejection is preferable to provider-side surprises.

## Runtime Skill Seems Stale

Read [repo-provenance.md](repo-provenance.md). Refresh the skill when:

- The repository commit differs from the recorded commit.
- The SDK version differs from the recorded package version.
- Public docs, examples, optional dependency groups, `src/agents/`, or test-backed behavior changed.
- A generated helper reports missing or renamed SDK surfaces.

## Where To Go Next

- Core run, streaming, result, or `RunState` issues: [../sub-skills/core-runtime/references/troubleshooting.md](../sub-skills/core-runtime/references/troubleshooting.md)
- Tool, handoff, approval, or guardrail issues: [../sub-skills/tools-handoffs-guardrails/references/troubleshooting.md](../sub-skills/tools-handoffs-guardrails/references/troubleshooting.md)
- Session/history issues: [../sub-skills/sessions-memory/references/troubleshooting.md](../sub-skills/sessions-memory/references/troubleshooting.md)
- Provider/model/websocket issues: [../sub-skills/models-providers/references/troubleshooting.md](../sub-skills/models-providers/references/troubleshooting.md)
- MCP issues: [../sub-skills/mcp-and-hosted-tools/references/troubleshooting.md](../sub-skills/mcp-and-hosted-tools/references/troubleshooting.md)
- Realtime/voice issues: [../sub-skills/realtime-voice/references/troubleshooting.md](../sub-skills/realtime-voice/references/troubleshooting.md)
- Sandbox issues: [../sub-skills/sandbox-agents/references/troubleshooting.md](../sub-skills/sandbox-agents/references/troubleshooting.md)
- Tracing/logging/usage issues: [../sub-skills/tracing-observability/references/troubleshooting.md](../sub-skills/tracing-observability/references/troubleshooting.md)
- Repository development issues: [../sub-skills/repo-development/references/troubleshooting.md](../sub-skills/repo-development/references/troubleshooting.md)
