# Command workflows

Use this reference for day-to-day CLI operation and for modifying command behavior. The CLI is an agent-facing API: command paths, help, output, errors, exit status, docs, bundled skills, and tests are one contract.

## Default use loop

1. Identify the canonical path from this reference or by running the relevant `--help` command.
2. Prefer `--output json` whenever the command supports it.
3. Provide every required argument, option, and confirmation flag up front; JSON mode must never wait for a prompt.
4. Use UUIDs and `qualified_name` values returned by JSON. Do not automate with table row numbers or ambiguous bare names.
5. After a mutation, inspect the returned object or run the smallest read command that proves the requested state transition.
6. If a mutation times out or the transport fails after the request was sent, treat the result as unknown and read current state before retrying.
7. Report warnings, pending reviews, queued telemetry, partial setup, or health fields explicitly; a zero exit code alone may only mean that diagnosis completed.

## Command families

| Family | Main paths | Use and verification signals |
| --- | --- | --- |
| Auth and account | `observal auth login`, `logout`, `whoami`, `status`, `change-password`, `set-username` | JSON login requires complete credential inputs or SSO JSON Lines. Use password `_FILE` variables where possible. Verify identity with `whoami --output json` or health/outbox with `status --output json`. |
| Local config | `observal config show`, `set`, `path`, `alias`, `aliases` | Config files are atomically written and redacted. `config path` in table mode prints only the path; JSON includes existence. Auth fields are not set through `config set`. |
| API escape hatch | `observal api METHOD /api/v1/...` | Use only when no dedicated command exists. It rejects full URLs, query strings in the path, fragments, and traversal. Bodies come from one JSON object via `--from-file` or stdin. Output preserves raw endpoint JSON. |
| Inventory and versions | `observal scan`, `observal outdated` | `scan` is read-only and never patches harness files. `outdated` never installs; missing rows are item results, not command failures. Inspect `items`, `summary`, and `report`. |
| Telemetry recovery | `observal reconcile` | Use for missed session delivery, not routine healthy collection. `--dry-run` reads local state only. A queued session is not delivered; inspect `summary`, `targets`, and `rejections`. |
| Doctor and support | `observal doctor`, `doctor patch`, `doctor cleanup`, `doctor support bundle`, `doctor support inspect` | Diagnosis JSON exits zero when checks run, even if `healthy` is false. Patch requires `--all-harnesses` or repeated `--harness`. JSON cleanup requires `--yes` unless dry-run. Support bundles are redacted but still sensitive. |
| Registry components | `observal registry mcp|skill|hook|prompt|sandbox ...`, `registry bulk`, `registry version`, `registry models`, `registry recommend` | References accept UUIDs, `namespace/slug`, aliases, and sometimes row numbers; automation must use UUIDs or canonical names. Submit may return pending review. JSON bulk execution requires `--yes`; re-run only after inspecting per-entry results. |
| Agents | `observal agent create`, `bulk-create`, `list`, `my`, `show`, `install`, `pull`, `init`, `add`, `build`, `publish`, `release`, `versions`, lifecycle, co-authors | No-flag creation and init can be interactive; JSON requires complete flags. `pull` writes harness files and requires `--no-prompt` in JSON. Verify `files`, `warnings`, `setup_commands`, lockfile state, or `scan` after installs. |
| Teamspaces and inbox | `observal team ...`, `observal inbox ...` | Use team handles/UUIDs and item UUIDs. Public visibility can remain private with `visibility_request_status: pending`. Inbox `read` does not resolve; `read-all` mutates all filtered items. |
| Operations | `observal ops top`, `rate`, `feedback`, `traces`, `telemetry status`, `logs`, `insights ...` | Finite ops commands return one JSON document. `ops logs --follow --output json` and `ops insights generate --wait --output json` stream JSON Lines. Trace/detail failures should surface rather than silently producing partial summaries. |
| Admin | `observal admin settings`, users, SAML, SCIM, security, audit, review | Requires admin/reviewer authority as appropriate. JSON destructive commands require `--force` or `--yes`. Treat generated passwords, SCIM tokens, certificates, submitted headers, and review payloads as sensitive. |
| Server and self-management | `observal server ...`, `observal self ...`, `observal server migrate ...` | `server` and `self` are recovery commands exempt from normal server-version enforcement. JSON foreground server start/restart is invalid; use `--background`. `server migrate` requires the optional migrate extra and keeps database URLs secret. |

## Adding or changing a command

Follow this sequence for every new command, subcommand, flag, output shape, or behavior change.

### 1. Choose the existing group

- Add leaf commands to the owning `cmd_*.py` module.
- Register a new top-level group in `observal_cli/main.py` only when no existing group fits.
- Preserve canonical paths. Examples: `observal agent pull`, `observal doctor support`, `observal registry version publish`.
- If command inventory changes, update the executable-path assertion in the CLI error tests deliberately.

### 2. Help and examples

- Root, group, and leaf help screens must contain one to three examples.
- Every example starts with that screen's canonical command path.
- Examples must parse with current flags and realistic values.
- Include a JSON example when the command supports JSON.
- Dynamically generated commands such as co-author, ownership, and archive commands must show examples for the actual component type.

### 3. Output implementation

- Type the format option as `OutputMode` and default to `table`.
- Use `output_json` for JSON documents and `output_json_line` for streams.
- Put the JSON branch before human table rendering, prompts, spinners, and Rich printing.
- Dedicated list commands return `items`, `total`, `page`, and `page_size`.
- Detail and mutation commands return direct objects unless the command has a documented envelope.
- Empty JSON is still JSON; do not print a human-only empty message first.
- Do not use `--output` as a destination. Existing destination names include `--file`, `--archive`, and `--output-dir`.

### 4. Error implementation

- Use shared `client` helpers for HTTP and `fail(ErrorCategory, ...)` for local validation or filesystem failures.
- Add the enclosing function to `OPERATION_LABELS` and add a module resource label to `RESOURCE_LABELS` when needed.
- Include message, operation, resource when useful, remediation, request ID when available, and debug-only detail.
- Do not print then raise `typer.Exit` for expected failures.
- Keep tokens, passwords, auth headers, env values, DB URLs, and secret payloads out of errors and logs.

### 5. Noninteractive and side-effect safety

- Expose every input as an option or argument.
- JSON mode cannot prompt. If required input is missing, return validation exit code 7 with remediation.
- Destructive JSON commands require a documented confirmation flag such as `--yes` or `--force`.
- Multi-resource or file-writing operations should support `--dry-run` when preview is meaningful.
- Validate inputs before the first mutation whenever possible.
- Never report success before all required side effects, setup commands, and lockfile updates complete.

### 6. Docs and bundled skills

For command path, flag, output, or behavior changes, update all of the following that apply:

- The matching CLI command reference page under `docs/cli`.
- Any specialized bundled skill under `observal_cli/skills` whose workflow mentions the command.
- The generated command reference in the core bundled skill by running the sync script from the repository root.
- Static tests that assert command count, command examples, bundled skill command paths, and bundled skill flags.

Do not rely on docs alone. The bundled skills are used by agents and must describe noninteractive inputs and JSON output explicitly.

### 7. Tests and validation

Run the smallest relevant tests first, then broader checks when the change is cross-cutting.

```bash
# Static import, command tree, and bundled-skill presence check.
python <skill-dir>/scripts/check_cli_contract.py --repo-root . --output json

# Shared error contract, JSON stderr/stdout behavior, retries, and command count.
uv run pytest tests/test_cli_errors.py -q

# Help examples and component-submit flag contracts.
uv run pytest observal_cli/tests/test_cmd_component_submit_flags.py -q

# Bundled skill frontmatter, references, command paths, flags, and generated command reference.
uv run pytest tests/test_observal_skill.py tests/test_observal_skill_sync.py -q
```

Expected healthy signals:

- The static helper reports `ok: true` and `root_group_class: "ErrorHandlingGroup"`.
- JSON success output parses with `json.loads` and stdout contains no Rich markup or prompt text.
- JSON failure output leaves stdout empty and writes one object to stderr under `error`.
- `tests/test_cli_errors.py` passes; if command inventory changed, the expected executable count was intentionally updated.
- Command help examples parse without invoking callbacks.
- Bundled skill tests pass after regeneration and workflow edits.

For a domain command, add or update a focused `CliRunner` test near neighboring coverage. Mock external HTTP, subprocesses, files, and prompts; do not require Docker for unit tests.

## High-risk workflow: add a noninteractive registry command

Use this pattern for a command such as a new `observal registry <type> <action>` mutation.

1. Add the command to the component's Typer app or a shared dynamic helper if it applies to all component types.
2. Accept canonical references and resolve to UUIDs with the existing registry-reference resolver where appropriate.
3. Require complete flags in JSON mode. If the command can destroy or transfer state, require `--yes` or `--force`.
4. Call one shared `client.post`, `client.patch`, `client.put`, or `client.delete`; do not wrap it in retry loops.
5. Return the direct server object in JSON. In human mode, print only after the mutation succeeded.
6. Add or update the operation label and resource label.
7. Add tests for help examples, JSON success, table success, missing required inputs in JSON, API failure with request ID, confirmation behavior, and no retry after transient mutation failure.
8. Update the registry CLI docs and the `observal-registry` bundled skill reference. If the command tree changed, regenerate the generated command reference and run bundled skill tests.

## High-risk workflow: debug dirty JSON mode

Symptoms: `json.loads(result.stdout)` fails, a Rich table appears in JSON stdout, spinner text appears before JSON, or a JSON error also prints human output.

Checklist:

1. Confirm the command declares `output: OutputMode = typer.Option("table", "--output", "-o", ...)`.
2. Move all `rprint`, `console.print`, `spinner`, progress, table rendering, and prompts after the `if output == "json"` return.
3. If a helper prints while building a result, wrap it in a JSON-only capture or pass a quiet reporter.
4. Use `output_json` or `output_json_line`; do not render JSON through Rich.
5. Ensure failures use `fail` or shared `client` helpers so the root error boundary emits one stderr object.
6. Add a test asserting successful JSON stdout parses and failure JSON has empty stdout.

## High-risk workflow: debug unsafe mutation retry

Symptoms: duplicate creates, repeated deletes, retry loops around `client.post`, or scripts automatically rerun after a timeout.

Rules:

- Shared automatic retry is for authenticated `GET` only on HTTP 429, 503, and 504.
- Token refresh may retry once after 401 because authorization failed before the operation should be accepted.
- `POST`, `PUT`, `PATCH`, and `DELETE` are sent once. If they fail after send with timeout, connection reset, 503, or 504, server state is unknown.
- Verify with the smallest read: list or show by canonical identity, read version history, inspect request status, check archive/delete state, inspect returned files, or run `scan` for install effects.
- Treat 409 conflict as a deterministic decision point, not a transient failure.

Add tests that mock a transient mutation failure and assert no second mutation call occurs until an explicit verification read has happened.
