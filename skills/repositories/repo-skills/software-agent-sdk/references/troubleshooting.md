# Cross-Cutting Troubleshooting

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'openhands'` | The packages are not installed in the active Python environment. | Install the relevant distributions or run `make build` in a source checkout. For a package-user environment, install `openhands-sdk`, `openhands-tools`, `openhands-workspace`, and `openhands-agent-server` as needed. |
| `pip check` reports broken requirements | Mixed editable/non-editable installs or incompatible dependency upgrades. | Recreate the environment or run the repo's `make build` in a clean checkout. Avoid broad extra installs unless a selected workflow needs them. |
| Startup banner appears in scripts | `OPENHANDS_SUPPRESS_BANNER` is not set. | Set `OPENHANDS_SUPPRESS_BANNER=1` for machine-readable scripts. |
| Bedrock rejects `LLM.api_key` with invalid API-key format | LiteLLM interprets `api_key` as a Bedrock bearer token. | For IAM/SigV4 auth use AWS credentials/profile fields and do not forward `LLM.api_key`; use `AWS_BEARER_TOKEN_BEDROCK` only for Bedrock bearer-token auth. |

Run this skill's [`scripts/check_env.py`](../scripts/check_env.py) to collect import, version, tool-registry, and agent-server CLI diagnostics.

## LLM credentials and provider configuration

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `LLM_API_KEY environment variable is not set` | Examples and GitHub workflows require a model credential. | Set `LLM_API_KEY`; optionally set `LLM_MODEL` and `LLM_BASE_URL`. Do not log secret values. |
| Provider/model inference is surprising | Raw model identifiers can be ambiguous. | Accept the full model string at the SDK boundary; prefer SDK provider utilities and construct a new `LLM` when model/provider changes. |
| Token callback errors or missed async callbacks | Callback type mismatch. | Token callbacks may be sync or async; rely on the SDK callback dispatch instead of wrapping with custom event-loop hacks. |

## Agent and conversation failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Remote conversation returns before hooks actually finish | A WebSocket field-level `FINISHED` status can be a hint before server stop hooks complete. | Treat full-state snapshots as authoritative. If needed, poll REST after a delay and handle stop-hook denial by continuing the run. |
| `LLMMalformedConversationHistoryError` appears | Anthropic-style malformed tool-use/tool-result history. | Let `Agent.step()` condensation recovery handle it; distinguish from true context-window overflow in logs. |
| `asyncio.CancelledError` during interrupt | Expected cancellation propagation from `conversation.interrupt()`. | `arun()` should set status `PAUSED` and emit `InterruptEvent`; do not add per-layer interrupt APIs to frozen LLM/Agent models. |
| Project skills are missing from a local conversation | Project skill loading is lazy and tied to workspace startup. | Use `AgentContext(load_project_skills=True)` or pass explicit loaded skills; ensure the workspace points inside the intended project/repo root. |

## Tool and optional dependency failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `browser_tool_set` is registered but absent from usable tools | Chromium/browser runtime not detected or executor cannot start. | Use `is_tool_usable("browser_tool_set")` or `/server_info`; install a browser or disable browser tools. Unit coverage can mock detection. |
| Terminal/tmux behavior conflicts across concurrent runs | Shared default tmux socket location. | Set a per-process or per-test `TMUX_TMPDIR`; the agent-server defaults to an isolated temp directory when unset. |
| `ToolDefinition '<name>' is not registered` | Tool implementation module was not imported or registration is missing. | Import the implementation module, use `register_default_tools()`, or fix tool registration with the repo-development helper. |
| `file_editor` rejects a path | It expects host-native absolute paths for local filesystem writes/validation. | Use host-native absolute paths for editing; use cross-platform wire-path helpers only for remote/source syntax. |

## Agent-server and workspace failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Binding to `0.0.0.0` is refused or unsafe | No session API key is configured. | Use loopback for unauthenticated local testing, or set `SESSION_API_KEY`/`OH_SESSION_API_KEYS_0` and send `X-Session-API-Key`. |
| `/api/*` returns 503 in warm-pool mode | Deferred init is enabled and the server is still dormant or initializing. | Probe `/api/init`; call `POST /api/init` with `X-Init-API-Key` matching the bootstrap secret. Rely on status code because 503 bodies may be rewritten. |
| Secret lookup from hostless URL fails | `OH_INTERNAL_SERVER_URL` is missing or points at a wildcard bind. | The server sets this automatically on startup; wildcard binds are rewritten to loopback for local lookup. |
| Docker workspace cannot start | Docker daemon unavailable, port conflict, image pull failure, or auth/env forwarding issue. | Check Docker availability, choose another port, verify image tag, and forward session API key env vars when binding beyond loopback. |
| Apptainer workspace cannot start | Apptainer CLI unavailable or SIF/image source invalid. | Install Apptainer or use Docker/API/cloud workspace; provide exactly one of `server_image` or `sif_file`. |
| Remote git changes/diff path breaks on Windows | URL query path built from host `Path` separators. | Use slash-normalized strings for `/api/git/changes` and `/api/git/diff` `path` query parameters. |

## Repository maintenance failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Pre-commit or `uv sync --frozen` fails after dependency edits | Root `uv.lock` or `[tool.uv]` policy drift. | Run the appropriate lock/update workflow and respect root `exclude-newer` guardrails. |
| Persisted settings compatibility check fails | Settings shape changed without migration or golden fixture. | Bump the internal schema version, add a migration, and update `tests/sdk/persisted_settings_baselines/`. |
| SDK public API breakage check fails | Public `__all__` symbol/member removed or structurally changed without deprecation runway. | Add deprecation metadata with at least 5 minor releases before removal and ensure a MINOR SemVer bump for breaking changes. |
| REST OpenAPI breakage check fails | Endpoint/contract was removed or changed incompatibly. | Additive changes are preferred. Deprecated REST operations need OpenAPI `deprecated=True` and a 5-minor-release removal note before removal. |
| Example runner fails with missing `EXAMPLE_COST` | Example script did not emit the required marker. | Ensure runnable examples print `EXAMPLE_COST: ...`; use `0` for non-LLM examples. |
