---
name: autogen
description: "Use this skill for maintaining, migrating, debugging, and safely
  operating Microsoft AutoGen Python 0.7.x applications, including AgentChat,
  Core runtimes, extensions, Studio, Magentic-One, AG Bench, and pyautogen
  compatibility."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# AutoGen

Use this skill when the user is working with Microsoft AutoGen Python code, especially existing AutoGen 0.7.x applications, migration from older AutoGen APIs, AgentChat teams, Core runtimes, `autogen-ext` integrations, AutoGen Studio, Magentic-One, AG Bench, or `pyautogen` compatibility.

AutoGen is in maintenance mode. For brand-new greenfield agent applications, first recommend Microsoft Agent Framework. Continue with this skill when the user is maintaining current AutoGen systems, reproducing behavior, migrating existing code, or explicitly asks for AutoGen.

## Quick Routing

- Use `sub-skills/agentchat-workflows/` for high-level `autogen_agentchat` agents, teams, tools-as-agents, messages, termination, handoffs, streaming, state, serialization, and v0.2 migration.
- Use `sub-skills/core-runtime/` for lower-level `autogen_core` routed agents, runtimes, message handlers, topics/subscriptions, tools, components, serialization, cancellation, intervention, and distributed runtime design.
- Use `sub-skills/extensions-integrations/` for `autogen_ext` model clients, optional extras, MCP, code executors, memory/cache, surfer/helper agents, provider credentials, and gRPC extension setup.
- Use `sub-skills/tools-studio-bench/` for AutoGen Studio, Magentic-One CLI, AG Bench, `pyautogen`, safe CLI checks, benchmark/service planning, and package version-boundary decisions.

## Start Here

1. Identify whether the task is an application workflow, low-level runtime, optional integration, or developer tooling problem.
2. Read `references/package-map.md` for package names, install commands, version boundaries, and safe import checks.
3. Read `references/troubleshooting.md` for cross-cutting install/import, async, optional dependency, credential, and migration failures.
4. Run `python scripts/inspect_autogen_install.py --json` in the target environment to inspect installed AutoGen packages without network calls, provider credentials, Docker, Jupyter, Studio startup, or benchmark execution.
5. Route to the focused sub-skill and use its references/scripts for concrete APIs, commands, examples, and troubleshooting.

## Package Map

- `autogen-core==0.7.5` provides foundational runtimes, routed agents, messages, components, model/tool interfaces, and serialization.
- `autogen-agentchat==0.7.5` provides high-level agents, teams, termination, streaming, UI helpers, and depends on `autogen-core==0.7.5`.
- `autogen-ext==0.7.5` provides optional integrations and is intentionally extra-driven; install only the extras needed for the workflow.
- `pyautogen==0.10.0` is a compatibility/proxy package for current `autogen-agentchat`; pin old `pyautogen~=0.2` only for legacy v0.2 code.
- `agbench==0.0.1a1` exposes the `agbench` console script for benchmark configuration, linting, runs, and result tabulation.
- AutoGen Studio and Magentic-One CLI in this source snapshot have dependency ranges older than the 0.7.x libraries; check `sub-skills/tools-studio-bench/references/compatibility.md` before installing them into an existing environment.

## Safe Defaults

- Prefer minimal packages: `autogen-agentchat`, `autogen-core`, and only the needed `autogen-ext[...]` extras.
- Do not install broad optional extras or tool packages into an existing environment until dependency ranges are checked.
- Treat model providers, MCP servers, Docker/Jupyter executors, browser tools, Studio servers, database backends, and AG Bench runs as side-effectful or credential-dependent until explicitly prepared.
- Keep examples bounded with termination conditions, `max_turns`, cleanup (`close()`, `stop()`, `stop_when_idle()`), and isolated execution directories.
- Do not copy secrets into component configs, serialized teams, benchmark configs, Studio app directories, or troubleshooting logs.

## Bundled Checks

From the root of this skill directory or after copying the script paths into a command:

```bash
python scripts/inspect_autogen_install.py --json
python sub-skills/agentchat-workflows/scripts/agentchat_smoke.py --mode signatures
python sub-skills/core-runtime/scripts/core_runtime_smoke.py --inspect
python sub-skills/extensions-integrations/scripts/inspect_extensions.py --json
python sub-skills/tools-studio-bench/scripts/inspect_tooling.py --json
```

These scripts inspect package metadata, imports, signatures, and help text only. They do not start provider calls, Studio, Docker, Jupyter, MCP servers, browsers, Redis/ChromaDB, or benchmarks by default.

## References

- `references/package-map.md` explains package names, install choices, optional extras, console scripts, and compatibility boundaries.
- `references/troubleshooting.md` covers cross-cutting failure diagnosis before routing to a focused sub-skill.
- `references/repo-provenance.md` records the source snapshot and evidence used to generate this skill.

## Boundary Notes

- This skill is for using and maintaining AutoGen Python, not for unrelated monorepo development.
- The .NET implementation is outside the selected extraction scope except for conceptual cross-runtime/protocol context that informs Core runtime notes.
- Docs build assets, CI/release automation, generated protobuf maintenance, frontend internals, and large credential/network examples are excluded unless the user explicitly asks for maintainer work in those areas.
- Runtime instructions in this skill are self-contained; source documentation, tests, and samples informed the skill but are not required to use it.
