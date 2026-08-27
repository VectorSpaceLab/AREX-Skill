# Production Troubleshooting

Use this guide for Browser Use Cloud, `@sandbox`, MCP, hosted skills, profile sync, app integrations, and monitoring failures.

## API Key and Auth

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `BROWSER_USE_API_KEY environment variable is not set` | Worker/sandbox/MCP process lacks env var | Set `BROWSER_USE_API_KEY` in the exact process environment and restart. Print only whether it is present. |
| Cloud profile id rejected | Profile missing, not synced, or belongs to another account | Re-sync profile or select the correct profile id from the cloud dashboard. |
| Cloud skill says required cookie missing | Skill requires authenticated cookies | Use profile sync or perform login in a cloud browser before retrying. |

## Sandbox Failures

- If the decorated function receives no browser, confirm it is declared like `async def task(browser: Browser, ...)` and the caller does not pass `browser` manually.
- If serialization fails, remove non-serializable captured objects, open file handles, clients, and large local state from the closure.
- If no live URL is visible, add an `on_browser_created` callback and confirm cloud connectivity.
- If a run stalls, lower `max_steps`, set `cloud_timeout`, and log sanitized progress via callbacks.

## Cloud Browser Failures

- For captchas, bot detection, or slow local browsers, prefer `Browser(use_cloud=True)` and optionally a supported proxy country.
- For authenticated sites, prefer a cloud profile over entering credentials in the task prompt.
- For domain-sensitive tasks, set allowed domains in the Browser configuration and route detailed browser constraints to `../../browser-control/SKILL.md`.

## MCP Failures

| Symptom | Recovery |
| --- | --- |
| MCP command unavailable | Install a Browser Use environment with MCP dependencies and run the CLI/MCP entry point again. |
| MCP client cannot see tools | Check JSON-RPC transport wiring, process stderr logs, and that the server has started before the client initializes. |
| External MCP tool fails in Agent | Validate the external tool independently, then route action schema/security fixes to `../../tools-and-actions/SKILL.md`. |

## App Integration Failures

- Webhook timeout: acknowledge immediately and run Browser Use asynchronously.
- Duplicate browser tasks: deduplicate by event id/message id before enqueueing.
- Secret leak risk: never echo tokens/cookies; use domain-scoped secrets and sanitize logs.
- Provider rate limit: route model retry/fallback choices to `../../llm-and-output/SKILL.md`.

## When to Stop

Stop and ask the user for missing external requirements when the workflow needs private API keys, a cloud account, a login-capable profile, external app credentials, paid credits, or access to a protected site that is not available in the environment.
