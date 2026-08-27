# Instill Core Configuration Map

## Purpose

Read this when you need the service layout, environment knobs, or the main ports and health probes before starting Compose or Helm workflows.

## Environment files and overlays

- `.env` supplies the default Compose and chart values that the Makefile loads.
- `.env.secrets.component` and `.env.secrets.console` carry component-specific secrets for Compose runs.
- `.env.secrets.component.test` is the test secret file used by integration workflows.
- `docker-compose-dev.yml` enables the development profile with debug ports and more verbose backend settings.
- `docker-compose-observe.yml` enables the observability stack when `OBSERVE_ENABLED=true`.
- `docker-compose-nvidia.yml` adds the Ray GPU reservation path when the host exposes NVIDIA GPUs.

## Common environment knobs

- `EDITION` selects the deployment flavor: local Compose, test Compose, or Kubernetes chart mode.
- `SYSTEM_CONFIG_PATH` is where the Makefile stores the generated `user_uid` file.
- `NVIDIA_VISIBLE_DEVICES` overrides the default GPU device list when the NVIDIA path is active.
- `INITMODEL_ENABLED` and `INITMODEL_INVENTORY` drive the model initialization helper in the compose model flow.
- `CFG_...` variables are the standard backend container configuration prefix in Compose and Helm.

## Service and port map

| Service | Main ports | Purpose | Common health probe |
| --- | --- | --- | --- |
| api-gateway | 8080 / 8070 / 8071 | Public API entry point, stats, and metrics | `/__health` |
| pipeline-backend | 8081 / 3081 | Pipeline orchestration and workflow APIs | `/v1beta/health/pipeline` |
| artifact-backend | 8082 / 3082 | Artifact and RAG resource management | `/v1alpha/health/artifact` |
| model-backend | 8083 / 3083 | Model import, serving, and init-model flows | `/v1alpha/health/model` |
| mgmt-backend | 8084 / 3084 | User, auth, and usage management | `/v1beta/health/mgmt` |
| console | 3000 | Web UI | browser access |
| temporal | 7233 / 8088 | Workflow engine and UI | `tctl ... cluster health` |
| ray | 8265 / 10001 / 9000 / 8080 | Ray dashboard and serve ports | `ray status` |
| pg_sql | 5432 | PostgreSQL backing store | `pg_isready -U postgres` |
| redis | 6379 | Cache and state store | `redis-cli --raw incr ping` |
| influxdb | 8086 | Metrics and usage store | `/health` |
| openfga | 18081 / 8081 | Authorization datastore and API | OpenFGA health endpoints |
| registry | 5001 host / 5000 container | Local image registry for model builds | registry API |
| milvus | 19530 / 9091 | Vector database and web UI | Milvus health endpoint |
| minio | 19000 / 19001 | Object storage and console | MinIO health / console |
| prometheus | 9090 | Metrics scraping | Prometheus web UI |
| grafana | 3001 | Dashboards for compose observability | Grafana UI |
| tempo | 3200 / 4317 | Tracing backend | Tempo UI / OTLP |
| loki | 3100 | Log backend | Loki API |
| otel_collector | 4317 / 9001 | OpenTelemetry collection and metrics | OTLP / metrics |

## Workflow notes

- `make run` is the alias for `make compose-run`.
- `make compose-dev` adds the dev overlay on top of the base Compose file.
- `make helm-run` is the Helm equivalent for Kubernetes deployments.
- `make model-integration-test` uses the local registry plus the dummy model inventory to trigger model initialization.
- `make helm-integration-test` starts a Minikube cluster, installs the chart stack, and then runs the same service-level checks through port-forwarding.
