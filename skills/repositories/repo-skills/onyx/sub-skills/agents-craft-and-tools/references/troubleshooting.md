# Troubleshooting

Use the most local signal first: chat worker state, sandbox state, or MCP auth state. Most failures are a stale config, a missing prerequisite, or a provider/tool mismatch.

| Area | Likely cause | What to check | Likely fix |
| --- | --- | --- | --- |
| Stuck chat processing | Drain loop never finished, a worker errored, cancel state was not cleared, or the processing fence stayed set | Turn/worker logs, Redis cancel state, reserved assistant message IDs, whether an `OverallStop` or partial save was emitted | Clear the cancel state, fix the upstream provider/tool error, and rerun the turn. If the request died mid-stream, confirm partial state was saved before retrying. |
| Missing LLM/provider | The selected persona/model is inaccessible, misconfigured, rate-limited, or over budget | Provider/model selection, accessible model list, cost-limit checks, and whether the LLM call is tagged with the expected `LLMFlow` | Switch to an accessible model or repair the provider config. Do not leave an untagged LLM call behind. |
| Bad tool call / forced search | The forced tool is not in the active tool set, search is disabled, or fallback tool extraction failed | Forced tool ID, search-usage state, assistant `tool_calls`, and the tool definition list | Remove the forced tool when the tool is unavailable, or adjust the prompt/tool choice so the model can emit a valid call. |
| MCP auth / OAuth failure | Bad bearer token, stale OAuth state, bad redirect URL, or SSRF blocking | `Authorization` header, `/me` auth check, OAuth state/callback, and outbound URL validation | Refresh or reconnect the credential, then correct the server URL or security setting that blocked the flow. |
| Sandbox ImagePullBackOff / DNS / env mismatch | Wrong kubectl context, sandbox image not loaded, missing env vars, or proxy/network mismatch | Current context, local sandbox image, `.env.k8s` or compose env, `SANDBOX_BACKEND`, proxy host/network, and sandbox logs | Rebuild/load the sandbox image, align the backend flag with the environment, and reconnect the local cluster/proxy plumbing. |
| Skill stale / push failure | Skills hash or MCP fingerprint changed, the session is still using old config, or managed-content push only partially landed | `reload_session_skills`, `regenerate_session_config`, `dispose_opencode_instance`, and the current sandbox/session hashes | Reload the session skills or recreate the session. Managed-content push failures are often logged rather than fatal, so stale sessions may need a manual refresh. |

## Quick guardrails

- If the failure is in generic routing, DB shape, or framework plumbing, this is probably a backend-platform task instead.
- If the failure is mostly rendered UI or client state, hand it to the frontend skill instead.
- If the problem repeats after a config reload, compare the live runtime config against the current session hashes before changing code.
