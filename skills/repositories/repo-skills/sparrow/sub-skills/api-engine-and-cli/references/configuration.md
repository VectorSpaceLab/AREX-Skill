# Configuration, protected access, and database toggles

This reference explains how Sparrow's LLM API reads service configuration, validates `sparrow_key`, and decides whether database-backed logging and key validation are active.

## Configuration object behavior

The API creates one singleton config reader on import. It reads `config.properties` beside the service code; if that file is absent, the config utility creates a default file with settings and example key records.

The config helper exposes typed reads:

| Helper | Behavior |
| --- | --- |
| `get_str(section, key, default)` | string lookup with default |
| `get_int(section, key, default)` | integer conversion, falling back to default on conversion error |
| `get_float(section, key, default)` | float conversion, falling back to default on conversion error |
| `get_bool(section, key, default)` | true for `true`, `yes`, `1`, or `on`, case-insensitive |
| `get_list(section, key, default)` | comma-split string list with whitespace stripped |
| `get_sparrow_keys()` | returns key records from the `[keys]` section |
| `update_key_usage(key_name, new_count)` | persists an updated config-key usage count |

## Service settings

Important `[settings]` keys:

| Key | Meaning | Default/observed behavior |
| --- | --- | --- |
| `protected_access` | Enables API key enforcement when true. | `false` by default in the service config snapshot. |
| `use_database` | Enables Oracle database pool, logging, and database key validation when true. | `false` by default in the service config snapshot. |
| `ollama_base_url` | Ollama-compatible base URL used by related model integrations. | Local Ollama URL in the service config snapshot. |
| `llm_function` | Legacy/default LLM function setting. | Present in config, but request-time backend selection normally comes from `options`. |
| `backend_url` / `backend_options` | Defaults created by the config utility if it has to create a missing config file. | Useful for UI/default-client contexts; request form fields still override runtime inference choices. |

## Config-key format

When database use is disabled, protected access is validated against config keys. Each key record uses this pattern:

```ini
[keys]
key1_value = value1
key1_usage_count = 0
key1_usage_limit = 5
key2_value = value2
key2_usage_count = 0
key2_usage_limit = 3
```

`get_sparrow_keys()` groups entries by the prefix before `_value`, so the example above becomes two logical records: `key1` and `key2`.

## Protected-access flow

When a document or instruction API request arrives:

1. The API reads `protected_access` as a boolean.
2. If `protected_access=false`, no `sparrow_key` is required.
3. If `protected_access=true`, `sparrow_key` must be present as a form field.
4. The API reads `use_database` as a boolean.
5. If `use_database=true`, it calls the database validation function.
6. If `use_database=false`, it calls config-key validation.

### Config-key validation

Config-key validation:

- scans all configured key values;
- rejects unknown keys with HTTP `403` and `Protected access. Pipeline not allowed.`;
- checks `usage_count >= usage_limit` and rejects exceeded keys with HTTP `403`;
- increments and persists `usage_count` for accepted keys.

### Database-key validation

Database-key validation is used only when both `protected_access=true` and `use_database=true`. The database function is expected to:

- check that the key exists;
- check that the key is enabled;
- check the usage limit;
- increment usage and update last-used metadata;
- return a true/false success result.

The API maps false results to HTTP `403` with `Invalid, disabled, or usage limit exceeded for key.`

## Database logging behavior

Database support is also used for inference logging:

- On application startup, the API lifespan tries to initialize a database connection pool when `use_database=true`.
- On shutdown, it closes the pool.
- For document inference, PDF page count is estimated first and then logged with inference type `DATA_EXTRACTION`.
- For instruction inference, page count is logged as `1` with inference type `INSTRUCTION_PROCESSING`.
- After inference completes, the duration is written back when a log record exists.
- When `use_database=false`, logging and duration updates are no-ops.

## Operational guidance

- For local open testing, keep `protected_access=false` and `use_database=false`.
- For config-key protection without database infrastructure, set `protected_access=true`, keep `use_database=false`, and maintain `[keys]` usage limits.
- For database-backed protection and analytics, set both `protected_access=true` and `use_database=true`, configure the database section, and ensure the database driver and schema functions are available.
- Do not put real `sparrow_key` values in examples, logs, reports, or generated prompts. Use placeholders such as `<SPARROW_KEY>`.
- If protected access is unexpectedly rejecting requests, first check whether the API is using config-key validation or database validation; the same `sparrow_key` form field enters both flows, but the backing key store differs.
