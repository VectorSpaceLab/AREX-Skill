# CLI And Client Troubleshooting

## `unexpected keyword argument` On A CLI List Filter

Symptom:

```text
TypeError: list_pipeline_runs() got an unexpected keyword argument 'new_field'
```

Cause: a filter model field became a Click option through `@list_options(FilterModel)`, but the matching `Client.list_*` method signature or body was not updated.

Fix all relevant layers together:

1. Filter model: add or verify the field, type, description, sort/filter behavior, and whether it belongs in `CLI_EXCLUDE_FIELDS`.
2. Client signature: add the same keyword to the matching `Client.list_*` method.
3. Client body: pass the keyword into the filter model constructor in that method.
4. CLI command: verify it uses the intended filter model and does not accidentally forward a field that should be excluded.
5. Store/server: for relationship-backed fields, add join/query support and schema handling if the filter cannot be evaluated by existing store logic.
6. Tests: add a CLI functional test that invokes the generated option and a Client/store test for the actual filtering behavior.

Route server/store query work to `../server-and-stores/SKILL.md`; keep CLI option and Client signature changes in this sub-skill.

## Missing Server Or Local Extras

Symptoms include import errors or runtime errors when starting a local server, connecting to SQL stores, serving the dashboard, using native schedules, or running server commands.

Likely cause: base `zenml` is installed but not the narrow extra for the requested capability.

Use the smallest relevant extra:

- Local store/server development needs DB dependencies from the local extra.
- Server runtime needs server dependencies such as FastAPI, Uvicorn, auth, templates, and DB dependencies.
- OpenTelemetry server instrumentation needs the OTEL extra.
- Server streaming needs the streaming extra.
- Project templates need the templates extra.
- Cloud secret backends, connectors, and integrations need their own narrow extras.

Avoid broad dev or all-integration installs unless the task is repository maintenance and the user accepted the environment impact. CLI help and metadata-only Client usage should work with base dependencies; if they require optional extras, suspect an accidental optional import at module level.

## Auth, Login, Connect, And Environment Variable Errors

Symptoms:

- `zenml login` refuses to run while auth environment variables are set.
- 401/403 against a remote server.
- Token expires or browser/device flow fails.
- Automation works locally but fails in CI.
- The wrong project is active after login.

Checks:

1. If `ZENML_STORE_URL` and `ZENML_STORE_API_KEY` are set, do not run `zenml login`/`logout`; the client authenticates directly from those variables.
2. For human local work, use `zenml login <server-url>` or `zenml login` for Pro/device-flow selection.
3. For non-interactive OSS automation, use a service account API key via `zenml login <url> --api-key` or `ZENML_STORE_URL` plus `ZENML_STORE_API_KEY`.
4. For ZenML Pro workspace API calls, use Pro-supported PAT or organization service account credentials with the workspace URL; do not confuse the workspace URL with the Pro management API URL.
5. Use `--project NAME_OR_ID` on login when the server default project is not the desired project.
6. For TLS issues, inspect `--no-verify-ssl` and `--ssl-ca-cert`, but do not disable verification as a default recommendation.
7. Do not print API keys, tokens, or credential store contents in summaries.

## Secret Redaction And Safe Audits

Dangerous pattern: running `zenml secret get` or `Client().get_secret(...)` during a broad audit. These can expose secret values.

Safe pattern:

- Use `zenml secret list --columns=id,name,private --output=json` for CLI audits.
- Use `Client().list_secrets(...)` for programmatic audits; it returns metadata without values.
- Only use `secret get` or `Client().get_secret(...)` when the user explicitly asks to retrieve secret values.
- Redact values from logs, reports, screenshots, and final summaries.
- Treat API key creation/rotation output as one-time sensitive material.

If centralized secrets are disabled, the CLI and Client can raise a “centralized secrets management is disabled/not supported” error. Confirm server capabilities before treating it as a code bug.

## Trigger Versus Legacy Schedule Confusion

There are two scheduling command families:

- `zenml pipeline schedule ...` manages legacy pipeline schedule records.
- `zenml trigger schedule ...` manages native schedule triggers.
- `zenml trigger platform-event ...` manages platform event triggers.

Before changing code or advising a command, identify which data model and command family the user means. Native trigger work often spans CLI, Client, trigger models, server endpoints, stores, schemas, docs, and tests; route deep model/store/server parts to `../server-and-stores/SKILL.md`.

## Resource Pool Versus Resource Request Confusion

There are two related command families:

- `zenml resource-pool ...` manages pool capacity and component subject policies.
- `zenml resource-request ...` inspects queued or active resource requests.

Common mistakes:

- Passing non-integer resource values in JSON/YAML capacity, reserved, or limit fields.
- Updating a pool when the issue is a pending request or queue status.
- Changing orchestrator/step-operator scheduling behavior only in CLI without updating store/server models.

Keep pool CRUD and policy CLI/client work here; route backend scheduling, request lifecycle, store filtering, and schema/migration changes to `../server-and-stores/SKILL.md`.

## Optional Integration Imports Break CLI Help

Symptom: `zenml --help` or `python -c "from zenml_cli import cli"` fails because an optional integration SDK is missing.

Cause: a CLI module, model, flavor, or helper imported an optional integration library at module import time.

Fix:

- Move optional SDK imports inside the command/function that needs them.
- Use `typing.TYPE_CHECKING` imports for type-only references.
- Keep CLI modules dependent on ZenML core, public `Client`, shared models, and lightweight utilities.
- Do not import integration SDKs, server deployment modules, or SQL schema internals in command modules just to render help.
- Add a help-only smoke test for the affected command path.

For integration flavor design and optional dependency boundaries, route to `../stacks-and-integrations/SKILL.md`.

## Output Or Piping Looks Wrong

ZenML CLI reroutes logs to stderr and keeps structured output pipeable on stdout. If a script consumes CLI output:

- Prefer `--output=json`, `--output=yaml`, `--output=csv`, or `--output=tsv`.
- Avoid parsing Rich table output.
- Keep command status/logging separate from structured output.
- In tests, account for clean-output behavior rather than assuming all output is in one stream.

## Destructive Command Guardrails

Do not run these without explicit user intent and an appropriate environment:

- `zenml clean`, especially without confirming local/global config impact.
- `delete` commands for projects, stacks, pipelines, runs, schedules, triggers, secrets, resource pools, resource requests, tags, models, API keys, or service accounts.
- `zenml login --local --docker`, server start/stop, or blocking server commands when Docker/services are not authorized.
- Commands that mutate active project/stack/server context in a shared environment.

Prefer read-only `list`, `describe`, `--help`, and bounded Client list calls while diagnosing.

## Synthetic Cases This Sub-Skill Should Support

- A contributor adds a new `PipelineRunFilter` field and the CLI exposes it, but `Client.list_pipeline_runs` lacks the parameter and raises `unexpected keyword argument`; fix requires filter model, Client signature/body, CLI exclusion decision, store join if needed, and tests.
- A user requests a safe remote audit of projects, stacks, pipelines, runs, secrets, resource pools, resource requests, native schedule triggers, platform event triggers, tags, and models; use list commands/Client methods without leaking secret values or tokens.
