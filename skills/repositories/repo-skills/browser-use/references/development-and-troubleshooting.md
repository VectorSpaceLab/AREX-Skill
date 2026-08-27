# Development and Cross-Cutting Troubleshooting

Read this for issues that span multiple Browser Use sub-skills.

## Install and Import Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: browser_use` | Package not installed in active Python | Install with `uv pip install browser-use` and rerun the import check. |
| Missing `textual` for CLI/TUI | CLI extra not installed | Install `browser-use[cli]`. |
| Native beta/core binary unavailable or slow to install | `[core]` wheel unavailable, slow network, or unsupported platform | Use legacy Python `Agent` path, document the limitation, or retry `[core]` on a supported platform. |
| Browser launch fails | Chromium or system dependencies missing | Run `browser-use install` then `browser-use doctor`; for production use `Browser(use_cloud=True)`. |
| Provider API key missing | Env var not present in the running process | Set the provider env var and restart the process; prefer `BROWSER_USE_API_KEY` with `ChatBrowserUse`. |

## Cross-Sub-Skill Routing

- Agent prompts, run loops, history, callbacks: `../sub-skills/agent-programming/SKILL.md`.
- Browser/CDP/profile/domain/download/session issues: `../sub-skills/browser-control/SKILL.md`.
- Custom tools, `ActionResult`, sensitive data, file/upload/download security: `../sub-skills/tools-and-actions/SKILL.md`.
- LLM adapters, credentials, structured output, costs, fallbacks: `../sub-skills/llm-and-output/SKILL.md`.
- Terminal CLI daemon/session/profile/cloud/tunnel commands: `../sub-skills/cli-and-sessions/SKILL.md`.
- Sandbox, Cloud API, MCP, hosted skills, telemetry, external app integrations: `../sub-skills/production-integrations/SKILL.md`.

## Safe Debug Checklist

1. Confirm Python and package version with `scripts/inspect_browser_use_api.py`.
2. Confirm secrets are present without printing values.
3. Reproduce with the smallest safe import, signature, `--help`, or local HTML fixture check.
4. Avoid live websites, accounts, uploads, cloud mutations, tunnels, or profile sync unless the user approved those side effects.
5. Preserve user-selected model names; only recommend `ChatBrowserUse` when choosing a default.
6. Use `allowed_domains` and file path allowlists when credentials or local files are involved.

## Maintainer Commands

```bash
uv sync --all-extras --dev
./bin/lint.sh
./bin/test.sh
```

For focused changes, prefer a targeted `pytest` command matching the touched module before running the broad suite. Browser, cloud, and integration tests may require Chromium, network, API keys, or services.
