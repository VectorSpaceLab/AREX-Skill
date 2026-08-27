---
name: tools-studio-bench
description: "Use for AutoGen developer tooling maintenance: AutoGen Studio, AG
  Bench, Magentic-One CLI, pyautogen proxy compatibility, CLI help checks, safe
  benchmark/service planning, and dependency/version boundary decisions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# AutoGen Tools, Studio, and Benchmarking

Use this sub-skill when a task involves AutoGen developer tools rather than application code: `autogenstudio`, `agbench`, `m1` / Magentic-One CLI, `pyautogen`, package metadata checks, CLI availability, benchmark planning, or dependency conflicts between tool packages and installed AutoGen libraries.

AutoGen is in maintenance mode. For new greenfield projects, recommend Microsoft Agent Framework; use this skill for existing AutoGen Python maintenance, debugging, migration, and cautious tool usage.

## Route First

- Use `references/compatibility.md` before installing or mixing AutoGen tool packages; Studio and Magentic-One CLI can have dependency ranges that conflict with modern `autogen-core`, `autogen-agentchat`, and `autogen-ext` 0.7.x environments.
- Use `references/studio.md` for `autogenstudio` UI, Lite, API serving, app directory, database, auth, and web-server planning.
- Use `references/agbench.md` for `agbench` help checks, benchmark configuration, lint/tabulate workflows, Docker/native safety, credentials, and result directories.
- Use `references/magentic-one-cli.md` for the `m1` command, sample config inspection, Docker/model requirements, and why the package may need a separate older AutoGen environment.
- Use `references/troubleshooting.md` for CLI not found, Python constraints, dependency conflicts, database/server failures, benchmark provider/Docker/network issues, result paths, and maintenance-mode decisions.

## Boundaries

- Route library application code using `autogen_agentchat` agents, teams, streaming, state, and termination to `agentchat-workflows`.
- Route model clients, MCP, Docker/Jupyter executors, browser tools, optional `autogen_ext` extras, and provider credentials to `extensions-integrations`.
- Route low-level `autogen_core` runtimes, topics, message handlers, subscriptions, components, and distributed runtime internals to `core-runtime`.
- Keep tool inspection safe by preferring metadata reads and `--help`/`--version`; do not start Studio servers, run benchmarks, invoke providers, launch Docker, or execute Magentic-One tasks unless the user explicitly approves those side effects.

## Safe Inspection

Run the bundled inspector when you need a quick environment report:

```bash
python sub-skills/tools-studio-bench/scripts/inspect_tooling.py --json
```

The script only checks imports/distribution metadata and help text for known commands when available. It skips server startup, benchmark execution, Docker, network calls, and provider/model calls.

## Decision Checklist

1. Identify the requested tool package and current installed AutoGen library versions.
2. Check Python version and package dependency ranges before installing any tool into an existing environment.
3. If Studio or Magentic-One CLI conflicts with modern 0.7.x AutoGen libraries, propose a separate environment pinned to the tool’s supported range.
4. For AG Bench, start with `agbench --help`, `agbench run --help`, `agbench lint --help`, and configuration review; do not run tasks until Docker, credentials, and output directories are intentionally prepared.
5. For `pyautogen`, treat current releases as a proxy for `autogen-agentchat`; pin `pyautogen~=0.2.0` only for legacy 0.2-style code.
