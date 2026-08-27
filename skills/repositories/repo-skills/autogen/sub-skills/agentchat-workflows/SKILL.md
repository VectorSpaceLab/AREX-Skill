---
name: agentchat-workflows
description: "Maintain, debug, migrate, and write high-level AutoGen AgentChat
  applications using agents, teams, tools-as-agents, termination, handoffs,
  streaming, state, and serialization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# AgentChat Workflows

Use this sub-skill when working on existing AutoGen Python applications built with `autogen_agentchat`. AutoGen is in maintenance mode: recommend Microsoft Agent Framework for greenfield work, but use this guidance to support existing AutoGen maintenance, debugging, migration, and usage.

## Route Here

Use this sub-skill for:
- `AssistantAgent`, `UserProxyAgent`, `CodeExecutorAgent`, and high-level chat agent behavior.
- Team workflows with `RoundRobinGroupChat`, `SelectorGroupChat`, `Swarm`, `MagenticOneGroupChat`, nested teams, and tools-as-agents.
- `TextMentionTermination`, `MaxMessageTermination`, `HandoffTermination`, streaming with `run_stream`, `Console`, save/load state, and component serialization.
- Migration of v0.2-style `autogen.agentchat` code to the 0.4+ layered `autogen_agentchat` APIs used by 0.7.x.

Route elsewhere when the user needs:
- Low-level routed agents, topics, message handlers, subscriptions, or custom runtime internals: `../core-runtime/SKILL.md`.
- Concrete model clients, MCP, Docker/Jupyter/local executors, memory providers, caches, or optional provider extras: `../extensions-integrations/SKILL.md`.
- AutoGen Studio, AG Bench, Magentic-One CLI, `pyautogen`, or package version-boundary decisions: `../tools-studio-bench/SKILL.md`.

## Start Safely

1. Confirm the package family and version boundary. Current AgentChat maintenance work generally targets `autogen-agentchat` 0.7.x, not legacy `pyautogen` 0.2 APIs.
2. Avoid provider calls while inspecting or debugging structure. Use replay/mock clients, constructor inspection, and bounded teams first.
3. Always add `termination_condition` and/or `max_turns` to teams unless the surrounding app has a verified stop mechanism.
4. Treat agents and teams as stateful. Do not pass full history back into `run`, `run_stream`, `on_messages`, or `on_messages_stream` on every call.
5. Close or clean up concrete model clients, workbenches, and executors according to their integration-specific requirements.

## Common References

- API constructors and important kwargs: `references/api-reference.md`.
- Design patterns for agents, teams, tools, streaming, and no-provider testing: `references/workflows.md`.
- v0.2 migration plus state and serialization guidance: `references/migration-and-state.md`.
- Failure diagnosis and fixes: `references/troubleshooting.md`.
- Safe smoke inspection script: `scripts/agentchat_smoke.py`.

## Minimal Safe Checks

Run signature-only checks without model credentials:

```bash
python scripts/agentchat_smoke.py --mode signatures
```

If imports fail, install or expose compatible `autogen-agentchat`, `autogen-core`, and `autogen-ext` packages before running application-level checks. Do not solve provider credential failures in this sub-skill; route model-client setup to `../extensions-integrations/SKILL.md`.
