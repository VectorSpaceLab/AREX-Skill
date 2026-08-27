# mcp-agent Troubleshooting

Use this reference for failures that cut across multiple mcp-agent workflows. For workflow-specific failures, continue to the nearest sub-skill troubleshooting file.

## Install and Import Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'mcp_agent'` | Package is not installed in the active Python environment. | Install with `pip install "mcp-agent"` or add it to the project with `uv add "mcp-agent"`; rerun `python -c "import mcp_agent"`. |
| Provider wrapper import fails, such as `No module named 'openai'` or `No module named 'anthropic'` | The base package is installed but the provider extra is missing. | Install the smallest needed extra, for example `mcp-agent[openai]`, `mcp-agent[anthropic]`, `mcp-agent[google]`, `mcp-agent[azure]`, `mcp-agent[bedrock]`, or `mcp-agent[cohere]`. |
| `ProviderKeyError`, authentication errors, or empty model responses | Provider SDK may be installed, but credentials/model defaults are missing or wrong. | Put API keys in `mcp_agent.secrets.yaml` or environment variables; keep non-secret default models in config. Run the core SDK checker before making network calls. |
| Temporal imports fail | Temporal is optional. | Install `mcp-agent[temporal]` and validate config with `sub-skills/durable-execution/scripts/check_temporal_config.py`. |
| LangChain, CrewAI, Redis, or provider adapter imports fail | Optional integration extra is missing. | Install only the matching extra (`[langchain]`, `[crewai]`, `[redis]`, or a provider extra). Do not install all extras just to diagnose one adapter. |

## Config and Secrets

- `mcp_agent.config.yaml` stores reusable non-secret settings. `mcp_agent.secrets.yaml`, environment variables, `.env`, or Cloud secret handles store credentials.
- Config discovery can climb parent directories and user directories. When a command sees the wrong config, pass explicit paths or run the CLI from the intended app directory.
- `MCP_APP_SETTINGS_PRELOAD` overrides disk discovery. Set `MCP_APP_SETTINGS_PRELOAD_STRICT=true` when invalid preload YAML should fail fast.
- YAML errors often come from unquoted values containing `:`, bad indentation, or environment placeholders in secrets. Validate with `mcp-agent config check` or `sub-skills/cli-cloud-operations/scripts/check_project_config.py`.
- If an `Agent` names a server that is not configured under `mcp.servers`, the failure is a config routing problem, not an LLM/provider problem.

## CLI and Cloud Safety

- Prefer `mcp-agent --help`, `mcp-agent config check`, `mcp-agent doctor`, and bundled checker scripts before mutating Cloud state.
- `mcp-agent deploy`, Cloud env changes, workflow resume/cancel, and client install writes can mutate external state. Confirm target app/server, credentials, and overwrite policy before running.
- Use `mcp-agent install ... --dry-run` to preview client configuration. Add `--force` only after checking the destination client entry.
- Use `--non-interactive` for CI deploys so missing secrets fail instead of prompting.

## MCP Server Runtime

- For `stdio` servers, validate the command exists and arguments are complete. For `sse`, `streamable_http`, and `websocket`, validate URL, headers, timeouts, and auth.
- Use `allowed_tools` to reduce tool surface before attaching an LLM to high-risk servers.
- OAuth failures often require checking authorization metadata, resource/audience values, redirect URI options, token-store backend, and whether `include_resource_parameter` matches the provider.
- Elicitation, sampling, roots, prompts, and resources require callbacks/config that match the MCP primitive being used; read the MCP server integration sub-skill before debugging provider calls.

## Workflow and Observability

- Use `LLMRouter`, not `RouterLLM`; this is a verified class-name trap.
- Parallel and orchestrator patterns multiply LLM calls. Estimate fan-out, retry, and refinement counts before production runs.
- Token counters and trace/span ids appear only when tracing/logging is configured and code runs inside `MCPApp.run()` context.
- File logs are JSONL event streams. Validate a small file with `sub-skills/observability-integrations/scripts/summarize_event_log.py` before assuming exporter failure.

## Root Helper

Run the root helper to check base imports, optional extras, selected CLI availability, and sub-skill helper visibility without network calls:

```bash
python scripts/check_mcp_agent_environment.py --json
```
