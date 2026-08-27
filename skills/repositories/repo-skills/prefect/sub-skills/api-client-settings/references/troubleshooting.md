# Troubleshooting API Clients and Settings

## Sync/Async Mismatch

Symptoms:

- `RuntimeWarning: coroutine was never awaited`.
- `TypeError` from using `async with` on a sync client or `with` on an async client.
- Hanging or loop-related behavior when reusing clients across event loops.

Fix:

- Async code: `async with get_client() as client:` and `await client.method(...)`.
- Sync code: `with get_client(sync_client=True) as client:` and `client.method(...)`.
- Do not cache an async client across unrelated event loops; open it in the loop that uses it.

## Missing API URL or Ephemeral Assumptions

Symptoms:

- `ValueError: No Prefect API URL provided`.
- Code works locally but fails in a container or serverless function.
- `prefect-client` code tries to start local server components.

Fix:

- Set `PREFECT_API_URL` to a Prefect Cloud or self-hosted server API URL.
- For Cloud, also set `PREFECT_API_KEY`.
- If intentionally relying on ephemeral mode with the full package, confirm `PREFECT_SERVER_ALLOW_EPHEMERAL_MODE` is enabled.
- Do not rely on ephemeral server behavior from `prefect-client`; use a remote API URL.

## Cloud Authentication and URL Shape

Symptoms:

- 401/403 responses from Cloud.
- Warning that `PREFECT_API_URL` points at `app.prefect.cloud`.
- Warning about `/account/`, `/workspace/`, or missing `/api` in the URL.

Fix:

- Use `https://api.prefect.cloud/api/accounts/<account-id>/workspaces/<workspace-id>`.
- Pair the API URL with a valid `PREFECT_API_KEY` in the same effective settings context.
- Avoid logging API keys. Use `to_environment_variables(include_secrets=False)` for diagnostics.

## Setting Not Taking Effect

Symptoms:

- `PREFECT_API_URL.value()` differs from the profile or TOML file.
- A `.env` value overrides a checked-in project TOML value.
- Switching profiles appears to do nothing.

Fix:

- Check source precedence: environment variables, `.env`, `prefect.toml`, `pyproject.toml`, active profile, defaults.
- Clear higher-precedence environment variables when testing profile behavior.
- Confirm `PREFECT_PROFILES_PATH` points at the file you are editing.
- Confirm the active profile name exists in the profiles TOML.
- Run the bundled inspector with `--show-unset --validate-profiles`.

## Invalid Env Var Values

Symptoms:

- Pydantic `ValidationError` during `Settings()` construction.
- `SettingsError` from invalid JSON or type conversion.
- Custom headers ignored or rejected.

Fix:

- Booleans should be parseable values like `true` or `false`.
- Lists often use comma-separated or JSON-like forms depending on the setting; inspect the setting schema when unsure.
- `PREFECT_CLIENT_CUSTOM_HEADERS` must be a JSON object, for example `'{"X-Trace": "dev"}'`.
- Header keys and values must be strings. Protected headers such as `User-Agent`, `Prefect-Csrf-Token`, and `Prefect-Csrf-Client` cannot be overridden.

## Profile Validation Failures

Symptoms:

- `ProfileSettingsValidationError`.
- Warnings about unrecognized profile setting names.
- Active profile silently falls back to defaults.

Fix:

- Write profile keys as recognized environment-variable names, for example `PREFECT_API_URL`.
- Validate with `Profile.validate_settings()` or the bundled inspector.
- Ensure TOML syntax is valid and the file contains an `active` profile that exists under `[profiles.<name>]`.
- Remember that test mode intentionally ignores normal profile loading.

## Schema Validation and Model Construction

Symptoms:

- Client method raises a local Pydantic error before network I/O.
- Server returns 422 for a filter, action, or sort payload.
- A custom SDK generated from deployments is stale.

Fix:

- Build request payloads with `prefect.client.schemas.*` models, not free-form nested dictionaries, when practical.
- Use sort enums from `prefect.client.schemas.sorting`.
- Check `schemas/settings.schema.json` or the bundled inspector for supported settings and environment variables.
- Regenerate a custom deployment SDK after deployment, parameter schema, or work-pool job variable changes.

## `prefect-client` Missing Modules

Symptoms:

- `ModuleNotFoundError` for CLI/server modules.
- Code imports but fails when it reaches local server, database, or service functionality.
- The `prefect` command is unavailable.

Fix:

- Install the full `prefect` package when CLI or server behavior is needed.
- Keep `prefect-client` code focused on remote API calls, schemas, settings, deployment triggering, and events.
- Route CLI operations to `../cli-server-operations/SKILL.md` and server/repo internals to `../repo-development/SKILL.md`.

## Safe Diagnostic Commands

```bash
python ../scripts/inspect_prefect_settings.py --show-unset --schema-summary
```

```bash
python ../scripts/inspect_prefect_settings.py --validate-profiles --profiles-path ~/.prefect/profiles.toml
```

The inspector prints redacted settings by default and does not start a server, contact Cloud, or mutate configuration files.
