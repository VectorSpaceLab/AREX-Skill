# Configuration and project overlay reference

CubeStudio's backend source is intentionally incomplete without runtime overlay
files. This reference describes where settings live, which values matter for
backend operation, and how to make safe changes.

## The critical placeholder-vs-overlay rule

The checked-out `myapp/config.py` and `myapp/project.py` are empty placeholders.
They are not the effective application configuration used by Docker or
Kubernetes.

Runtime overlays provide the real files:

| Runtime | Config source | Runtime mount or destination | Notes |
| --- | --- | --- | --- |
| Docker Compose | `install/docker/config.py` | `/home/myapp/myapp/config.py` | Mounted by Compose together with `project.py` and `entrypoint.sh`. |
| Docker Compose | `install/docker/project.py` | `/home/myapp/myapp/project.py` | Defines `Myauthdbview` and organization-specific hooks. |
| Kubernetes | `install/kubernetes/cube/overlays/config/config.py` | ConfigMap key mounted to `/home/myapp/myapp/config.py` | Mostly matches Docker config; Kubernetes overlay comments out the local debug `HOST` line. |
| Kubernetes | `install/kubernetes/cube/overlays/config/project.py` | ConfigMap key mounted to `/home/myapp/myapp/project.py` | Same role as Docker project overlay. |
| Kubernetes/Docker | overlay `entrypoint.sh` | `/entrypoint.sh` | Performs DB creation, migrations, admin/init, frontend build stage, and server start. |

Backend import behavior:

- `MYAPP_CONFIG` defaults to `myapp.config` in `myapp/__init__.py`.
- The real overlay normally replaces the empty `myapp/config.py` module path.
- `CONFIG_PATH_ENV_VAR = "MYAPP_CONFIG_PATH"` lets the overlay import an extra
  local config file and copy uppercase attributes into the module, but the
  overlay module itself still must be importable first.
- `myapp/security.py` imports `Myauthdbview` from `myapp.project`; without a real
  `project.py` overlay, auth import fails.

## Minimum runtime environment variables

| Variable | Used for | Default or behavior | Operator notes |
| --- | --- | --- | --- |
| `STAGE` | Entrypoint branch | `build`, `dev`, `prod`, or fallback help | `build` runs frontend install/build commands; `dev` runs `check_tables.py` then `run.py`; `prod` runs `check_tables.py` then gunicorn. |
| `FLASK_APP` | Flask CLI target | Entrypoint sets `myapp:app` | Needed for `myapp db ...`, `myapp fab ...`, `myapp init`. |
| `MYSQL_SERVICE` | SQLAlchemy URI and DB creation | Empty by default | Live runtime expects a MySQL URI such as `mysql+pymysql://.../kubeflow?charset=utf8mb4`. |
| `REDIS_HOST`/`REDIS_PORT`/`REDIS_PASSWORD` | Cache, Celery broker/result, socket queue | host `127.0.0.1`, port `6379`, password `admin` | Set consistently for backend, worker, schedule, and watcher pods/containers. |
| `ENVIRONMENT` | Cluster selection | Defaults to `DEV`, lowercased to `dev` | Must match a key in `CLUSTERS`; watchers exit if it does not. |
| `KUBECONFIG` | Fallback cluster credentials | Used by watchers if cluster config path is absent | Kubernetes pods usually rely on mounted config or in-cluster config. |
| `MYAPP_HOME` | Runtime data dir | `~/.myapp` when unset | Avoid leaking local paths into reusable docs or generated skills. |

## Important config groups

| Group | Keys and behavior |
| --- | --- |
| App/FAB | `APP_NAME="CubeStudio"`, `APP_THEME`, `FAB_STATIC_FOLDER`, `FAB_UPDATE_PERMS`, `FAB_API_MAX_PAGE_SIZE`, `SILENCE_FAB`, `HTTP_HEADERS`, `ENABLE_CORS`, `WTF_CSRF_ENABLED`. |
| Auth/RBAC | `AUTH_TYPE=AUTH_DB`, `AUTH_USER_REGISTRATION`, `AUTH_USER_REGISTRATION_ROLE="Gamma"`, `AUTH_HEADER_NAME="Authorization"`, `JWT_PASSWORD`, `AUTH_PLATFORM_ACCESS`, `COOKIE_DOMAIN`, `CUSTOM_SECURITY_MANAGER`. |
| DB | `SQLALCHEMY_DATABASE_URI=os.getenv("MYSQL_SERVICE", "")`, pool size/recycle/max overflow, `SQLALCHEMY_BINDS`. These defaults are tuned for MySQL, not SQLite. |
| Redis/cache/Celery | `CACHE_CONFIG`, `SOCKETIO_MESSAGE_QUEUE`, `CeleryConfig.broker_url`, `result_backend`, task annotations, and beat schedule all derive from Redis env vars. |
| Namespaces | `PIPELINE_NAMESPACE`, `SERVICE_PIPELINE_NAMESPACE`, `AUTOML_NAMESPACE`, `NOTEBOOK_NAMESPACE`, `SERVICE_NAMESPACE`, `AIHUB_NAMESPACE`, `HUBSECRET_NAMESPACE`. |
| Images/registry | `REPOSITORY_ORG`, `PUSH_REPOSITORY_ORG`, `USER_IMAGE`, `NOTEBOOK_IMAGES`, `NNI_IMAGES`, `INFERNENCE_IMAGES`, `CONTAINER_CLI`, Docker/nerdctl socket settings, `IMAGE_PULL_POLICY`. Route detailed image catalog work to `compute-notebooks-and-images` or `serving-aihub-and-llm`. |
| Kubernetes | `CRD_INFO`, `CLUSTERS`, `K8S_DASHBOARD_*`, `K8S_NETWORK_MODE`, `SERVICE_DOMAIN`, `HOST`, `SERVICE_EXTERNAL_IP`, `HOSTALIASES`. Route raw cluster operations to `deploy-and-operate`. |
| Storage/monitoring | `WORKSPACE_HOST_PATH`, `ARCHIVES_HOST_PATH`, `DATASET_SAVEPATH`, `STORE_CONFIG`, `PROMETHEUS`, `GRAFANA_*_PATH`, `CHECK_WORKSPACE_SIZE`, `DELETE_OLD_DATA`. |
| Frontend routing | `MODEL_URLS` maps backend model names to SPA paths under `/frontend/...`. Update it when a shared model route needs a frontend entry. |
| Extension hooks | `BLUEPRINTS`, `ADDITIONAL_MIDDLEWARE`, `FLASK_APP_MUTATOR`, `GET_FEATURE_FLAGS_FUNC`, `HELP_URL`, project hook functions in `project.py`. |

Installed inspection with a runtime overlay observed `APP_NAME=CubeStudio`,
`ENVIRONMENT=dev`, namespaces `pipeline`/`jupyter`/`service`,
`REPOSITORY_ORG=ccr.ccs.tencentyun.com/cube-studio/`,
`SERVICE_DOMAIN=service.svc.cluster.local`, and 684 Flask routes.

## Safe overlay change workflow

1. Identify the target runtime.
   - Docker Compose: edit `install/docker/config.py` and/or `project.py` before
     starting containers.
   - Kubernetes: edit the overlay under `install/kubernetes/cube/overlays/config/`
     and let the deployment mechanism rebuild/mount the ConfigMap.
   - Temporary static inspection: create a separate importable inspection module
     rather than mutating placeholders.
2. Keep secrets out of committed config. Use environment variables or cluster
   secrets for DB passwords, Redis passwords, registry credentials, provider
   tokens, and organization-specific messaging hooks.
3. Keep root placeholders empty unless the repository's deployment design has
   intentionally changed. Editing only the placeholders usually has no effect in
   real containers/pods because the overlays replace them.
4. Check that `ENVIRONMENT.lower()` exists in `CLUSTERS`. A mismatch causes
   watchers and Kubernetes helper code to exit or select the wrong service
   domain/kubeconfig.
5. If using SQLite for a private inspection harness, remove MySQL-specific pool
   options from the temporary config. The shipped overlay's pool settings are
   for MySQL and can break SQLite engine creation.
6. After adding backend routes or changing model schemas, run the runtime DB
   order from `backend-lifecycle.md`: create DB if needed, migrate/upgrade,
   create admin if needed, then `myapp init` for permissions and seed data.

## Project overlay customization points

The runtime `project.py` overlay is the intended organization-specific hook
surface.

- `Myauthdbview` customizes `/login/api/`, `/login/`, and `/logout`.
- `push_resource_apply`, `push_resource_approve`, `push_admin`, and
  `push_message` are no-op hooks by default and can be wired to approval
  systems, chat, email, or incident tools.
- The login flow validates lowercase username shape, checks hashed or plaintext
  password, can auto-create missing users, adds the default role, logs a login
  event, and prepares a user workspace.

When changing these hooks, maintain the imports expected by `myapp/security.py`
and keep the `Myauthdbview` class name unless you also change the security
manager binding.
