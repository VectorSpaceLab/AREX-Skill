---
name: repo-development
description: "Modify the ADK Python repository itself with repo-specific setup,
  style, testing, docs, samples, schema generation, and review conventions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ADK Python Repo Development

Use this sub-skill when the user asks to change, review, or validate the ADK Python repository itself. It is for maintainer workflows, not for using ADK as an application library.

## Route Common Requests

- **Set up or validate a contributor environment**: use [Development and Testing](references/development-and-testing.md) for `uv`, extras, formatter, linter, type-check, pytest, and tox commands.
- **Select focused tests for a code change**: use [select_adk_tests.py](scripts/select_adk_tests.py), which maps changed files or capability names to likely pytest targets and non-test checks without running anything.
- **Modify source, public APIs, configs, docs, or samples**: use [Development and Testing](references/development-and-testing.md) for style rules, public API conventions, generated schema checks, and docs/sample update policy.
- **Review local changes before handoff**: use [Review Checklist](references/review-checklist.md) for architecture, style, tests, docs, samples, and safety gates.
- **Debug repo-maintenance failures**: use [Troubleshooting](references/troubleshooting.md) for formatter/import issues, optional dependencies, flaky or credentialed tests, stale schemas, and unsafe git operations.

## Boundaries

- Use this sub-skill for repository maintenance: files under `src/google/adk/`, `tests/`, `docs/`, `contributing/samples/`, packaging/configuration, and contributor scripts.
- Route library usage questions about constructing `Agent`/`LlmAgent` to the agent-construction sub-skill.
- Route ADK `Workflow` graph design and runtime behavior to workflow-orchestration.
- Route tools, toolsets, auth, MCP/OpenAPI/Google/cloud integrations to tools-and-integrations.
- Route `Runner`, `App`, sessions, memory, artifacts, plugins, telemetry, and code execution services to runtime-services.
- Route CLI app discovery, YAML config, `adk run`, `adk web`, `adk api_server`, deploy, and eval command usage to cli-configuration-deployment unless the task is changing the CLI implementation itself.
- Route eval/test JSON design and debugging an ADK app run to evaluation-debugging unless the task is changing repo test infrastructure.

## Maintainer Defaults

- Package facts: `google-adk` 2.3.0, import root `google.adk`, Python 3.10+.
- Base installation may omit optional extras such as `db`, `extensions`, `mcp`, and cloud integrations; missing optional imports are expected failure modes, not automatic blockers.
- Prefer focused validation first, then broaden only when the changed surface or risk justifies it.
- Do not perform destructive git operations, publish packages, run credentialed remote/cloud tests, or rewrite broad areas without explicit user approval.
