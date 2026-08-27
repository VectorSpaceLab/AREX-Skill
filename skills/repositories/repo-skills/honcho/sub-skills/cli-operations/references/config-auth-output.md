# Config, Auth, And Output Semantics

Use this reference when `honcho` behavior changes with shell context, credential source, TTY/non-TTY output, or scoped flags.

## Install And Runtime Checks

```bash
uv tool install honcho-cli
honcho --version
honcho doctor --help
```

If `honcho` is not found immediately after install, open a new shell or add the `uv tool` binary directory to `PATH` according to `uv`'s install message.

The CLI package is named `honcho-cli`; the executable is `honcho`; the Python entry point is the Typer app `honcho_cli.main:app`.

## Config File Ownership

The default config file is `~/.honcho/config.json`. Set `HONCHO_CONFIG_DIR` to relocate the directory for tests, CI, or isolated profiles.

CLI-owned keys:

- `environmentUrl`: full Honcho API URL, such as `https://api.honcho.dev` or `http://localhost:8000`.
- `apiKey`: shared manual/admin JWT. The CLI writes it when using paste-key setup and reads it as fallback.
- `oauth`: CLI-owned device-flow token block with `accessToken`, `refreshToken`, `accessExpiresAt`, `clientId`, `scope`, and `host`.

Preserved foreign keys:

- `hosts`, `sessions`, `saveMessages`, `sessionStrategy`, and other sibling-tool keys are left untouched on save.

Never expect these in the config file:

- `workspace_id`, `peer_id`, or `session_id`. Scoping is runtime-only via flags or env vars.

Config saves restrict plaintext credential files to owner-only permissions on POSIX (`0600`) when possible.

## Resolution Order

For every command, values resolve in this order:

1. command/group/top-level flags,
2. `HONCHO_*` environment variables,
3. config file values,
4. default values.

Mapping:

| Setting | Flag | Env var | Config/default |
| --- | --- | --- | --- |
| API key | `honcho init --api-key` | `HONCHO_API_KEY` | `apiKey` or empty |
| Base URL | `honcho init --base-url` | `HONCHO_BASE_URL` | `environmentUrl` or `https://api.honcho.dev` |
| Workspace | `-w`, `--workspace` | `HONCHO_WORKSPACE_ID` | none |
| Peer | `-p`, `--peer` | `HONCHO_PEER_ID` | none |
| Session | `-s`, `--session` | `HONCHO_SESSION_ID` | none |
| JSON output | `--json` | `HONCHO_JSON=1`/`true` | non-TTY stdout implies JSON |
| Config dir | none | `HONCHO_CONFIG_DIR` | `~/.honcho` |

Empty `HONCHO_*` values are removed before SDK calls so the SDK can fall back cleanly.

## `honcho init` Modes

### Interactive TTY

`honcho init` prompts for a URL first, then authentication method:

- browser/device login when the server advertises the OAuth device grant;
- paste an API key;
- keep existing credentials when credentials already exist.

Device login prints a user code and verification URL, attempts to open a browser, and polls until approval, denial, expiry, timeout, interrupt, or transport error. Device tokens are host-scoped.

### Non-interactive / JSON / explicit API key

`honcho init --api-key <token> --base-url <url> --json` follows the manual-key path and does not attempt browser/device login. In JSON mode, a missing URL emits a structured `MISSING_VALUE` error and exits non-zero.

After writing config, init probes connectivity by listing workspaces. Failure is reported as `CONNECTION_FAILED` in JSON mode.

## OAuth And API Key Precedence

Credential selected for SDK calls:

1. usable, unexpired OAuth access token for the current host;
2. saved API key;
3. expired host-matching OAuth token when no API key exists, allowing the server to be final authority;
4. empty credentials.

Refresh behavior:

- Expired host-matching OAuth token with a refresh token is refreshed and persisted before reuse.
- If refresh fails but an API key exists, the CLI warns and falls back to the API key.
- If refresh fails or no refresh token exists and no API key exists, the CLI emits `SESSION_EXPIRED` and exits.
- OAuth grants bound to a different host are ignored for the current base URL; the API key can cover that host if present.

## `honcho doctor` Checklist

`honcho doctor --json` returns:

```json
{
  "checks": [
    {"check": "Config file", "ok": true, "detail": "..."},
    {"check": "Credentials configured", "ok": true, "detail": "API key"},
    {"check": "API connectivity", "ok": true, "detail": "OK"}
  ],
  "passed": 3,
  "total": 3
}
```

Additional scoped checks:

- workspace reachable when `-w` or `HONCHO_WORKSPACE_ID` is set;
- queue health after workspace reachability succeeds;
- peer exists when `-p` or `HONCHO_PEER_ID` is set.

Critical failures:

- Config file, credentials, and API connectivity are critical.
- Workspace reachability becomes critical when workspace is scoped.
- Queue endpoint unavailability is non-critical and may still be reported as OK with a note.

## Output Modes

`honcho` decides JSON mode when any of these is true:

- `--json` was passed;
- `HONCHO_JSON` is `1` or `true`;
- stdout is not a TTY.

JSON mode:

- machine data goes to stdout as formatted JSON;
- structured errors go to stderr;
- collection commands emit arrays;
- single-resource commands emit objects;
- search and conclusion results preserve full content.

Human mode:

- tables and key/value views use Rich;
- long search/conclusion content may be truncated for display;
- status/warning messages go to stderr;
- transcripts preserve newlines, literal markup-like text, full IDs when `--ids` is set, and UTC millisecond timestamps.

Known help behavior:

- `honcho <group> --help` and `honcho <group> <command> --help` are reliable scriptable help surfaces.
- The top-level `honcho` welcome is designed for interactive display. If top-level `honcho --help` is blank in a non-TTY context, use group-level help or the bundled docs generator.

## Structured Error Shape

JSON errors are emitted on stderr:

```json
{
  "error": {
    "code": "NO_WORKSPACE",
    "message": "No workspace scoped. Pass --workspace/-w or set HONCHO_WORKSPACE_ID.",
    "details": {"workspace": "..."}
  }
}
```

Common codes:

| Code | Meaning |
| --- | --- |
| `NO_WORKSPACE` | Workspace-scoped command has no workspace. |
| `NO_PEER` | Peer-scoped command has no peer. |
| `NO_SESSION` | Session command has no session. |
| `NO_SCOPE` | Both workspace and peer are missing for peer/conclusion flows. |
| `INVALID_ID` / `EMPTY_ID` | ID validation failed before API call. |
| `INVALID_JSON` | Metadata or data argument was not valid JSON. |
| `INVALID_FLAGS` | Mutually exclusive or out-of-range flags, usually before API call. |
| `INVALID_REASONING` | `peer chat --reasoning` was outside `minimal`, `low`, `medium`, `high`, `max`. |
| `<RESOURCE>_NOT_FOUND` | SDK returned not found for the named resource. |
| `AUTH_ERROR` | Authentication failure. |
| `PERMISSION_ERROR` | Authenticated but not authorized. |
| `SERVER_ERROR` | SDK server-side error. |
| `API_ERROR` | Other typed API error with status. |
| `CONNECTION_FAILED` | `init` connectivity probe failed. |
| `SESSION_EXPIRED` | OAuth session could not be refreshed and no API key fallback exists. |

## Exit Codes

Pinned behavior from tests and error handling:

- `0`: success.
- `1`: client/input/resource error, including invalid flags, invalid JSON, missing scope, not found, unknown non-SDK error.
- `2`: server error.
- `3`: auth or permission error.

Use both the exit code and the JSON stderr body when automating recovery.

## ID Validation Rules

The CLI fails before network calls for:

- empty IDs;
- `?`, `#`, `%`;
- `/` or `\\`;
- ASCII control characters and DEL;
- any `..` substring.

Spaces and shell metacharacters are not rejected by ID validation; continuation hints shell-quote them. When scripting, quote all user-provided IDs anyway.
