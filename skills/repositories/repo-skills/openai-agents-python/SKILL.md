---
name: openai-agents-python
description: "Route tasks for using, debugging, and maintaining the OpenAI
  Agents Python SDK across agents, tools, sessions, models, MCP, realtime,
  sandbox, tracing, and repo-development workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# OpenAI Agents Python

Use this repo skill when a task involves the Python `openai-agents` package, the `agents` import module, or this repository's SDK code, examples, tests, docs, and maintainer workflow.

The root is a router. Read only the nearest sub-skill and references needed for the current task.

## Start Here

1. Install the package with Python 3.10+:

   ```bash
   pip install openai-agents
   ```

2. Use extras only for the workflow that needs them:

   ```bash
   pip install "openai-agents[voice]"       # VoicePipeline, STT/TTS helpers
   pip install "openai-agents[redis]"       # RedisSession
   pip install "openai-agents[sqlalchemy]"  # SQLAlchemySession
   pip install "openai-agents[docker]"      # Docker sandbox client
   pip install "openai-agents[litellm]"     # LiteLLM adapter
   ```

3. Run the bundled install diagnostic when import, extras, or version facts are unclear:

   ```bash
   python openai-agents-python/scripts/check_openai_agents_install.py --json
   ```

4. Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a checkout. If commit, dirty source state, version, or major evidence paths changed, refresh the skill.

## Route By Task

| User task or signal | Read |
| --- | --- |
| Define `Agent`, run `Runner.run`, stream events, inspect `RunResult`, resume `RunState`, use `RunConfig` core settings | [sub-skills/core-runtime/SKILL.md](sub-skills/core-runtime/SKILL.md) |
| Add function tools, hosted tools, local shell/computer/apply-patch tools, agents-as-tools, handoffs, approvals, guardrails | [sub-skills/tools-handoffs-guardrails/SKILL.md](sub-skills/tools-handoffs-guardrails/SKILL.md) |
| Add persistent memory, choose `SQLiteSession` or optional session backends, use OpenAI conversation continuation, compact history | [sub-skills/sessions-memory/SKILL.md](sub-skills/sessions-memory/SKILL.md) |
| Configure OpenAI model providers, Responses vs Chat Completions, websocket transport, third-party adapters, retries, `ModelSettings` | [sub-skills/models-providers/SKILL.md](sub-skills/models-providers/SKILL.md) |
| Integrate local MCP servers, hosted MCP tools, filtering, approvals, structured content, retries, auth/session issues | [sub-skills/mcp-and-hosted-tools/SKILL.md](sub-skills/mcp-and-hosted-tools/SKILL.md) |
| Build realtime sessions, audio/text event loops, telephony attach flows, interruption playback, optional voice pipelines | [sub-skills/realtime-voice/SKILL.md](sub-skills/realtime-voice/SKILL.md) |
| Configure `SandboxAgent`, `Manifest`, entries, capabilities, sandbox clients, snapshots, mounts, sandbox memory, workspace safety | [sub-skills/sandbox-agents/SKILL.md](sub-skills/sandbox-agents/SKILL.md) |
| Configure tracing, processors, spans, sensitive-data controls, usage tracking, logging/debug, visualization | [sub-skills/tracing-observability/SKILL.md](sub-skills/tracing-observability/SKILL.md) |
| Modify this repository, choose focused tests, follow API compatibility rules, update docs/snapshots, prepare PR handoff | [sub-skills/repo-development/SKILL.md](sub-skills/repo-development/SKILL.md) |

## Cross-Cutting References

- Read [references/capability-map.md](references/capability-map.md) when a request spans several SDK surfaces and the owning sub-skill is not obvious.
- Read [references/troubleshooting.md](references/troubleshooting.md) for install/import, API key, optional extra, package-version, and source-vs-installed-package confusion.
- Read [references/repo-routing-metadata.json](references/repo-routing-metadata.json) only when importing or updating the managed `repo-skills-router` entry.

## Bundled Scripts

- Run [scripts/check_openai_agents_install.py](scripts/check_openai_agents_install.py) to inspect package version, importability, public surfaces, and optional extras without API calls.
- Run [scripts/list_example_families.py](scripts/list_example_families.py) to see the distilled example families this skill covers without depending on the original checkout.
- Each sub-skill also owns focused helpers for safe schema, config, manifest, tracing, or test-target checks.

## Important Boundaries

- This skill is self-contained. Do not require future agents to open original repository docs, examples, tests, or scripts at runtime.
- Original examples and tests are evidence. Credentialed, networked, audio-device, Docker, hosted-provider, or long-running examples are distilled into bundled references or marked as verification candidates, not runtime dependencies.
- Most SDK examples require `OPENAI_API_KEY` or another provider credential before real model calls. The bundled helpers avoid model/API calls by default.
- `agents.voice` requires the `voice` extra. Optional session, provider, sandbox, and visualization backends require their matching extras.
- When editing this repository, follow [sub-skills/repo-development/SKILL.md](sub-skills/repo-development/SKILL.md) before changing runtime code, tests, examples, build/test config, or behavior-impacting docs.
