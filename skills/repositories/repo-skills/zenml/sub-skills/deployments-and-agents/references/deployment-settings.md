# ZenML Deployment Settings

Use this reference when configuring the ASGI application and runtime packaging for a deployed ZenML pipeline.

## Mental Model

ZenML serving has two related settings families:

- `DeploymentSettings` configures the deployed ASGI application: endpoints, docs paths, CORS, secure headers, dashboard/static files, app metadata, custom endpoints/middleware/extensions, startup/shutdown hooks, uvicorn options, and deployment service customization.
- `DockerSettings` configures how the pipeline runtime image is built or selected: requirements, package installer, parent image, build options, environment variables, stack requirements, and registry/image behavior.

Do not use `DeploymentSettings` to solve image packaging problems. Do not use `DockerSettings` to solve endpoint, middleware, CORS, auth, or dashboard routing problems.

## Minimal Deployment Settings

```python
from zenml.config import CORSConfig, DeploymentSettings

settings = DeploymentSettings(
    app_title="Fraud Scoring Service",
    app_description="Online scoring API",
    app_version="1.0.0",
    dashboard_files_path="ui",
    cors=CORSConfig(
        allow_origins=["https://app.example.com"],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["authorization", "content-type"],
        allow_credentials=True,
    ),
)
```

Attach it at pipeline level only:

```python
from zenml import pipeline

@pipeline(settings={"deployment": settings})
def scoring_pipeline(features: dict[str, float] = {}) -> dict[str, float]:
    ...
```

## Common Fields

| Field | Use |
| --- | --- |
| `app_title`, `app_description`, `app_version` | OpenAPI/UI metadata for the service. |
| `root_url_path`, `api_url_path` | Base paths when the service is mounted behind a gateway or path prefix. |
| `docs_url_path`, `redoc_url_path` | Documentation endpoints. Disable or remap for stricter production surfaces. |
| `invoke_url_path`, `submit_url_path` | Main synchronous and submit-style invocation endpoints. |
| `health_url_path`, `info_url_path`, `metrics_url_path` | Operational endpoints for health, service info, and metrics. |
| `include_default_endpoints` | Limit exposed built-in endpoints when the service should be minimal. |
| `include_default_middleware` | Choose built-in CORS and secure-headers middleware. |
| `dashboard_files_path` | Relative source-root path containing `index.html` and static assets for an embedded UI. |
| `cors` | Browser access policy for UIs and external apps. Avoid `*` with credentials in production. |
| `secure_headers` | HTTP security headers, including CSP. Tune when serving custom dashboards. |
| `thread_pool_size` | Synchronous request handling pool. Increase only with load evidence. |
| `async_execution_thread_pool_size` | Pool for async pipeline execution internals. |
| `uvicorn_host`, `uvicorn_port`, `uvicorn_workers`, `uvicorn_kwargs` | Server process configuration. Coordinate with the deployer/platform. |
| `custom_endpoints`, `custom_middlewares`, `app_extensions` | Advanced ASGI extension points. Keep handler sources importable in the deployment image. |
| `startup_hook`, `shutdown_hook` | ASGI app lifecycle hooks. Use pipeline `on_init`/`on_cleanup` when the state belongs to pipeline execution. |
| `deployment_app_runner_flavor`, `deployment_service_class` | Advanced overrides for app runner or service logic. Use only when standard settings and extensions are insufficient. |

## Endpoint and Middleware Selection

When reducing the public surface, include only endpoints needed by the service and operators. For example, a locked-down scoring service may keep invocation and health but omit docs and metrics. Use the `DeploymentDefaultEndpoints` and `DeploymentDefaultMiddleware` enum values exposed by ZenML when writing Python config.

Avoid changing endpoint paths after clients are integrated unless the user expects a breaking API change. If behind a gateway, prefer a clear `root_url_path` or `api_url_path` rather than manually baking prefixes into every endpoint.

## Dashboard and UI Files

The `dashboard_files_path` points to a directory relative to the source root. It must contain `index.html`; subdirectories can hold assets.

When serving an embedded UI:

- Keep frontend assets small and static unless the deployment image build explicitly includes a frontend build step.
- Align CORS, CSP, and external resource access. Custom dashboards that load external scripts, fonts, images, or APIs often need explicit `secure_headers.csp` changes.
- Keep UI-to-API calls same-origin when possible to avoid unnecessary credential and CORS complexity.
- Do not assume local filesystem paths in remote deployments; package files through the Docker/source-root mechanism.

## Docker Settings for Deployments

Use `DockerSettings` when the deployed pipeline needs extra Python packages, environment variables, source files, or image build behavior.

```python
from zenml.config import DockerSettings, PythonPackageInstaller

DockerSettings(
    python_package_installer=PythonPackageInstaller.UV,
    requirements="requirements.txt",
    environment={"OPENAI_API_KEY": "${OPENAI_API_KEY}"},
)
```

Guidelines:

- Prefer `requirements="requirements.txt"` or a short list of packages over broad dev extras.
- Forward provider keys through environment expansion or secret-backed stack config; never hard-code values.
- Add only packages required by online serving. Training, evaluation, notebook, and docs dependencies usually belong outside the deployment image.
- If remote execution is involved, cross-check image builder, artifact store, and registry behavior with `stacks-and-integrations`.
- Docker packaging validation does not require a Docker daemon until an actual build/deploy command runs.

## Deployer vs Model Deployer

ZenML deployers provision pipeline deployments as persistent HTTP services. They manage deployment lifecycle, URLs, status, logs, and invoke endpoints through stack components.

Model deployers are specialized stack components for external model servers. They are still relevant for integration-specific serving behavior, but pipeline deployments are the preferred general strategy for new online model and agent services. When a user asks for model serving, first decide whether a deployed inference pipeline can meet the requirements before reaching for a model deployer.

Use model deployers when the task explicitly targets an integration's model-server lifecycle, `BaseModelDeployer`, `BaseService`, service discovery, start/stop/delete behavior, or legacy serving step APIs.

## Local vs Remote Configuration

Local deployments are useful for smoke tests and demos. Remote deployments require more infrastructure.

| Concern | Local deployment | Remote/cloud deployment |
| --- | --- | --- |
| Deployer | Local or Docker deployer can be enough. | Cloud/Kubernetes/App Runner/Cloud Run deployer with credentials. |
| Artifact store | Local may work for local-only service. | Remote artifact store usually required. |
| Container registry | Often unnecessary for local process deployer. | Required when images must be pulled by remote infrastructure. |
| Image builder | May be skipped or local. | Must push images accessible to the target backend. |
| Credentials | Usually ZenML local config only. | Cloud auth, registry auth, service connectors, and secret management. |
| Network | Localhost endpoints. | Gateway/load balancer URL, firewall, TLS, auth, and observability. |

Do not promise a remote deployment can run from local-only settings. Validate stack components and credentials before deploy commands.

## Safe Settings Validation

Use the bundled validator for schema-level checks:

```bash
python scripts/validate_deployment_settings.py --example
python scripts/validate_deployment_settings.py --json deployment_settings.json
```

Accepted JSON shape:

```json
{
  "deployment": {
    "app_title": "Document Analysis Service",
    "dashboard_files_path": "ui",
    "cors": {"allow_origins": ["*"]}
  },
  "docker": {
    "requirements": "requirements.txt",
    "environment": {"OPENAI_API_KEY": "${OPENAI_API_KEY}"}
  }
}
```

The validator imports ZenML settings classes when available and instantiates them. It does not deploy, start servers, load source hooks, call providers, inspect secrets, require Docker, or validate cloud credentials.
