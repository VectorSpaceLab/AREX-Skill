# CLI troubleshooting

Use this guide when a CLI command, CLI edit, JSON contract, bundled skill sync, or command workflow fails. Prefer the smallest reproducer and keep secrets out of logs, terminal history, and final reports.

## Fast triage

1. Re-run the leaf command with `--help` to confirm the path and flags.
2. If the command supports JSON, reproduce with `--output json` and parse stdout with `json.loads` or `jq`.
3. For failures in JSON mode, expect empty stdout and one JSON object on stderr under `error`.
4. Run the static helper from the repository root using the bundled helper path:

   ```bash
   python <skill-dir>/scripts/check_cli_contract.py --repo-root . --output json
   ```

5. Run the focused `CliRunner` test for the command's module before broader tests.
6. If the failure followed a mutation, read current state before retrying.

## Install or import failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `observal` command not found | CLI package is not installed in the active environment. | Install the project editable or run through the project environment. Confirm `[project.scripts]` exposes `observal = "observal_cli.main:app"`. |
| `ModuleNotFoundError: loguru`, `typer`, `rich`, `yaml`, or similar while importing `observal_cli.main` | Runtime dependencies are absent from the current Python. | Use the project environment or install the package dependencies. For quick static checks, run with dependencies supplied by the environment manager. |
| Package conflict warning about `observal` vs `observal-cli` | A legacy package named `observal` is installed alongside the CLI distribution. | Uninstall the legacy package and keep `observal-cli`. |
| Import fails for shared harness registry modules | The local shared package is missing from the import path or package build. | The source-tree import path should include `packages/observal-shared`; packaged wheels must include `packages/observal-shared/observal_shared`. |
| Static helper cannot import app but bundled skill files are present | Environment problem, not necessarily a command-tree problem. | Fix dependencies first, then rerun the helper so it can list command groups. |

Expected signal after repair: importing `observal_cli.main:app` succeeds and the root command group class is `ErrorHandlingGroup`.

## CLI/API failures

| Result | Action |
| --- | --- |
| Authentication error, exit 3 | Run `observal auth whoami --output json` or `observal auth status --output json`. If not configured, log in or provide supported token environment variables. |
| Permission error, exit 4 | Report the required role or ownership. Do not retry with broader authority unless the user explicitly changes credentials. |
| Not found, exit 5 | Re-list in JSON and use the returned UUID or `qualified_name`; qualify ambiguous bare names as `namespace/slug`. |
| Conflict, exit 6 | Read the current resource and choose update, release/version bump, skip, or no-op deliberately. Do not treat conflict as transient. |
| Validation, exit 7 | Fix the named argument, enum, file shape, confirmation flag, or option combination. |
| Rate limit, exit 8 | Honor `Retry-After` for reads. Do not retry a mutation blindly. |
| Unavailable, exit 9 | Check server health, network, optional dependency, filesystem, Docker, database, or local process state. |
| Version mismatch, exit 10 | Use recovery commands under `observal self` or `observal server`; those groups are exempt from normal version enforcement. |

Shared API-backed commands should use `observal_cli.client`; it preserves server request IDs and maps HTTP failures into categorized CLI errors. If a new command raises raw `httpx` exceptions, add or route through a shared client wrapper.

## JSON mode prints Rich output or prompts

Common causes:

- `rprint`, `console.print`, a `Table`, or a spinner runs before the JSON branch returns.
- A helper emits human progress while assembling data for a JSON response.
- JSON is rendered through Rich instead of `output_json`.
- A finite command accidentally uses a streaming/log helper or prints warnings to stdout.
- JSON mode reaches an interactive prompt because required inputs were not validated first.
- A command uses a destination option named or confused with `--output`.

Fix pattern:

```python
# collect data without human output in JSON mode
if output == "json":
    output_json(result)
    return

# human-only printing below
```

For nested human helpers, pass a null reporter or capture stdout/stderr while `output == "json"`. For streams, use `output_json_line` and document that the command emits JSON Lines rather than one JSON document.

Test pattern:

- Success: invoke the command with `--output json`, assert exit code 0, parse stdout, and assert stderr is empty.
- Failure: make the shared client or validation path fail, assert stdout is empty, parse stderr as one `error` object, and assert category, exit code, operation, resource, remediation, request ID when applicable, and absence of debug detail unless `--debug` is used.

## Mutation retried unsafely

The automatic retry contract is intentionally narrow:

- `GET` may be retried on HTTP 429, 503, or 504.
- A 401 may refresh the token and retry once.
- `POST`, `PUT`, `PATCH`, and `DELETE` are not retried automatically.

If a mutation command is duplicated or a retry loop appears around `client.post`, `client.put`, `client.patch`, or `client.delete`:

1. Remove the automatic retry loop.
2. Validate all inputs before the first mutation.
3. After timeout, connection failure, 503, or 504, read current state before deciding whether to retry.
4. Use a command-family verification read: list/show by canonical identity, version history, review/request status, team membership, `scan`, file status, or server status.
5. Add a test where a transient mutation failure occurs and assert the mutation call count is one before verification.

A conflict response is not a network retry signal. It is a state decision.

## Config and local state failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| Not configured | Missing server URL or access token in effective config. | Run `observal auth login`, or set `OBSERVAL_SERVER_URL` plus one supported token variable. |
| Permission denied writing config | `~/.observal` or its files are owned by another user or not writable. | Fix ownership/permissions. Config writes should remain atomic and `0600`. |
| Config set rejects `output` or `color` | Removed persisted settings; they have no runtime consumer. | Pass `--output json` per command instead. |
| Environment override hides a saved value | Env vars take precedence for the current invocation. | Unset the environment override or change the invocation environment. |
| Alias resolves unexpectedly | Alias, row-number cache, or ambiguous bare name. | Prefer UUID or `qualified_name`; inspect aliases with `observal config aliases --output json`. |
| Legacy MCP shim migration fails at startup | An older generated MCP config cannot be safely unwrapped. | Repair or remove the affected legacy config; MCP commands and remote URLs should remain direct. |

Config output must never reveal token values or fragments.

## Optional dependency failures

`observal server migrate` commands require the optional migration dependency set, especially `pyarrow`.

Expected failure when missing:

- Category: `unavailable`.
- Exit code: 9.
- Operation: load migration tools.
- Resource: `pyarrow`.
- Remediation: install the CLI migrate extra and retry.

Migration commands read PostgreSQL and ClickHouse connection URLs from environment variables or explicit options. Do not paste credential-bearing URLs into logs, chat, examples, or issue reports. JSON results and categorized errors must not echo those URLs.

## Telemetry and harness command failures

This sub-skill owns the CLI command contract; harness internals belong to the harness-telemetry sub-skill. Still, the CLI behavior should be triaged this way:

| Command | Expected behavior |
| --- | --- |
| `observal scan --output json` | Read-only inventory. It does not patch, wrap, or rewrite MCP commands or harness files. |
| `observal doctor --output json` | Finite diagnosis. Exit 0 can contain `healthy: false`, `issues`, or `warnings`; inspect fields. |
| `observal doctor patch --all-harnesses --dry-run --output json` | Preview patch for every registered harness with no writes. |
| `observal doctor patch --harness <name> --output json` | Requires configured server URL and valid harness target. Patch is idempotent and preserves unrelated config. |
| `observal doctor cleanup --harness <name> --yes --output json` | Removes only Observal-managed artifacts. JSON cleanup requires confirmation unless dry-run. |
| `observal reconcile --dry-run --output json` | Reads recent session sources and cursor state only; does not send outbox data or update cursors. |

Failure patterns:

- Unknown harness is validation, not unexpected.
- Unsupported adapter methods should surface clearly and should not be swallowed as success.
- Malformed harness config files should fail before overwrite.
- Patch/cleanup dry-runs should leave files untouched.
- No telemetry data is not automatically a hook problem; check auth, server reachability, outbox state, then hook state.
- Do not add telemetry environment wrappers such as `OTEL_*`; Observal telemetry flows through managed hooks/extensions and reconciliation.

## Workflow result misread as success

Some commands intentionally exit zero when a check or comparison completed but the returned data still requires action.

| Command | Zero exit can still mean |
| --- | --- |
| `observal doctor --output json` | `healthy: false`, issues, warnings, missing skills, or patch not attempted. |
| `observal server status --output json` | Services may be stopped or unhealthy; status check completed. |
| `observal outdated --output json` | Items may be outdated or missing; comparison completed. |
| `observal reconcile --output json` | Sessions may be queued, rejected, skipped, or errored per item. |
| `observal agent pull --output json` | Warnings or setup commands may need follow-up; inspect `files`, `warnings`, and `setup_commands`. |
| `observal registry ... submit --output json` | Submission may be pending review, draft, skipped, or rejected by per-entry bulk result. |
| `observal ops telemetry status --output json` | Outbox may be unavailable or pending even if the command itself succeeded. |

Always inspect documented fields, not just exit status.

## Command registration or help regression

Symptoms: command missing from help, examples fail to parse, command count test fails, or bundled command reference is stale.

Fix sequence:

1. Confirm the command is added to the correct Typer app.
2. Confirm `observal_cli/main.py` wires the app into the hierarchy only if necessary.
3. Run the static helper to list top-level commands and executable count.
4. Add or update help examples on the group and leaf command.
5. If command inventory changed, intentionally update the executable-count assertion in the CLI error tests.
6. Regenerate the bundled command reference.
7. Run help-example, CLI-error, and bundled-skill tests.

## Bundled skill sync failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Missing bundled `SKILL.md` | Packaged `observal_cli/skills/<name>/SKILL.md` missing or renamed. | Restore one of the six managed skill directories or update installer inventory and tests together. |
| Stale command reference | Command tree changed but generated reference was not regenerated. | Run the sync script from the repository root and commit the updated generated block. |
| Broken skill reference link | A linked `references/*.md` file was moved or omitted. | Keep references in the same skill directory's `references/` folder and update `SKILL.md` links. |
| Skill tests fail on command flags | Fenced examples mention a long flag not present on the command leaf. | Correct the example or implement the flag; rerun help parsing tests. |
| Installed skill lacks references/scripts | Installer copied only `SKILL.md` or sync did not replace the full directory. | The installer must copy and hash the complete directory tree. |

Expected healthy signals: all six managed skill directories exist, the core generated command reference has sentinels, command examples resolve, and installer preservation tests pass.
