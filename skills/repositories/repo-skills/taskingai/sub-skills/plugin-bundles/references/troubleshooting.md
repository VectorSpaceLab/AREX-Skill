# Plugin Troubleshooting

Use this reference for TaskingAI plugin microservice problems: catalog/cache loading, schema validation, credential verification, plugin execution, and generated-image storage. If the problem is backend object lifecycle routing, use the backend API skill. If it is model-provider inference unrelated to plugins, use the inference-provider skill. If the service cannot be deployed or configured at all, use the deployment-configuration skill first and return here for plugin-specific causes.

## Quick diagnosis flow

1. **Classify the surface.** Is the failure from `/v1/bundles`, `/v1/plugins`, `/v1/execute`, `/v1/verify_credentials`, or an image URL?
2. **Check response envelope.** Top-level `status: error` means route/model/config validation failed. Top-level `status: success` with nested `data.status != 200` means the plugin handler caught a provider-style error.
3. **Confirm catalog visibility.** Missing bundles can be filtered by `ALLOWED_BUNDLES` or `FORBIDDEN_BUNDLES`.
4. **Validate schema and credentials.** Required inputs must be present and credential names must match the bundle schema exactly.
5. **Separate provider errors from storage errors.** Generated-image plugins can fail after successful provider/rendering work if local or S3 storage is misconfigured.

## Symptoms, causes, recovery steps

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| `/v1/bundles` returns fewer than 47 bundles | Startup filters are configured; bundle schema failed to load; service did not complete startup cache load. | Check whether filters intentionally limit catalog. Use [../scripts/inspect_plugin_bundles.py](../scripts/inspect_plugin_bundles.py) against a local checkout to compare static schema counts. If static count is correct but API count is low, inspect deployment config and startup logs. |
| A specific plugin is absent from `/v1/plugins?bundle_id=...` | Parent bundle filtered out; plugin schema directory/file missing; plugin id has invalid naming; cache not reloaded. | Confirm parent bundle appears. Re-run static helper to list plugin schema paths. Restart the service after schema changes. |
| `OBJECT_NOT_FOUND` for bundle or plugin | Unknown `bundle_id`/`plugin_id`, filtered bundle, or handler/cache not loaded. | Compare the payload ids to the catalog in [bundle-catalog.md](bundle-catalog.md). Remember ids use lowercase underscores, e.g. `chart_maker/make_bar_chart`. |
| `REQUEST_VALIDATION_ERROR` before handler execution | Missing route field, wrong JSON type, required plugin input missing, URL input does not start with `http`, or generated-image plugin lacks `project_id`. | Compare payload with plugin `input_schema`. For chart/QR/image-generation plugins, include `project_id` at top level, not inside `input_params`. |
| Top-level success but nested `data.status` is `500` with `data.error` | Handler raised a provider-style error; examples include divide-by-zero, chart value mismatch, provider HTTP failure, or storage upload failure. | Treat nested `data.error` as the actionable plugin/provider message. For `arithmetic/divide`, reject `number_2=0`. For chart plugins, ensure value arrays are same length. For storage plugins, use the storage sections below. |
| `credentials must be a dict` or `encrypted_credentials must be a dict` | Credential field was sent as a string/list/null instead of an object. | Send an object. Use `{}` for no-credential bundles. |
| `either credentials or encrypted_credentials is required, but not both` | Both credential forms were supplied. | Send exactly one credential form. Use `/v1/verify_credentials` to convert plaintext into encrypted credentials when needed. |
| `Failed to load default credentials ... from env` | No credentials were supplied for a credentialed bundle and required environment variables were absent. | Provide `credentials` explicitly or configure the provider credential env vars named in [bundle-catalog.md](bundle-catalog.md). |
| `invalid credentials. Not encrypted` | Plaintext was sent in `encrypted_credentials`, or encrypted value is malformed. | Use plaintext `credentials`, or first call `/v1/verify_credentials` and reuse its returned `encrypted_credentials`. |
| Credential verification returns 401 | Provider rejected credentials, provider quota is exhausted, network/proxy failed, or provider-specific verify logic hit an unsupported endpoint. | Confirm exact credential names and provider account status. Retry only if network/proxy is the likely cause. Do not treat missing credentials as a repo bug. |
| Startup/import error for a bundle/plugin handler | Dynamic class name does not match id convention or handler module import dependencies are missing. | Class names are title-cased ids: `chart_maker` -> `ChartMaker`, `make_bar_chart` -> `MakeBarChart`. Install only the required plugin dependencies for the selected capability. |
| Icon route fails | Unknown bundle id or missing icon resource. | Confirm bundle visibility first. Icons are served from the bundle's resource icon for known bundles. |
| `i18n key ... is missing` during startup | Bundle or plugin schema references an i18n key absent from a language file. | Fix or complete the i18n resource for the bundle. Catalog text can still be reasoned from schema keys, but service startup may reject incomplete resources. |

## Local image URL troubleshooting

Generated-image plugins under local storage return `HOST_URL/<generated-path>` after writing a PNG below `PATH_TO_VOLUME`.

Expected local configuration:

| Variable | Expected role |
| --- | --- |
| `OBJECT_STORAGE_TYPE` | Must be `local`. |
| `PATH_TO_VOLUME` | Writable directory used to store generated files. |
| `HOST_URL` | Public prefix used in returned URLs. Must include scheme and host in a usable form. |
| `INCLUDE_FILE_CATEGORY_IN_STORAGE_PATH` | When enabled, generated paths include `imgs/p/<project_id>/...`. |

Common local-storage symptoms:

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| Returned URL does not start with expected host | `HOST_URL` is unset, malformed, or points to an internal address not reachable by the client. | Set `HOST_URL` to the externally reachable base URL for the plugin image service. Include `http://` or `https://`. |
| URL has no `/imgs/` segment but a later image reader treats it as localhost | Generated path/category setting changed or URL was rewritten. | Keep the generated `imgs/p/...` prefix when local image readers need to map localhost URLs back to `PATH_TO_VOLUME`. |
| File URL is returned but image is 404 | `PATH_TO_VOLUME` is not shared with the HTTP-serving process, not writable, or file was written under a different generated path. | Ensure the plugin service can write to the configured volume and that the image-serving route/static setup exposes the same path convention. |
| `project_id is required` | Generated-image plugin was executed without top-level `project_id`. | Add `project_id` to the `/v1/execute` request body. Do not put it only inside `input_params`. |
| Chart plugin fails before storage | Plot input mismatch or image renderer dependency problem. | Ensure `x_values` and `y_values` lengths match. If rendering dependencies are unavailable, use arithmetic for no-storage tests or provision image-rendering dependencies. |

## S3 storage troubleshooting

Generated-image plugins under S3 storage write a temporary local file, upload it to a S3-compatible bucket, delete the local temporary file, and return a public URL.

Expected S3 configuration:

| Variable | Expected role |
| --- | --- |
| `OBJECT_STORAGE_TYPE` | Must be `s3`. |
| `S3_ACCESS_KEY_ID` | Required access key. |
| `S3_ACCESS_KEY_SECRET` | Required secret. |
| `S3_ENDPOINT` | Required S3-compatible endpoint URL. |
| `S3_IMAGE_BUCKET_NAME` | Preferred image bucket name. |
| `S3_BUCKET_NAME` | Fallback bucket name if image bucket is unset. |
| `S3_BUCKET_PUBLIC_DOMAIN` | Optional public URL prefix; if absent, returned URL uses `S3_ENDPOINT/S3_IMAGE_BUCKET_NAME`. |
| `PATH_TO_VOLUME` | Temporary local path before upload. Must still be writable. |

Common S3 symptoms:

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| Service fails during config initialization | `OBJECT_STORAGE_TYPE=s3` but access key, secret, endpoint, or bucket is missing. | Set all required S3 variables. If `S3_IMAGE_BUCKET_NAME` is absent, ensure `S3_BUCKET_NAME` is set. |
| Upload fails with provider error | Invalid endpoint, bucket, credentials, permissions, or network/proxy issue. | Verify endpoint URL, bucket existence, write permission, and network reachability. Retry only after confirming credentials and endpoint. |
| Returned S3 URL uses endpoint/bucket but should use CDN/public domain | `S3_BUCKET_PUBLIC_DOMAIN` is unset. | Set `S3_BUCKET_PUBLIC_DOMAIN` to the public domain when direct endpoint/bucket URLs are not externally readable. |
| Returned URL has duplicated or missing path segments | Public domain already includes a path, or generated path/category setting differs from expectation. | Normalize `S3_BUCKET_PUBLIC_DOMAIN` to the intended base prefix. Confirm whether category prefix inclusion is enabled. |
| Local storage works but S3 does not | Local path/rendering is healthy; failure is in S3 credentials, bucket, endpoint, or public URL. | Keep the same chart/QR payload and switch only storage variables to isolate S3. Do not blame the chart plugin until upload and returned URL rules are checked. |
| S3 works but downstream provider cannot read returned URL | Bucket object is private or public domain is not reachable by the provider. | Make the bucket/object public as intended, configure CDN/public domain, or use a signed/public URL strategy outside this plugin contract. |

## Credential troubleshooting details

Credential schemas declare only accepted names. Unknown credential keys are ignored during `load_input`, so a typo can silently become a missing credential later.

Checklist:

1. Get the bundle's credential names from [bundle-catalog.md](bundle-catalog.md) or `/v1/bundles`.
2. Send exactly those names under `credentials`.
3. For no-credential bundles, send `{}` and do not invent dummy keys.
4. Do not send plaintext values under `encrypted_credentials`.
5. Use `/v1/verify_credentials` when an encrypted credential map is required for reuse.
6. If verification calls a provider, treat network/proxy/quota failures as external blockers unless the task explicitly includes provider integration repair.

## Catalog/cache troubleshooting details

Startup loads all allowed bundle schemas before plugin schemas and dynamic handlers. A failure in early bundle loading can cascade into missing plugins.

Checklist:

- Bundle ids and plugin ids must match lowercase/underscore naming conventions.
- Bundle handler module/class must exist and follow id-to-class conversion.
- Plugin handler module/class must exist and follow plugin id-to-class conversion.
- Bundle i18n files must contain keys referenced by bundle and plugin schemas.
- `ALLOWED_BUNDLES` limits the catalog to listed ids.
- `FORBIDDEN_BUNDLES` removes listed ids from the catalog.
- Cache checksum endpoints can confirm whether a running service has reloaded expected schemas.

## Schema troubleshooting details

| Type | Accepted JSON/Python value |
| --- | --- |
| `string` | string |
| `integer` | integer |
| `number` | integer or float |
| `boolean` | boolean |
| `string_array` | list of strings |
| `integer_array` | list of integers |
| `number_array` | list of integers/floats |
| `boolean_array` | list of booleans |
| `image_url` | string beginning with `http` |
| `file_url` | string beginning with `http` |

`null` values are allowed past validation and removed before handler execution. If a handler relies on a missing optional key, it should use its own default; if it does not, expect a handler/internal error rather than a schema error.
