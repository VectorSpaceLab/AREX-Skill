# ADK Python Cross-cutting Troubleshooting

Use this root troubleshooting reference when the failure appears before a specific sub-skill route is clear. After identifying the surface, move to the nearest sub-skill troubleshooting file for deeper guidance.

## Install or Import Fails

Symptoms:

- `ModuleNotFoundError: No module named 'google.adk'`.
- `adk: command not found`.
- `python -m pip show google-adk` reports a different version than expected.

Checks:

```bash
python -c "import google.adk; print(google.adk.__version__)"
adk --help
python scripts/check_adk_install.py --json
```

Fixes:

- Install `google-adk` in the same Python environment used by the shell or tool runner.
- Ensure the environment's console-script directory is on `PATH`.
- Avoid mixing globally installed `adk` commands with a different Python interpreter.
- Use Python 3.10+.

## Optional Extra Missing

Symptoms:

- `No module named 'mcp'` for MCP toolsets.
- `DatabaseSessionService` asks for SQLAlchemy or `google-adk[db]`.
- LiteLLM, Claude, LangGraph, Docker/Kubernetes code execution, cloud storage, BigQuery, Slack, or toolbox imports fail.

Fixes:

- Treat missing extras as expected in a base install.
- Install the narrow extra needed by the task instead of `google-adk[all]` by default.
- Route toolset and auth setup to `tools-and-integrations`.
- Route persistent services and DB migration decisions to `runtime-services`.
- Route CLI eval/optimization dependencies to `evaluation-debugging` and `cli-configuration-deployment`.

## Agent Loads but Behavior Is Wrong

Symptoms:

- Agent emits raw JSON instead of calling tools.
- A sub-agent does not see parent conversation context.
- Tool errors appear as normal function responses.
- `LlmCallsLimitExceededError` or looping behavior occurs.

Routes:

- Use `agent-construction` for `output_schema`, `generate_content_config`, callbacks, `mode`, `output_key`, transfer, and branch-isolation guidance.
- Use `tools-and-integrations` for tool error callbacks, tool schemas, confirmation, long-running tools, and toolsets.
- Use `evaluation-debugging` for event JSONL, traces, and session inspection.

## CLI or Server Fails Before Agent Logic

Symptoms:

- `adk web` does not list the expected agent.
- `adk run` cannot import an app folder.
- Browser CORS, logs, or server reload problems occur.
- Deployment command fails before serving traffic.

Routes:

- Use `cli-configuration-deployment` for app discovery, `__init__.py`, `agent.py`, `root_agent`/`app`, YAML config, service URIs, server flags, and deployment command families.
- Use `runtime-services` for session/artifact/memory storage backends.
- Use `tools-and-integrations` when an import failure comes from an optional toolset or credentialed integration.

## Evaluation, Test, or Trace Failures

Symptoms:

- `adk test` JSON cases do not observe expected tool calls.
- Eval set IDs and file paths are mixed incorrectly.
- Model-backed evals are flaky or fail on credentials.
- Trace/session JSON is too noisy to interpret.

Routes:

- Use `evaluation-debugging` for eval set formats, `adk test`, `adk eval`, assertions, event fields, trace summaries, and `summarize_adk_events.py`.
- Use `agent-construction` or `tools-and-integrations` after event inspection identifies the failing agent/tool behavior.

## Repository Skill May Be Stale

Check [Repository Provenance](repo-provenance.md) against the current checkout. Refresh this skill when:

- The current commit differs from the provenance snapshot.
- Public APIs, CLI commands, config schema, optional dependency groups, docs, samples, or tests changed.
- The checkout has dirty changes affecting evidence paths beyond generated skill output.
- `google-adk` package version or entry points changed.

## Safe Stop Conditions

Ask before running commands that:

- Start long-running local servers.
- Rewrite tests or eval sets.
- Deploy, mutate, or delete cloud resources.
- Touch production databases, credentials, OAuth flows, service accounts, or private datasets.
- Install broad optional extras when a narrow extra would cover the selected workflow.
