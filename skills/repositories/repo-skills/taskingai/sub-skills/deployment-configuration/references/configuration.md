# TaskingAI configuration reference

Use this reference to audit TaskingAI deployment environment variables and service URLs. It is self-contained and should be applied to the user's current deployment files or runtime environment, not to an assumed source checkout.

## Configuration principles

- Treat `HOST_URL` as the externally reachable base URL that clients and browsers use. Include protocol and port.
- Treat `TASKINGAI_INFERENCE_URL` and `TASKINGAI_PLUGIN_URL` as backend-internal service origins. They must be reachable from the backend service network.
- Keep `AES_ENCRYPTION_KEY` consistent across backend, inference, and plugin services because encrypted credentials and service-to-service secrets must be interpreted consistently.
- Replace source example secrets before exposing a deployment.
- Choose exactly one object storage mode: `local` or `s3`.
- Do not assume a health check proves provider credentials, plugin execution, or S3 upload behavior; it proves only service readiness at the deployment layer.

## Compose-level environment checklist

| Variable | Required for | Meaning / safe value rule | Failure pattern |
| --- | --- | --- | --- |
| `AES_ENCRYPTION_KEY` | Backend, inference, plugin | 32-byte random hex-style secret in source examples; keep the same value across TaskingAI services for one deployment. | Credential decrypt/encrypt failures or inconsistent provider/plugin credential handling after rotation/mismatch. |
| `JWT_SECRET_KEY` | Backend web mode | Secret used by web/auth flows. Replace defaults before exposure. | Login/session failures or unsafe default credentials/secrets. |
| `DEFAULT_ADMIN_USERNAME`, `DEFAULT_ADMIN_PASSWORD` | Initial web/admin setup | Default console credentials for a new deployment. Replace for real deployments. | Unable to log in with expected defaults, especially if persisted database state already differs from env. |
| `HOST_URL` | Backend/web/plugin/inference public URLs | Public base URL such as `http://localhost:8080`, LAN URL, or HTTPS domain. Must match nginx/reverse-proxy port and protocol. | Console loads assets from wrong host; generated file/icon URLs are broken or point to container-local addresses. |
| `PROJECT_ID` | Backend/plugin/inference | Source examples use `taskingai`. Keep consistent across services unless the deployment intentionally namespaces data. | Files or metadata may be stored under unexpected project paths. |
| `OBJECT_STORAGE_TYPE` | Backend/plugin | Must be `local` or `s3`. | Startup exception in plugin for unsupported values; upload/file URL failures in backend/plugin. |
| `PATH_TO_VOLUME` | Backend/plugin and sometimes inference config | Local storage path or temporary path before S3 upload. In containers, use an in-container path backed by a writable mount when persistence is required. | File creation/upload failures, missing generated files after restart, or URLs that cannot be served. |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Compose database and backend `POSTGRES_URL` | Must match the database service and backend connection URL. | Backend cannot connect to database; database health check may fail if username is changed without adapting health check. |
| `REDIS_DB`, `REDIS_PASSWORD` | Compose Redis and backend `REDIS_URL` | Must match Redis command password and backend URL. | Backend cache connection/auth failures. |

## Backend service configuration

The same server image can run in API or WEB purpose.

| Variable | Required | Notes |
| --- | --- | --- |
| `MODE` | Yes | Normalized to lowercase; examples use `prod`, `dev`, or `test`. |
| `PURPOSE` | Yes | `API` for public API service, `WEB` for console-facing web service. Compose runs one of each. |
| `SERVICE_PORT` | Yes | Defaults to `8000` in source config. In Compose, backend containers listen on `8000` behind nginx. |
| `HOST_URL` | Yes | Public URL for file/image URL generation and console integration. |
| `TASKINGAI_INFERENCE_URL` | Yes | Backend-internal origin for inference service. Compose value: `http://backend-inference:8000`. Standalone host examples use a host-reachable inference port. |
| `TASKINGAI_PLUGIN_URL` | Yes | Backend-internal origin for plugin service. Compose value: `http://backend-plugin:8000`. Standalone host examples use a host-reachable plugin port. |
| `POSTGRES_URL` | Yes | Compose shape: `postgres://<user>:<password>@db:5432/<db>`. Host/dev deployments must use a host-reachable database URL. |
| `POSTGRES_MAX_CONNECTIONS` | Yes | Default source value is `10`. Increase only with database capacity planning. |
| `REDIS_URL` | No in source config, but expected for full deployment | Compose shape: `redis://:<password>@cache:6379/<db>`. |
| `AES_ENCRYPTION_KEY` | Yes | Must align with inference/plugin. |
| `JWT_SECRET_KEY` | Yes | Especially important for WEB purpose. |
| `DEFAULT_ADMIN_USERNAME`, `DEFAULT_ADMIN_PASSWORD` | Yes | Used by web/admin setup. |
| `OBJECT_STORAGE_TYPE`, `PATH_TO_VOLUME`, `PROJECT_ID` | Yes | Storage and project namespace settings. |
| `S3_ENDPOINT`, `S3_BUCKET_NAME`, `S3_ACCESS_KEY_ID`, `S3_ACCESS_KEY_SECRET`, `S3_BUCKET_PUBLIC_DOMAIN` | Required by deployment policy when `OBJECT_STORAGE_TYPE=s3` | Backend config loads these without startup-required enforcement, so validate them before runtime. |

### Backend URL validation

For each backend service instance:

1. Determine where the backend process runs: Compose network, host process, or custom orchestrator.
2. Confirm the inference/plugin URL is resolvable from that network namespace.
3. Confirm the URL is an origin, for example `http://backend-inference:8000`, not an origin plus `/v1` path.
4. Diagnose with the health path `GET <origin>/v1/health_check` from the backend network if command execution is allowed.
5. If the health path works but a functional API call fails, route object/API semantics to `../backend-api/`, provider details to `../inference-providers/`, or plugin details to `../plugin-bundles/`.

## Inference service configuration

Deployment-level knobs:

| Variable | Required | Notes |
| --- | --- | --- |
| `MODE`, `LOG_LEVEL` | Yes / operational | Examples use `PROD` and `INFO`. |
| `SERVICE_PORT` | Yes | Source standalone example uses `8002`; Compose image listens internally on `8000`. Use the actual process/container port for the deployment mode. |
| `AES_ENCRYPTION_KEY` | Yes | Must align with backend for encrypted provider credentials. |
| `ALLOWED_PROVIDERS` | Optional | Comma-separated allow-list. Leave blank to permit all configured providers. Provider list semantics belong to `../inference-providers/`. |
| Provider credential variables | Optional until provider execution is required | Examples include OpenAI, Anthropic, AWS Bedrock, Azure OpenAI, Ollama, LM Studio, LocalAI, and others. Do not treat missing keys as deployment failure unless the user's scenario requires that provider. |
| `PROXY` | Optional | Outbound proxy for provider/network calls when supported by the service. |
| `IMAGE_URL_PREFIX` / image-icon prefix behavior | Optional/version-sensitive | Source config supports image URL prefix behavior, while pinned deployment images may expect older prefix env names. Verify against the image tag when icons or provider images resolve incorrectly. |
| `PROVIDER_URL_BLACK_LIST` | Optional | Comma-separated provider URL blocklist. Semantics belong to `../inference-providers/`. |
| `PATH_TO_VOLUME` | Optional | Loaded by source config for cases that need local file paths. |

## Plugin service configuration

Deployment-level knobs:

| Variable | Required | Notes |
| --- | --- | --- |
| `MODE`, `LOG_LEVEL` | Yes / operational | Examples use `PROD` and `INFO`. |
| `SERVICE_PORT` | Yes | Source standalone example uses `8003`; Compose image listens internally on `8000`. |
| `AES_ENCRYPTION_KEY` | Yes | Must align with backend. |
| `ALLOWED_BUNDLES`, `FORBIDDEN_BUNDLES` | Optional | Comma-separated bundle allow/deny lists. Bundle semantics belong to `../plugin-bundles/`. |
| `PROJECT_ID` | Yes for storage organization | Keep consistent with backend. |
| `OBJECT_STORAGE_TYPE` | Yes | Must be `local` or `s3`; invalid values raise an exception. |
| `PATH_TO_VOLUME` | Yes | Local storage path or temporary path before S3 upload. |
| `HOST_URL` | Required for local storage | Used to build returned local file URLs. The source standalone example contains a malformed local URL shape; use a valid URL such as `http://127.0.0.1:8003` or the public proxy URL. |
| `ICON_URL_PREFIX` | Optional | Defaults to localhost with the service port if unset; set to the public base URL when icon URLs must be client-reachable. |
| `PROXY` | Optional | Outbound proxy for networked plugin calls. |
| `INCLUDE_FILE_CATEGORY_IN_STORAGE_PATH` | Optional | Defaults enabled in source config. Keep default unless migration/storage layout requires a change. |

### Plugin S3 variables

When `OBJECT_STORAGE_TYPE=s3`, plugin config requires:

- `S3_ACCESS_KEY_ID`
- `S3_ACCESS_KEY_SECRET`
- `S3_ENDPOINT`
- `S3_IMAGE_BUCKET_NAME` or a fallback `S3_BUCKET_NAME`

`S3_BUCKET_PUBLIC_DOMAIN` is loaded for public URL generation. Treat it as required for user-visible file URLs even if the startup path does not always enforce it.

## S3 audit algorithm

Use this audit whenever `OBJECT_STORAGE_TYPE=s3` appears in the user's env:

1. Confirm `OBJECT_STORAGE_TYPE` is exactly `s3` for all services expected to create or serve files.
2. Check access credentials: `S3_ACCESS_KEY_ID`, `S3_ACCESS_KEY_SECRET`.
3. Check endpoint: `S3_ENDPOINT`, including scheme.
4. Check bucket: `S3_BUCKET_NAME` for backend/Compose compatibility; `S3_IMAGE_BUCKET_NAME` or `S3_BUCKET_NAME` for plugin image outputs.
5. Check public URL domain: `S3_BUCKET_PUBLIC_DOMAIN`, because returned URLs must be accessible by the browser/client.
6. Check temporary local path: `PATH_TO_VOLUME` exists and is writable for services that create files before upload.
7. If any required value is missing, stop and report an env validation failure before trying to exercise API/plugin flows.

Minimal missing-variable message pattern:

```text
OBJECT_STORAGE_TYPE=s3 was selected, but the deployment is missing: <comma-separated variables>. Set them consistently for backend and plugin services before startup/retry.
```

## Local-storage audit algorithm

Use this audit whenever `OBJECT_STORAGE_TYPE=local` appears in the user's env:

1. Confirm `PATH_TO_VOLUME` is set for backend and plugin services.
2. In containers, confirm the in-container path is backed by a persistent, writable volume.
3. Confirm services that must share generated files use the same mounted storage or compatible serving paths.
4. Confirm `HOST_URL` is a valid public URL, not a container-local address.
5. Confirm reverse-proxy routes for generated file/icon paths reach the serving service.

## Version-sensitive env names

Source config and pinned deployment images can diverge. If an env variable appears correct but has no effect:

- Identify the exact image tag or source version running.
- Check whether the tag expects `ICON_URL_PREFIX`, `IMAGE_URL_PREFIX`, or a service-specific prefix name.
- Keep Compose manifests, env examples, and image tags from one release set instead of mixing a current source config with older pinned images.

## What not to validate here

- Provider/model schemas and provider credential semantics: route to `../inference-providers/`.
- Backend object/API request and response models: route to `../backend-api/`.
- Plugin bundle execution payloads and bundle-specific storage behavior: route to `../plugin-bundles/`.
