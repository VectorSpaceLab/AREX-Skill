---
name: evaluation-debugging
description: "Design and run ADK evaluation, test, and debugging workflows for
  eval sets, JSON fixtures, event traces, sessions, and safe native
  verification."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluation Debugging

Use this sub-skill when the user needs to create or run ADK evaluation cases, replay JSON tests, inspect session events, summarize traces, or choose safe native verification targets for an ADK agent.

## Route Common Requests

- Convert a manual interaction into an `adk test` fixture or replay existing `tests/*.json` event files with deterministic mocks: use [Evaluation Workflows](references/evaluation-workflows.md).
- Run metric-based EvalSet checks with `adk eval`, `adk eval_set`, or `google.adk.evaluation.AgentEvaluator`: use [Evaluation Workflows](references/evaluation-workflows.md).
- Debug missing tool calls, unexpected output, callback order, branch/node routing, or event/session state: use [Debugging](references/debugging.md).
- Diagnose schema validation, credentials, flaky LLM metrics, missing trace attributes, and server session lookup failures: use [Troubleshooting](references/troubleshooting.md).
- Summarize raw ADK session/event JSON without exposing long values: run [summarize_adk_events.py](scripts/summarize_adk_events.py).

## Boundaries

- Stay in this sub-skill for `adk test`, `adk eval`, `adk eval_set`, JSON test/eval fixtures, `AgentEvaluator`, event printing, session/trace inspection, and selecting safe native eval/debug verification candidates.
- Route general CLI command discovery, agent app layout, server startup, deployment, and YAML configuration mechanics to `cli-configuration-deployment`.
- Route code changes to agent constructors, tools, callbacks, instructions, schemas, or model binding to `agent-construction` or `tools-and-integrations`.
- Route repository maintainer style, broad pytest policy, docs/sample update policy, and PR review gates to `repo-development`.

## Safe Defaults

- Prefer read-only checks first: `adk test --help`, `adk eval --help`, `adk eval_set --help`, fixture validation, event summaries, and focused native candidates.
- Do not start a long-running `adk web` or `api_server` process unless the user asks or confirms; if one is already running, inspect it before starting another.
- Treat model credentials, cloud storage, Vertex AI scenario generation, and LLM-as-judge metrics as environment-dependent; separate these from deterministic local replay.
- Never print full tool arguments, session state, trace payloads, or model requests when they may contain secrets; truncate and redact before sharing.

## Quick Decision Guide

| Goal | Best path | Why |
| --- | --- | --- |
| Regression-test exact event flow | `adk test AGENTS_DIR` with `tests/*.json` | Replays stored event JSON, mocks model outputs/randomness, and normalizes volatile IDs. |
| Score behavior against references/tools | `adk eval AGENT_INIT EVAL_SET` or `AgentEvaluator.evaluate(...)` | Uses EvalSet metrics such as `tool_trajectory_avg_score` and `response_match_score`. |
| Inspect why a web session failed | Fetch session JSON, summarize events, then inspect `/dev/apps/{app}/debug/trace/session/{session}` | Correlates events, node paths, tool calls, and LLM/tool spans. |
| Choose repo-native verification | Start with focused evaluation unit coverage, selected eval fixture integration coverage, and CLI help | Avoids broad, credential-heavy, or server-dependent runs unless needed. |

## Bundled Reference Map

- [Evaluation Workflows](references/evaluation-workflows.md) — EvalSet schemas, legacy JSON, CLI/API routes, fixture design, assertions, and native candidates.
- [Debugging](references/debugging.md) — `adk run`/`web` debugging, session and trace inspection, event fields, callback order, and `print_event` usage.
- [Troubleshooting](references/troubleshooting.md) — Concrete failure signatures for schema mismatches, credentials, flaky metrics, missing tools, sessions, and trace attributes.
- [summarize_adk_events.py](scripts/summarize_adk_events.py) — Safe stdin/file event JSON summarizer for sessions, event arrays, and trace-like dumps.
