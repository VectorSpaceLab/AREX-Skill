# Agentic and MCP Troubleshooting

Return to [`../SKILL.md`](../SKILL.md) for safe-start guidance.

## Quick Diagnosis

Run these read-only checks first:

```bash
python sub-skills/agentic-and-mcp/scripts/check_mcp_runtime.py --profile fast-mock
python sub-skills/agentic-and-mcp/scripts/inspect_registry.py --phase P0+P0.5 --limit 5
omicverse --help
omicverse-mcp --help
ov-skill-seeker --help
```

If a command is unavailable, use the module form when possible:

```bash
python -m omicverse.mcp --help
python -m omicverse.ov_skill_seeker.cli --help
```

## MCP Extras Missing

Symptoms:

- `Error: could not start the OmicVerse MCP server.`
- Import errors for `mcp.server.stdio`, `mcp.server.fastmcp.server`, `uvicorn`, or `starlette`.
- `omicverse-mcp --transport stdio` exits before handshake.

Repair:

```bash
pip install 'omicverse[mcp]'
pip install mcp uvicorn starlette
```

Use the narrow install that matches the requested transport. `stdio` needs the MCP package; `streamable-http` also needs local HTTP serving dependencies.

## Stdio JSON-RPC Pollution

Symptoms:

- MCP client handshake fails even though the server starts.
- Client reports invalid JSON, unexpected stdout, or protocol parse errors.
- Python warnings, progress bars, logging, or `print(...)` output appear on stdout before JSON-RPC messages.

Rules:

- In `stdio` mode, stdout is reserved for MCP JSON-RPC only.
- All logging and diagnostics must go to stderr.
- Do not add `print(...)` calls to MCP startup paths unless they explicitly target stderr.
- Use `inspect_registry.py` for human-readable inspection instead of starting a stdio server manually and printing to stdout.

Useful command for manual diagnosis:

```bash
python -m omicverse.mcp --help
```

Help/version are exit-only paths and should print normal CLI output. Actual stdio server mode must not print diagnostics to stdout.

## Startup Timeout or Handshake Hangs

Symptoms:

- MCP client times out during initialization.
- First launch is slow due to registry hydration, optional imports, numba cache, or matplotlib font cache.

Repair ideas:

```bash
NUMBA_DISABLE_JIT=1 MPLCONFIGDIR=/tmp/ov-mpl NUMBA_CACHE_DIR=/tmp/ov-numba python -m omicverse.mcp --phase P0+P0.5 --transport stdio
```

Use writable cache directories appropriate for the user environment. After changing MCP client config, start a new client session; running MCP server processes do not hot-reload config.

## Phase Selection and Missing Tools

Symptoms:

- `ov.list_tools` returns fewer tools than expected.
- P0.5 analysis/visualization tools are absent.
- P2 class tools are absent.

Repair:

```bash
python sub-skills/agentic-and-mcp/scripts/inspect_registry.py --phase P0 --limit 50
python sub-skills/agentic-and-mcp/scripts/inspect_registry.py --phase P0+P0.5 --limit 50
python sub-skills/agentic-and-mcp/scripts/inspect_registry.py --phase P0+P0.5+P2 --limit 50
```

Use `P0` for core pipeline, `P0+P0.5` for default core plus analysis/visualization, and `P0+P0.5+P2` only when class tools are intentionally needed.

## Registry Hydration and Lazy Imports

Symptoms:

- Manifest build warnings about modules that could not import.
- Tool availability reports missing optional dependencies.
- A biological module import fails while the MCP manifest still builds.

Explanation:

OmicVerse lazily imports many modules. MCP manifest construction hydrates registry entries from a phase whitelist and may load leaf modules directly when package `__init__` imports heavy optional dependencies. This is expected for some optional scientific stacks.

Repair:

1. Inspect with `inspect_registry.py --warnings` to see hydration warnings.
2. Use `--search` and `--show-schema` to confirm the exact tool entry.
3. Install only the optional extra needed for the requested scientific workflow.
4. Route biological API details to the domain sub-skill named in `../SKILL.md`.

## Session, Persistence, and Quota Errors

| Error signal | Meaning | Repair |
| --- | --- | --- |
| `missing_session_object` | Handle ID is not present in this session. | Call `ov.list_handles`; rerun producing tool or restore persisted data. |
| `cross_session_access` | Handle belongs to a different `--session-id`. | Use the correct session or persist/restore into the target session. |
| `handle_not_found` | Handle ID is unknown. | Check the exact ID from the latest tool response. |
| `quota_exceeded` | Session exceeded handle limits. | Increase `--max-adata`/`--max-artifacts`, delete handles/artifacts, or start a new session. |
| `persistence_failed` | `.h5ad` or metadata write/read failed. | Confirm `--persist-dir` is writable and dependencies such as `anndata` are available. |
| `unsupported_persistence` | Attempted to persist a non-persistable handle such as a class instance. | Persist AnnData/artifacts only; recreate class instances after restart. |

Use a unique `--session-id` for multi-client use and a writable `--persist-dir` when outputs must survive process restart.

## Streamable HTTP Transport

Symptoms:

- Import errors for `uvicorn`, `starlette`, or MCP HTTP app classes.
- Port already in use.
- Server binds to a public interface unintentionally.

Repair:

```bash
python -m omicverse.mcp --transport streamable-http --host 127.0.0.1 --port 8765 --http-path /mcp
```

Keep `--host 127.0.0.1` unless the user explicitly wants network exposure. Confirm firewalls, sandbox rules, and port ownership before changing host or port.

## JARVIS, Provider, and Credential Failures

Symptoms:

- Missing API key errors from OpenAI-compatible, Gemini, Anthropic, or other providers.
- `OpenAI OAuth access token is missing chatgpt_account_id`.
- Channel bot starts but cannot send/receive messages.

Repair:

- Use environment variables or saved auth, not hard-coded secrets.
- For OpenAI API mode, set the appropriate provider variable such as `OPENAI_API_KEY`.
- For OpenAI Codex OAuth, rerun setup or use `omicverse jarvis --codex-login`.
- For Gemini CLI OAuth, use `omicverse jarvis --gemini-cli-login`.
- For Telegram, provide `TELEGRAM_BOT_TOKEN` or `--token` and optionally `--allowed-user`.
- For Discord, provide `DISCORD_BOT_TOKEN` or `--discord-token`.
- For Feishu, provide app ID/secret and connection-specific webhook/websocket settings.
- For QQ/iMessage/WeChat, confirm platform-specific permissions and required local helper tools.

Never paste API keys into generated notebooks, reports, issue comments, or skill files.

## `omicverse claw` vs Gateway Confusion

Symptoms:

- User expects a one-shot answer but a gateway/web process starts.
- User runs `omicverse claw` without tokens and sees setup or credential errors.
- Web UI import fails with missing `omicclaw`.

Rules:

- `omicverse claw` with no one-shot or daemon flags defaults to gateway mode and attempts web/channel startup.
- `omicverse claw -q "..."` is the one-shot code-generation path.
- `omicverse jarvis ...` directly controls channel bot behavior.
- `omicverse gateway ...` explicitly starts gateway daemon/web mode.
- `omicverse web` requires the optional web package (`omicclaw` or legacy fallback).

Repair examples:

```bash
omicverse claw -q "write QC code for this AnnData" --no-reflection
omicverse gateway --web-host 127.0.0.1 --web-port 5050 --no-browser
omicverse jarvis --setup
```

## Sandbox and Permission Policy

Symptoms:

- Agent refuses dynamic imports, filesystem access, package installs, or web downloads.
- Notebook execution fails and falls back unexpectedly.
- Generated code attempts restricted modules such as `subprocess` or `shutil`.

Repair:

1. Inspect the `AgentConfig.security` and `ExecutionConfig` settings.
2. Decide whether `approval_mode`, `security_level`, `auto_install_packages`, and `sandbox_fallback_policy` fit the task.
3. Ask the user before enabling downloads, external commands, package mutation, or broad filesystem access.
4. Keep `package_blocklist` and sandbox restrictions in place for untrusted prompts.

## Skill Seeker Issues

Symptoms:

- `ov-skill-seeker --validate` reports missing frontmatter or required files.
- `--create-from-link` crawls too broadly or fails on site restrictions.
- A packaged zip does not include expected assets.

Repair:

```bash
ov-skill-seeker --list
ov-skill-seeker --validate
ov-skill-seeker --package SLUG --out-dir output
ov-skill-seeker --create-from-link URL --max-pages 10 --target output
```

Use `--max-pages` to bound crawling. Validate before packaging. Prefer `--target output` when experimenting so project/user skills are not modified unexpectedly.
