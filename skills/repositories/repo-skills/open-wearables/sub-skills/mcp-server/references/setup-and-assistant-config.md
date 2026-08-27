# MCP Setup and Assistant Configuration

## Purpose

Read this when installing the MCP package, creating safe environment configuration, wiring Claude Desktop/Cursor/MCPJam to the server, or verifying setup without making live API calls.

## Prerequisites

| Requirement | Minimum | Notes |
| --- | --- | --- |
| Python | `>=3.13` | Required by the MCP package metadata. |
| Package manager | `uv >=0.9.17` | The documented MCP workflow uses `uv sync` and `uv run start`. |
| Backend | Running local backend or deployed Open Wearables API | The MCP server calls the backend REST API; it does not start the backend. |
| Credential | Open Wearables API key | Use a placeholder in templates and store the real key only in local secret config. |

For backend startup, seed data, API key creation endpoints, or auth behavior, use [backend-core](../../backend-core/SKILL.md). For frontend dashboard steps such as finding credential settings, use [frontend-portal](../../frontend-portal/SKILL.md).

## Install and Local Start

From an Open Wearables checkout:

```bash
cd <open-wearables-checkout>/mcp
uv sync --group code-quality --group dev
cp config/.env.example config/.env
```

Edit `config/.env` with local values, then start the server:

```bash
uv run start
```

`uv run start` launches the FastMCP stdio server. It is long-running and intended to be started by an MCP-capable assistant client after configuration. The command should log that the `open-wearables` MCP server initialized and show the configured API URL.

## Environment File Template

Keep the real `.env` local and uncommitted. Use placeholders in documentation and assistant templates:

```bash
# Required: backend API base URL, not the frontend/dashboard URL.
OPEN_WEARABLES_API_URL=http://localhost:8000

# Required for real tool calls. Replace with a real key only on the operator machine.
OPEN_WEARABLES_API_KEY=ow_REPLACE_WITH_YOUR_API_KEY

# Optional.
LOG_LEVEL=INFO
REQUEST_TIMEOUT=30
```

Configuration facts:

- `OPEN_WEARABLES_API_URL` should be the API base URL only, such as `http://localhost:8000` or `https://api.example.test`; the client appends `/api/v1/...` paths.
- `OPEN_WEARABLES_API_KEY` is read as a secret and sent as `X-Open-Wearables-API-Key`.
- Environment variables override file values through Pydantic settings, but the documented operator workflow is to keep values in `mcp/config/.env`.
- `LOG_LEVEL` should be a Python logging level such as `DEBUG`, `INFO`, `WARNING`, or `ERROR`.
- `REQUEST_TIMEOUT` should be a positive integer number of seconds.

## Safe Preflight Without Live API Calls

Use the bundled checker to validate config shape and package metadata. It does not call the backend API.

```bash
python <skill-root>/sub-skills/mcp-server/scripts/check_mcp_config.py \
  --mcp-root <open-wearables-checkout>/mcp \
  --env-file <open-wearables-checkout>/mcp/config/.env
```

Useful variants:

```bash
# Emit machine-readable output for review notes.
python <skill-root>/sub-skills/mcp-server/scripts/check_mcp_config.py \
  --mcp-root <open-wearables-checkout>/mcp \
  --json

# Fail non-zero when required live-call configuration is missing or placeholder-only.
python <skill-root>/sub-skills/mcp-server/scripts/check_mcp_config.py \
  --mcp-root <open-wearables-checkout>/mcp \
  --strict
```

Use a real live tool call only after the user authorizes credentials and confirms the backend target.

## Claude Desktop Configuration

Add an `open-wearables` server entry to Claude Desktop. The MCP package reads credentials from `mcp/config/.env`, so do not place real keys in this JSON unless a local operator explicitly chooses that secret-management style.

macOS config file: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "open-wearables": {
      "command": "uv",
      "args": [
        "run",
        "--frozen",
        "--directory",
        "/path/to/open-wearables/mcp",
        "start"
      ]
    }
  }
}
```

Windows config file: `%APPDATA%\\Claude\\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "open-wearables": {
      "command": "uv",
      "args": [
        "run",
        "--frozen",
        "--directory",
        "C:\\path\\to\\open-wearables\\mcp",
        "start"
      ]
    }
  }
}
```

After editing, restart Claude Desktop and ask: `Who can I query health data for?` A configured server should expose and call `get_users`.

## Cursor Configuration

Add this template to Cursor MCP settings:

```json
{
  "mcpServers": {
    "open-wearables": {
      "command": "uv",
      "args": [
        "run",
        "--frozen",
        "--directory",
        "/path/to/open-wearables/mcp",
        "start"
      ]
    }
  }
}
```

Restart Cursor, open the AI chat panel, and ask: `Who can I query health data for?` If Cursor cannot find `uv`, use the full path to the local `uv` executable in the `command` field.

## MCPJam Configuration

MCPJam is useful for local tool inspection before connecting a production assistant client.

```bash
npx @mcpjam/inspector@latest
```

Connection fields:

| Field | Value |
| --- | --- |
| Command | `uv` |
| Arguments | `run --frozen --directory /path/to/open-wearables/mcp start` |

Use MCPJam to list tools and perform deliberate test calls. It will still use the same `.env` file, so real calls require a backend and a valid API key.

## Development and Test Commands

Run these from the MCP package directory when working on MCP code:

```bash
# Mocked tests for API-client errors and tool envelopes.
uv run pytest -q

# Code-quality hooks when dependencies are available.
uv run pre-commit run --all-files
```

The mocked MCP tests are safe development candidates because they use HTTPX mocks and dummy keys rather than live backend credentials.

## Secret and Path Hygiene

- Use `/path/to/open-wearables/mcp`, `C:\\path\\to\\open-wearables\\mcp`, or `<open-wearables-checkout>/mcp` placeholders in shared docs.
- Do not commit real API keys, private assistant config files, or local absolute checkout paths.
- Keep the MCP package and backend package imports separated when developing in the monorepo; both expose a top-level `app` module, so run MCP commands from the MCP package directory or a clearly configured package environment.
