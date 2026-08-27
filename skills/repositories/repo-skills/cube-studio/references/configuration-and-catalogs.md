# Configuration and catalogs

## Runtime overlay model

CubeStudio's runtime configuration is not controlled by the checked-in placeholders alone. The deployment path injects real overlay files at runtime, so the generated skill should treat the overlay model as the normal operating mode.

## Cross-cutting configuration signals

### Backend and runtime

- `MYAPP_CONFIG` — Flask configuration module name
- `MYAPP_CONFIG_PATH` — optional direct config file override
- `ENVIRONMENT` — selected cluster / deployment environment
- `MYSQL_SERVICE` — database connection string
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` — Redis connection settings
- `APP_NAME` — application label
- `SECRET_KEY` — Flask session key
- `WTF_CSRF_ENABLED` — CSRF toggle
- `ENABLE_CORS`, `CORS_OPTIONS` — browser cross-origin behavior
- `RESULTS_BACKEND`, `CACHE_CONFIG` — async/cache service settings
- `PIPELINE_NAMESPACE`, `SERVICE_NAMESPACE`, `NOTEBOOK_NAMESPACE` — namespace defaults
- `SERVICE_DOMAIN`, `SERVICE_EXTERNAL_IP` — host routing defaults
- `REPOSITORY_ORG`, `PUSH_REPOSITORY_ORG` — container registry defaults

### Platform resource and catalog knobs

- `NOTEBOOK_IMAGES` — notebook image catalog
- `CRD_INFO` — runtime defaults for notebook/pipeline/service objects
- `CLUSTERS` — cluster-specific routing and host defaults
- `MODEL_URLS` — navigation targets for trained model and inference-service pages
- `HUBSECRET_NAMESPACE` — namespaces that need private image-pull credentials

## Seed catalog files

| Seed file | Main purpose |
| --- | --- |
| `myapp/init/init-project.json` | default project/group records |
| `myapp/init/init-job-template.json` | built-in job-template catalog |
| `myapp/init/init-pipeline.json` | example pipeline catalog |
| `myapp/init/init-etl-pipeline.json` | example ETL pipeline catalog |
| `myapp/init/init-service.json` | default service records |
| `myapp/init/init-inference.json` | inference-service examples |
| `myapp/init/init-train-model.json` | trained-model examples |
| `myapp/init/init-aihub.json` | AIHub card catalog |
| `myapp/init/init-chat.json` | chat scenario catalog |

## What future agents should remember

- The root placeholders are intentionally empty; the overlay files are the authoritative runtime values.
- Most UI defaults, namespace names, and routing links come from the overlay config rather than the source tree's empty placeholders.
- When a question is about notebook placement, pipeline placement, or service host routing, the answer usually depends on one of the knobs above.

## Related references

- `platform-overview.md` for the repository-wide architecture
- `troubleshooting.md` for common overlay / config / startup failures
