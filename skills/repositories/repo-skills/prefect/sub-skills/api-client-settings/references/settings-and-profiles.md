# Settings and Profiles

## Core APIs

Use these imports for programmatic settings work:

```python
from prefect.settings import get_current_settings, temporary_settings
from prefect.settings import PREFECT_API_URL, PREFECT_API_KEY
```

- `get_current_settings()` returns the active `Settings` object from the current context, or creates one from the environment and configuration files when no context is active.
- `temporary_settings(...)` creates a temporary settings context and restores the previous context on exit. It does not mutate `os.environ`.
- Legacy setting objects such as `PREFECT_API_URL` expose `.value()` and can be used as keys in `temporary_settings`.
- Accessor strings also work, for example `temporary_settings(updates={"api.url": "http://127.0.0.1:4200/api"})`.

## Source Precedence

Prefect settings are Pydantic settings with custom sources. Effective values are selected in this order, highest to lowest:

1. Explicit initialization or copied settings context.
2. Environment variables such as `PREFECT_API_URL`.
3. `.env` in the current working directory.
4. File secrets when configured by Pydantic settings.
5. `prefect.toml` in the current working directory.
6. `[tool.prefect]` in `pyproject.toml`.
7. Active profile settings from profiles TOML.
8. Defaults.

When a setting is not taking effect, check for a higher-precedence source first. Environment variables always beat profile and TOML values.

## File Formats

Environment variables use uppercase names, usually with the `PREFECT_` prefix:

```bash
PREFECT_API_URL=http://127.0.0.1:4200/api
PREFECT_CLIENT_CUSTOM_HEADERS='{"X-Trace": "dev"}'
```

`prefect.toml` uses root tables and dotted setting accessors:

```toml
api.url = "http://127.0.0.1:4200/api"
logging.level = "DEBUG"

[client]
retry_extra_codes = "429,500"
```

`pyproject.toml` uses the `[tool.prefect]` table:

```toml
[tool.prefect]
api.url = "http://127.0.0.1:4200/api"
logging.level = "DEBUG"
```

Profiles TOML stores one active profile and profile sections. Profile settings are written as environment-variable names:

```toml
active = "local"

[profiles.local]
PREFECT_API_URL = "http://127.0.0.1:4200/api"
PREFECT_SERVER_ALLOW_EPHEMERAL_MODE = "false"

[profiles.cloud]
PREFECT_API_URL = "https://api.prefect.cloud/api/accounts/<account-id>/workspaces/<workspace-id>"
PREFECT_API_KEY = "<redacted>"
```

Default profiles include an `ephemeral` profile that enables `PREFECT_SERVER_ALLOW_EPHEMERAL_MODE`, a `local` profile that points at `http://127.0.0.1:4200/api`, and Cloud-oriented profile scaffolding.

## Profiles Path Resolution

The profiles path defaults to `~/.prefect/profiles.toml`, but Prefect can resolve it from several sources:

- `PREFECT_PROFILES_PATH` environment variable.
- `PREFECT_PROFILES_PATH` in `.env`.
- `profiles_path` in `prefect.toml`.
- `tool.prefect.profiles_path` in `pyproject.toml`.
- `PREFECT_HOME/profiles.toml` when `PREFECT_HOME` is set.
- Built-in default profiles when no user profiles file exists.

If test mode is enabled, profile loading intentionally avoids normal user profile paths.

## Temporary Settings Patterns

Override for one client call:

```python
from prefect import get_client
from prefect.settings import PREFECT_API_URL, temporary_settings

async def check_api(api_url: str):
    with temporary_settings(updates={PREFECT_API_URL: api_url}):
        async with get_client() as client:
            return (await client.hello()).json()
```

Set defaults without overriding existing values:

```python
from prefect.settings import PREFECT_API_URL, temporary_settings

with temporary_settings(set_defaults={PREFECT_API_URL: "http://127.0.0.1:4200/api"}):
    ...
```

Restore a setting to its default inside a nested scope:

```python
from prefect.settings import PREFECT_API_URL, temporary_settings

with temporary_settings(restore_defaults={PREFECT_API_URL}):
    assert PREFECT_API_URL.value() is None
```

Prefer `temporary_settings` in tests and reusable helpers because it is context-scoped and restores on exceptions.

## Schema and Introspection

Prefect ships `schemas/settings.schema.json`, generated from `Settings.model_json_schema(...)`, with environment-variable metadata. The bundled script `../scripts/inspect_prefect_settings.py` adapts that pattern to print a safe settings summary, list known settings, validate profiles TOML, and optionally summarize the JSON schema.

Useful programmatic checks:

```python
from prefect.settings import get_current_settings

settings = get_current_settings()
print(settings.api.url)
print(settings.profiles_path)
print(settings.to_environment_variables(exclude_unset=True))
```

Use `to_environment_variables(include_secrets=False)` when rendering diagnostics for logs or handoffs.

## Validation Checklist

- Determine whether the value is coming from environment, `.env`, TOML, profile, or default.
- For profile files, validate the TOML syntax and each setting value with `Profile.validate_settings()`.
- For nested settings, prefer accessors like `api.url`, `server.api.host`, and `client.custom_headers`.
- For JSON-like environment values such as `PREFECT_CLIENT_CUSTOM_HEADERS`, ensure the value is valid JSON and matches the expected dict type.
- For Cloud, verify the API URL shape and API key are set in the same effective context.
