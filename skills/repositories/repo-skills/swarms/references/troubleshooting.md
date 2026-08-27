# Cross-cutting troubleshooting

## Install and import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: swarms` | Package not installed in the active environment | Reinstall the package in the inspection environment and rerun a minimal import check. |
| `ImportError` from optional graph packages | `graphviz` or `rustworkx` missing | Install the optional dependency only if the requested workflow needs that backend. |
| CLI command exists but behaves oddly | Wrong environment or stale editable install | Re-run the smoke script and confirm the package version. |

## Workspace and state

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Agent memory or artifact files appear in an unexpected place | `WORKSPACE_DIR` not set | Set `WORKSPACE_DIR` to the intended workspace before running the agent. |
| Skills do not load | `skills_dir` is missing or empty | Point `skills_dir` at a folder that contains subdirectories with `SKILL.md`. |
| Artifact save fails | File path is invalid or not writable | Use a writable path and confirm the parent directory exists. |

## Provider and auth

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Authentication errors from model calls | Missing or invalid provider API key | Set the appropriate provider key for the model you selected. |
| Marketplace fetch/publish fails | `SWARMS_API_KEY` missing | Provide `SWARMS_API_KEY` before using marketplace prompts or publish flows. |
| Prompt-caching or reasoning errors on a specific provider | Parameter shape incompatible with that provider | Remove unsupported parameters or switch to a model family that accepts them. |

## Workflow selection

- Use `cli-loaders` for `--markdown-path`, `agents.yaml`, `autoswarm`, or parser issues.
- Use `multi-agent-workflows` for empty agent lists, invalid flows, router misconfiguration, or workflow loops.
- Use `tools-mcp` for `MCPManager`, auth headers, local servers, and tool schema conversion.
- Use `single-agent` for memory, skills, prompt caching, fallback models, marketplace prompts, and one-agent execution.

## Validation habits

- Prefer parser/help smoke checks before live provider calls.
- Prefer offline fake-agent workflow checks before remote LLM execution.
- Prefer local MCP server checks before remote MCP endpoints.
- Treat provider-backed examples as optional unless keys are available and the request explicitly needs live behavior.
