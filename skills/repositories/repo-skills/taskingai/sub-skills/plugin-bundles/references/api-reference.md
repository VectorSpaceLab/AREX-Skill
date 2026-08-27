# Plugin API Reference

This reference covers the plugin microservice surfaces owned by this sub-skill. Backend tool-instance/action persistence belongs in the sibling backend API skill. Inference-provider model execution belongs in the inference-provider skill. Deployment-wide startup and environment basics belong in the deployment-configuration skill.

## Route map

The plugin routes are registered under two prefixes:

- API prefix: `/v1`
- image prefix: `/images`

| Method | Path | Purpose | Notes |
| --- | --- | --- | --- |
| `GET` | `/v1/bundles` | List available bundles. | Applies startup bundle filters. Accepts `lang`, default `en`. |
| `GET` | `/v1/plugins` | List plugins. | Optional `bundle_id`; accepts `lang`, default `en`. |
| `POST` | `/v1/execute` | Execute one bundle/plugin. | Validates credentials, plugin existence, and input schema before handler execution. |
| `POST` | `/v1/verify_credentials` | Verify and encrypt bundle credentials. | Hidden from OpenAPI schema in source evidence but implemented as a route. |
| `GET` | `/images/plugins/bundles/icons/{bundle_id}.png` | Serve a bundle icon. | 404-style plugin error if the bundle id is unknown. |
| `GET` | `/v1/health_check` | Service health. | Internal/manage route. |
| `GET` | `/v1/version` | Service version. | Returns plugin service version. |
| `GET` | `/v1/caches` | Debug bundle/plugin/i18n cache payloads. | Internal/manage route; useful only in controlled debugging. |
| `GET` | `/v1/cache_checksums` | Debug cache checksums. | Internal/manage route. |

## Catalog listing

### `GET /v1/bundles`

Query model:

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `lang` | string | `en` | Response language for i18n text. |

Response shape:

```json
{
  "status": "success",
  "data": [
    {
      "object": "Bundle",
      "bundle_id": "arithmetic",
      "provider": "taskingai",
      "developer": "TaskingAI",
      "name": "...",
      "description": "...",
      "credentials_schema": {},
      "icon_url": "http://localhost:8000/images/plugins/bundles/icons/arithmetic.png"
    }
  ]
}
```

If a bundle is unexpectedly absent, check startup filters `ALLOWED_BUNDLES` and `FORBIDDEN_BUNDLES` before assuming the schema is missing.

### `GET /v1/plugins`

Query model:

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `bundle_id` | string or null | null | When provided, returns only plugins from that bundle. |
| `lang` | string | `en` | Response language for i18n text. |

Response shape:

```json
{
  "status": "success",
  "data": [
    {
      "object": "Plugin",
      "bundle_id": "arithmetic",
      "plugin_id": "add",
      "name": "...",
      "description": "...",
      "input_schema": {
        "number_1": {"type": "number", "name": "...", "description": "...", "required": true}
      },
      "output_schema": {
        "result": {"type": "number", "name": "...", "description": "...", "required": false}
      }
    }
  ]
}
```

## Execute a plugin

### `POST /v1/execute`

Request model:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `project_id` | string or null | no | Required by generated-image plugins even though it is optional in the route model. |
| `bundle_id` | string | yes | Bundle id, length 1-50. |
| `plugin_id` | string | yes | Plugin id, length 1-50. |
| `input_params` | object | no | Plugin-specific input dictionary; defaults to `{}`. |
| `credentials` | object | conditional | Plaintext credentials. Use `{}` for no-credential bundles. |
| `encrypted_credentials` | object | conditional | Encrypted credential map returned by credential verification. Do not send with `credentials`. |

Validation order:

1. `validate_bundle_credentials` checks `bundle_id`, confirms the bundle exists, and enforces exactly one of plaintext `credentials` or `encrypted_credentials` when credentials are supplied.
2. If plaintext credentials are supplied, only names declared by that bundle's credentials schema are copied.
3. If encrypted credentials are supplied, values are decrypted before handler execution.
4. If neither is supplied, credentials are loaded from environment variables named by the bundle credentials schema. This fails for credentialed bundles when required variables are unset. For no-credential bundles this yields an empty credential object.
5. `get_plugin` verifies the plugin id exists within the bundle.
6. `Plugin.validate_input` checks required fields and declared types.
7. Null-valued input keys are removed before handler execution.
8. The dynamic plugin handler executes and returns `PluginOutput(status=200, data={...})` unless it raises.

Successful response shape:

```json
{
  "status": "success",
  "data": {
    "status": 200,
    "data": {
      "result": 3
    }
  }
}
```

Provider-style errors raised as `TKHttpException` inside the plugin handler are wrapped into a success envelope with nested status/data:

```json
{
  "status": "success",
  "data": {
    "status": 500,
    "data": {
      "error": "provider or plugin error message"
    }
  }
}
```

Other validation and internal errors use the service error envelope described below.

### Minimal no-credential execution example

```json
{
  "bundle_id": "arithmetic",
  "plugin_id": "add",
  "input_params": {
    "number_1": 1,
    "number_2": 2
  },
  "credentials": {}
}
```

Expected nested data is `{"result": 3}`.

### Generated-image execution example

```json
{
  "bundle_id": "chart_maker",
  "plugin_id": "make_bar_chart",
  "project_id": "demo_project",
  "input_params": {
    "x_values": ["A", "B", "C"],
    "y_values": [10, 20, 30]
  },
  "credentials": {}
}
```

Expected nested data contains `url`. If it does not, diagnose storage configuration in [troubleshooting.md](troubleshooting.md).

## Verify and encrypt credentials

### `POST /v1/verify_credentials`

Request model:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `bundle_id` | string | yes | Bundle id whose credential schema should be used. |
| `credentials` | object | conditional | Plaintext credentials. |
| `encrypted_credentials` | object | conditional | Existing encrypted credential map to decrypt and validate. |

Important behavior:

- The same `validate_bundle_credentials` logic is used as `/v1/execute`.
- The service loads the dynamic bundle handler and calls its `verify(credentials)` method.
- No-credential bundle verify methods are pass-through for `arithmetic`, `chart_maker`, and `qr_code_generator` evidence.
- Credentialed bundle verify methods generally call a small provider endpoint and raise credential-validation errors when the provider response is not accepted.
- On success, plaintext credentials are encrypted with AES-CBC and returned as a comma-separated `iv,ciphertext` value per field.

Successful response shape:

```json
{
  "status": "success",
  "data": {
    "encrypted_credentials": {
      "OPENAI_API_KEY": "base64_iv,base64_ciphertext"
    }
  }
}
```

Do not log, paste, or persist plaintext credentials in skill outputs or reports. If credential verification fails, separate schema/field-name issues from provider quota/network/auth failures.

## Error envelope

Non-handler validation and internal failures use:

```json
{
  "status": "error",
  "error": {
    "code": "REQUEST_VALIDATION_ERROR",
    "message": "...",
    "debug": "optional debug in dev/test"
  }
}
```

Known error codes include:

| Code | HTTP status | Typical trigger |
| --- | ---: | --- |
| `OBJECT_NOT_FOUND` | 404 | Unknown bundle/plugin or icon bundle id. |
| `REQUEST_VALIDATION_ERROR` | 422 | Missing field, wrong type, invalid storage mode, missing `project_id` for image plugin. |
| `PROVIDER_ERROR` | 500 | Provider call failed, local image URL invalid, chart input mismatch, storage upload failure. |
| `CREDENTIALS_VALIDATION_ERROR` | 401 | Credential verify failed. |
| `INTERNAL_SERVER_ERROR` | 500 | Import/cache/config bugs or unexpected exception. |
| `TOO_MANY_REQUESTS` | 429 | Declared but not prominent in plugin source evidence. |

## Image storage contract

Generated-image plugins use a shared helper that chooses local or S3 storage from `OBJECT_STORAGE_TYPE`.

Plugins using this path:

- `chart_maker/make_2d_histogram`
- `chart_maker/make_bar_chart`
- `chart_maker/make_histogram`
- `chart_maker/make_line_chart`
- `chart_maker/make_pie_chart`
- `chart_maker/make_scatter_plot`
- `dalle_3/generate_image`
- `qr_code_generator/generate_qr_code`
- `stability_ai/generate_image`

Shared behavior:

- `project_id` is required by each generated-image plugin.
- Generated paths use `imgs/p/<project_id>/<base62-date>/pgIM<random>.png` when file-category inclusion is enabled.
- For local storage, the image is saved below `PATH_TO_VOLUME` and the returned URL is `HOST_URL/<generated-path>`.
- For S3 storage, a temporary local file is uploaded to `S3_IMAGE_BUCKET_NAME`, deleted locally, and the returned URL is `S3_BUCKET_PUBLIC_DOMAIN/<generated-path>` when public domain is set; otherwise it falls back to `S3_ENDPOINT/S3_IMAGE_BUCKET_NAME/<generated-path>`.
- `S3_IMAGE_BUCKET_NAME` falls back to `S3_BUCKET_NAME` if unset; if both are unset, config initialization fails.

Output-key caveat:

- Chart-maker, QR-code, and DALL-E plugins return `url`.
- Stability AI returns `image_url` in both schema and handler.

## Cache and startup flow

On service startup, the FastAPI lifespan handler:

1. Loads bundle schemas and i18n values.
2. Dynamically imports all bundle handler classes.
3. Loads plugin schemas for the loaded bundle ids.
4. Dynamically imports all plugin handler classes.
5. Computes i18n checksum.

Handler class names are generated from ids by title-casing underscore-separated words. For example:

- `arithmetic` -> `Arithmetic`
- `chart_maker` -> `ChartMaker`
- `make_bar_chart` -> `MakeBarChart`

If a new bundle/plugin schema exists but dynamic import fails, check the class name and module path convention before debugging API routes.
