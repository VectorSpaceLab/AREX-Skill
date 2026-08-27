# Environment Variables

DisCo has its own `DISCO_*` namespace. Pi-owned variables such as
`PI_CODING_AGENT_DIR`, `PI_PACKAGE_DIR`, `PI_CACHE_RETENTION`, and
`PI_OAUTH_CALLBACK_HOST` do not configure DisCo. The CLI and RPC entry points
remove known Pi process variables before loading the runtime; the headless SDK
also filters `PI_*` values from provider auth and uses DisCo-owned paths and
OAuth flows.

Provider credentials such as `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` are not
Pi-specific and remain available. They are documented in
[Providers](providers.md#environment-variables-or-auth-file).

## Process marker

The CLI and RPC entry points set `DISCO_CODING_AGENT=true`. Child processes
inherit it and can detect that they run inside DisCo. It is not session-specific
and is not set automatically when DisCo is embedded through the SDK.

## Bash tool session environment

Commands run by the LLM-callable bash tool receive the current DisCo session
state:

| Variable | Description |
| --- | --- |
| `DISCO_SESSION_ID` | Current session ID |
| `DISCO_SESSION_FILE` | Absolute session JSONL path; unset for ephemeral sessions |
| `DISCO_PROVIDER` | Selected model provider |
| `DISCO_MODEL` | Selected model ID |
| `DISCO_REASONING_LEVEL` | Effective reasoning level: `off`, `minimal`, `low`, `medium`, `high`, `xhigh`, or `max` |

The values are resolved when each command starts. Switching model or reasoning
level therefore affects the next bash command without restarting DisCo.

```bash
printf '%s/%s\n' "$DISCO_PROVIDER" "$DISCO_MODEL"
printf 'reasoning=%s session=%s\n' "$DISCO_REASONING_LEVEL" "$DISCO_SESSION_ID"
```

These variables are injected into the LLM-callable bash tool, not user-entered
`!` or `!!` commands.

### Custom bash tools

Bash tools created with `createBashTool()` expose the session environment by
default. Injection happens before `spawnHook`, so the hook receives the values
in `ctx.env`:

```typescript
const bashTool = createBashTool(cwd, {
  spawnHook: (ctx) => ({
    ...ctx,
    env: { ...ctx.env, CI: "1" },
  }),
});
```

Disable it independently of the hook:

```typescript
const bashTool = createBashTool(cwd, {
  exposeSessionEnvironment: false,
  spawnHook: (ctx) => ctx,
});
```

When disabled, DisCo removes inherited session values so a nested process does
not receive stale metadata from its parent session.

## User configuration

| Variable | Description |
| --- | --- |
| `DISCO_CODING_AGENT_DIR` | Override the global agent directory; default `~/.disco/agent` |
| `DISCO_CODING_AGENT_SESSION_DIR` | Override session storage; `--session-dir` takes precedence |
| `DISCO_OFFLINE` | Disable startup network operations, update checks, package updates, model-catalog refresh, and install telemetry |
| `DISCO_SKIP_VERSION_CHECK` | Disable only the automatic npm registry version check |
| `DISCO_CACHE_RETENTION` | Provider prompt-cache policy: `none`, `short` (default), or `long` |
| `DISCO_OAUTH_CALLBACK_HOST` | Host interface for supported local OAuth callback servers; default `127.0.0.1` |
| `DISCO_SHARE_VIEWER_URL` | Override the base viewer URL used by `/share` |
| `DISCO_NO_SPLASH` | Disable the interactive startup animation when truthy |
| `DISCO_EXPERIMENTAL` | Enable the experimental first-run setup when set to `1` |
| `DISCO_HARDWARE_CURSOR` | Show the hardware cursor when set to `1`, unless settings override it |
| `DISCO_CLEAR_ON_SHRINK` | Clear terminal rows after content shrinks when set to `1` |
| `VISUAL`, `EDITOR` | External-editor fallback when `externalEditor` is unset |
| `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY` | Standard proxy configuration for DisCo-managed HTTP clients |

The `httpProxy` setting can populate `HTTP_PROXY` and `HTTPS_PROXY` when those
variables are not already set. See [Settings](settings.md#network).

## Telemetry and attribution

DisCo has no built-in install-telemetry endpoint.

| Variable | Description |
| --- | --- |
| `DISCO_TELEMETRY` | Force install telemetry and provider attribution headers on or off using `1`/`true`/`yes` or `0`/`false`/`no` |
| `DISCO_INSTALL_TELEMETRY_URL` | Distributor-supplied install/update version-ping endpoint; no request is sent when unset |

`enableInstallTelemetry` in settings controls the same behavior when
`DISCO_TELEMETRY` is unset. Provider attribution consists of documented client
headers sent only to providers that support attribution; it does not send a
separate telemetry request.

## Distribution overrides

These variables are intended for package distributors, controlled deployments,
and integration tests. Normal npm users do not need them.

| Variable | Description |
| --- | --- |
| `DISCO_PACKAGE_DIR` | Override the installed package root, for example in Nix/Guix stores |
| `DISCO_LATEST_VERSION_URL` | Override the npm-compatible JSON endpoint used for version checks |
| `DISCO_CHANGELOG_URL` | Add a changelog link to update notifications |
| `DISCO_MODEL_CATALOG_URL` | Enable a remote model-catalog overlay service |

By default, version checks read
`https://registry.npmjs.org/%40auto-ml-skills%2Fdisco/latest`. DisCo has no
default remote model-catalog or changelog service.

## Development diagnostics

| Variable | Description |
| --- | --- |
| `DISCO_TIMING` | Print internal timing measurements when set to `1` |
| `DISCO_STARTUP_BENCHMARK` | Run the interactive startup benchmark and suppress the splash |

Development-only proxy endpoints and credentials must be supplied to the test
process. They are not package defaults and must not be embedded in source,
documentation, or the npm tarball.
