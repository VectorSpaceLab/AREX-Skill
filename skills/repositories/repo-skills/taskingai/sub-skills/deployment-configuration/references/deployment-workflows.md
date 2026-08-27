# TaskingAI deployment workflows

This reference summarizes the self-hosted deployment topology and operational decisions that a future agent can use without reading the original repository. Use it with [configuration](configuration.md) and [troubleshooting](troubleshooting.md).

## Deployment modes

| Mode | Use when | Key decisions | Avoid when |
| --- | --- | --- | --- |
| Full Compose stack | The user wants the community self-hosted console plus API, inference, plugin, Postgres, Redis, and nginx on one Docker network. | Choose public `HOST_URL`, nginx host port, storage mode, secrets, database/Redis credentials, and image tags as one compatible set. | The user only wants API object semantics, provider schema details, plugin bundle behavior, or cannot allow service startup/image pulls/ports. |
| Standalone service development | The user is running individual FastAPI services for backend, inference, or plugin development. | Use host-reachable ports and explicit inter-service URLs; provide Postgres/Redis for backend; ensure inference/plugin are reachable from backend. | The user expects Compose DNS names such as `backend-inference` to work from the host outside Docker. |
| Existing production-like deployment | The user already has custom Compose, Kubernetes, reverse proxy, or managed database/cache/object storage. | Translate the same roles, health paths, env variables, and storage constraints into the user's platform. | Do not assume paths, volumes, or commands from the source checkout. Request the actual deployment manifests or runtime state. |

## Compose topology

The source-backed Compose topology contains eight services. Only nginx publishes a host port by default; the other services communicate on the Docker network.

| Service | Role | Image/tag evidence | Internal port / routes | Health signal | Persistent state |
| --- | --- | --- | --- | --- | --- |
| `frontend` | TaskingAI console UI served behind nginx. | `taskingai/taskingai-console:v0.3.0` | Container port `80`; nginx proxies `/` to it. | No explicit service health check in the source topology. | None in the topology. |
| `backend-web` | Server image in `PURPOSE=WEB` mode for console-facing web/auth/API routes. | `taskingai/taskingai-server:v0.3.0` | Container port `8000`; nginx proxies `/api/v1/` and `/imgs/` to it. | `GET /v1/health_check` inside the container. | Shares object-storage volume when local storage is used. |
| `backend-api` | Server image in API mode for public API routes. | `taskingai/taskingai-server:v0.3.0` | Container port `8000`; nginx proxies `/v1/` to it. | `GET /v1/health_check` inside the container. | Shares object-storage volume when local storage is used. |
| `backend-inference` | Inference microservice for provider/model operations. | `taskingai/taskingai-inference:v0.2.14` | Container port `8000`; backend services call it at `http://backend-inference:8000`; nginx proxies provider icon paths to it. | `GET /v1/health_check` inside the container. | None in the topology. |
| `backend-plugin` | Plugin microservice for bundle metadata/execution endpoints. | `taskingai/taskingai-plugin:v0.2.10` | Container port `8000`; backend services call it at `http://backend-plugin:8000`; nginx proxies plugin icon paths to it. | `GET /v1/health_check` inside the container. | Shares object-storage volume or uses S3 depending on storage mode. |
| `db` | Postgres with pgvector. | `ankane/pgvector:v0.5.1` | Container port `5432` on the Docker network. | `pg_isready -U postgres` in the source topology. | Database volume. |
| `cache` | Redis cache with password auth. | `redis:7-alpine` | Container port `6379` on the Docker network. | `redis-cli auth <password> ping`. | Redis volume. |
| `nginx` | Public reverse proxy for console, web API, public API, and image/icon routes. | `nginx:1.24` | Host `8080` to container `80` in the source topology. | No explicit service health check in the source topology. | Nginx cache volume. |

### Nginx routing map

| Public path | Upstream role | Expected use |
| --- | --- | --- |
| `/` | `frontend:80` | Console static app. |
| `/api/v1/` | `backend-web:8000` | Console-facing web routes. |
| `/v1/` | `backend-api:8000` | Public API routes used by clients. |
| `/imgs/` | `backend-web:8000` | Backend-served generated/static image paths. |
| `/images/providers/icons/` | `backend-inference:8000` | Provider icon assets. |
| `/images/plugins/bundles/icons/` | `backend-plugin:8000` | Plugin bundle icon assets. |

If the console loads but API calls fail, separate frontend delivery from `/api/v1/` and `/v1/` proxy reachability before debugging application semantics.

## Start and inspect a Compose deployment

Use these only in a user-provided deployment directory that contains the matching Compose manifest and environment file. Do not assume the original source checkout is present.

1. Create or edit the deployment-local `.env` from the user's chosen template or secrets manager.
2. Replace default secrets and credentials before exposing the service.
3. Start the stack with a stable project name, for example `taskingai`, if the user approves Docker service startup.
4. Inspect service status and logs from the deployment manager. For Docker Compose, useful signals are `ps`, health status, and logs for `backend-api`, `backend-web`, `backend-inference`, `backend-plugin`, `db`, `cache`, and `nginx`.
5. Check the public URL in a browser or HTTP client, then check `/api/v1/` and `/v1/` routes separately if the console or SDK cannot connect.

Expected default public endpoint: `http://localhost:8080` when nginx publishes host port `8080` and `HOST_URL` is also `http://localhost:8080`.

## Inter-service URL decision points

| Backend location | Correct inference URL shape | Correct plugin URL shape | Common mistake |
| --- | --- | --- | --- |
| Backend containers in the same Compose network | `http://backend-inference:8000` | `http://backend-plugin:8000` | Using `localhost`, which points back to the backend container instead of the sibling service. |
| Backend process running on the host | A host-reachable inference URL such as `http://127.0.0.1:<published-inference-port>` | A host-reachable plugin URL such as `http://127.0.0.1:<published-plugin-port>` | Reusing Compose DNS names without Docker networking or forgetting to publish inference/plugin ports. |
| Backend in a custom orchestrator | The service DNS name and port assigned by that orchestrator. | The service DNS name and port assigned by that orchestrator. | Copying source Compose service names into a different network namespace. |

Set `TASKINGAI_INFERENCE_URL` and `TASKINGAI_PLUGIN_URL` to service origins, not to a route with `/v1` already appended. For diagnostics, append `/v1/health_check` to the origin.

## Storage workflow

### Local object storage

Use `OBJECT_STORAGE_TYPE=local` when generated files/images should live on a shared local volume. In the source-backed topology, backend API, backend web, and plugin share the object-storage volume at the same in-container `PATH_TO_VOLUME`.

Checklist:

- `PATH_TO_VOLUME` is writable by the relevant service containers or service users.
- The same persisted storage is visible to services that need to create and serve generated files.
- `HOST_URL` matches the externally reachable URL that users and clients will use, including protocol and port.
- The reverse proxy routes image/file paths to the service that serves them.

### S3-compatible object storage

Use `OBJECT_STORAGE_TYPE=s3` when generated files/images should be uploaded to an S3-compatible bucket with public file URLs.

Checklist:

- Access key, secret key, endpoint, bucket, and public-domain settings are present before startup.
- The bucket or public-domain configuration makes returned file URLs accessible to the client/console.
- The plugin service has either `S3_IMAGE_BUCKET_NAME` or a compatible fallback bucket name.
- `PATH_TO_VOLUME` still points to a writable temporary directory for services that create local files before upload.

## Upgrade and version-skew workflow

The source deployment pins different service image families: console/server `v0.3.0`, inference `v0.2.14`, and plugin `v0.2.10`. The source service code observed during skill construction reports different internal versions for inference and plugin, which is a reminder not to mix Compose files, images, and env variable names from unrelated commits/tags.

When upgrading:

1. Keep the deployment manifest, env file, and image tags from one known-compatible release set.
2. Stop the running services gracefully.
3. Pull the selected image tags or update all related tags together.
4. Start the stack with the same persisted volumes and env values unless intentionally migrating.
5. Recheck service health, console reachability, and representative API/provider/plugin flows.

If a service starts but ignores an env variable, compare the image tag's expected variable name with the deployment config. For example, source config and pinned images can differ around image/icon URL prefix names.

## Development setup decision points

- Backend development needs Postgres, Redis, an inference service URL, and a plugin service URL. Decide whether those dependencies are local processes, Compose services, or externally managed services before setting backend env.
- Inference development can start without provider credentials for static health/catalog checks, but provider execution requires the relevant API keys or local provider host settings. Provider semantics belong to `../inference-providers/`.
- Plugin development can start with local object storage for schema/catalog work. S3 mode and credentialed plugin execution require storage/provider credentials. Bundle execution details belong to `../plugin-bundles/`.
- Running multiple backend purposes on one host may require distinct ports or separate process managers; the source Compose topology avoids this by running separate containers behind nginx.

## Source-backed native-testing notes and safe skip criteria

The native deployment candidate is a full Compose stack. It was classified as optional because it needs Docker, network image pulls, ports, disk, persistent volumes, and possibly external credentials.

Safe reasons to skip full native startup:

- The user asked only for config review, diagnosis from logs, or static topology explanation.
- Docker daemon access, network image pulls, or host port binding is unavailable or not approved.
- Port `8080` or the user's chosen public port is already reserved and cannot be changed.
- Required S3/provider credentials are absent for the scenario being tested.
- The task can be answered by validating env variables and service URL topology.

If native startup is explicitly approved, expected success signals are healthy backend/inference/plugin/db/cache checks and a reachable console at the configured `HOST_URL`. Treat provider/API-key tests and plugin execution tests as separate optional checks owned by their specialized sub-skills.
