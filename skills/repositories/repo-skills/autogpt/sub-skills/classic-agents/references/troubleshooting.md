# Classic Troubleshooting

## Unsupported and vulnerable dependencies

Classic is unsupported and dependencies will not be updated. If a dependency vulnerability or compatibility issue appears, do not present Classic as production-ready. Either constrain the task to historical/educational use or route new work to AutoGPT Platform.

## Poetry configuration errors

Old Poetry versions may reject the project configuration or dependency groups. Upgrade Poetry in the selected environment, then retry from `classic/`. Avoid mixing Classic dependencies into the Platform backend environment.

## Missing API keys

Original AutoGPT, Forge, and benchmarks can require provider keys such as `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GROQ_API_KEY`. Do not silently switch providers to make a command run. Ask for the intended provider/model and budget before executing credentialed workflows.

## Workspace or permission denial

Inspect `.autogpt/autogpt.yaml` and `.autogpt/agents/{id}/permissions.yaml`. First match wins across agent deny, workspace deny, agent allow, workspace allow, then interactive approval. Deny rules for `.env`, keys, destructive shell commands, and paths outside the workspace should remain conservative.

## Pydantic or agent state validation error

A legacy state database or agent state file may not match the current schema. Back up the workspace first. Removing sqlite state or agent state can resolve schema issues but loses local agent history and must be explicit.

## Port 8000 is busy

Forge/server mode defaults to 8000. Stop the conflicting process or configure a different port. A port conflict is not a reason to delete the workspace or reset benchmark state.

## Benchmark state confusion

Use `direct-benchmark state` and explicit reset flags before reruns. `--fresh` clears all saved state, `--retry-failures` selects previous failures, and `--reset-strategy`, `--reset-model`, or `--reset-challenge` reset specific dimensions. Confirm report and workspace directories before deleting outputs.

## Benchmark costs or long runtime

Limit `--tests`, `--models`, `--strategies`, `--attempts`, `--parallel`, and `--timeout`. External benchmarks may download datasets or require Docker/cloud dependencies. Use list/help commands first and record budget decisions.

## Import problems after install

Confirm Python 3.12+, run from the `classic` Poetry project, and check that Poetry installed the main dependencies. If `pip check` reports a bootstrap tool mismatch, repair the isolated environment rather than changing repository source.
