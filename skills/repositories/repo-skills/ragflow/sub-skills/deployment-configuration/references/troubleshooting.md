# Deployment Troubleshooting

## Fast Triage

1. Confirm deployment mode: Docker Compose, source, or Helm.
2. Confirm document engine and active profiles: `DOC_ENGINE`, `DEVICE`, and `COMPOSE_PROFILES`.
3. Confirm the UI port versus API port: `SVR_WEB_HTTP_PORT` is browser-facing; `SVR_HTTP_PORT` is backend API.
4. Check whether the API server and task executors are both running.
5. Validate config files with `scripts/validate_env.py` before restarting services.
6. Read logs for the failing service and the selected document engine before changing unrelated settings.

## Docker Or Compose Does Not Start

- Verify Docker Engine and Compose versions meet the documented minimums.
- Check available CPU, memory, and disk. RAGFlow self-hosting expects at least 4 CPU cores, 16 GB RAM, and 50 GB disk.
- For Elasticsearch/OpenSearch, check `vm.max_map_count` and disk watermarks.
- For Docker image pulls, verify `RAGFLOW_IMAGE` and registry mirror settings.
- Prebuilt RAGFlow images are documented for x86 platforms; ARM64 users may need a compatible image build.

## RAGFlow Starts But Browser Shows Network Errors

- Wait for the RAGFlow container to finish initialization; the UI can be reachable before the backend is ready.
- Check the RAGFlow service logs for the startup banner and backend bind port.
- Use the UI port for the browser. The backend API port is not the normal UI URL.
- If using source frontend development, check the Vite proxy target points to the backend API port.
- Confirm nginx is running in Docker deployments; source debug flows may bypass or disable nginx.

## Document Engine Mismatch

Symptoms: backend starts but search/indexing fails, document parsing stalls, or logs mention missing engine hosts.

Checks:

- `DOC_ENGINE` must match an active Compose profile.
- `service_conf.yaml` must contain the matching engine section and point to the host reachable from the backend process.
- Do not leave `DOC_ENGINE=infinity` while `COMPOSE_PROFILES` activates only Elasticsearch, or vice versa.
- Switching engines may require deleting or migrating old volumes; do not run volume-deleting commands without explicit user approval.
- Infinity switch flows are not officially supported on Linux arm64 in the documented path.

## Elasticsearch Or OpenSearch Errors

- Elasticsearch uses `ES_HOST`, `ES_PORT`, and `ELASTIC_PASSWORD`; service config uses the `es` section.
- OpenSearch uses `OS_HOST`, `OS_PORT`, and `OPENSEARCH_PASSWORD`; service config uses the `os` section.
- OpenSearch initial admin password must satisfy complexity requirements.
- If Kibana is enabled, ensure the Kibana profile is included and Elasticsearch security settings are compatible with the Kibana enrollment flow.
- If logs mention connection refused, distinguish container-network host/port from host-exposed port.

## Infinity, OceanBase, Or SeekDB Errors

- Infinity uses a thrift URI for RAGFlow backend connectivity and has separate HTTP/Postgres exposed ports.
- OceanBase requires high file descriptor limits and core dump settings before container startup.
- SeekDB shares the OceanBase-style config model but has its own host, port, user, password, database, and memory settings.
- If engine health checks pass but RAGFlow cannot connect, validate service config hostnames from the backend process context.

## MySQL Errors

- Confirm `MYSQL_PASSWORD`, `MYSQL_DBNAME`, `MYSQL_HOST`, and `MYSQL_PORT` match the service config.
- In Docker, `MYSQL_PORT` is the container-network port while `EXPOSE_MYSQL_PORT` is host-facing.
- In source mode, backend processes usually need host-reachable names and exposed ports.
- If large document metadata writes fail, check `MYSQL_MAX_PACKET` and `mysql.max_allowed_packet`.
- If migrations fail after an image version change, check image tag, database state, and migration logs before clearing data.

## MinIO Or Object Storage Errors

- Confirm `MINIO_USER`, `MINIO_PASSWORD`, `MINIO_HOST`, and service config `minio.host` match.
- In Docker Compose, RAGFlow normally reaches MinIO on the container-network API port, not the console port.
- If using external S3-compatible storage, configure the provider section completely and avoid mixing partial MinIO and S3 settings.
- For HTTPS or self-signed object storage endpoints, align `secure` and certificate verification settings.

## Redis, NATS, And Task Executor Issues

Symptoms: uploads work but parsing never completes, task executor exits repeatedly, or jobs remain queued.

- Default Python deployments require Redis connectivity for task executors.
- Check `REDIS_HOST`, `REDIS_PORT`, `REDIS_USERNAME`, `REDIS_PASSWORD`, and service config `redis` settings.
- Ensure at least one task executor is running; the backend API alone cannot process document ingestion work.
- `WS` controls task-executor worker count in the backend launcher; values below `1` are coerced to `1`.
- NATS is mainly for Go/hybrid mode and requires the corresponding Compose profile when used.

## Source Launch Failures

- Use Python 3.13. The project is not a generic Python 3.10/3.11 app in current metadata.
- Use `uv sync` rather than a generic editable install. A plain editable install can fail because package metadata expects a top-level `graphrag` package while the source layout is different.
- Run dependency download before starting the backend if model/parser assets are missing.
- Start base services first and ensure their hostnames resolve from the host-side Python process.
- Ensure backend processes run with the checkout root on Python's import path before launching services.
- If jemalloc is missing, install it or avoid manual `LD_PRELOAD` commands that reference it.
- Launch both API server and task executor processes; one without the other creates misleading partial success.

## Embedding Service Or Default Model Problems

- Current RAGFlow images do not include embedding models.
- If `user_default_llm` still contains placeholders, configure a real provider or use the UI settings before expecting embeddings to work.
- If using TEI, include `tei-cpu` or `tei-gpu` in `COMPOSE_PROFILES` and size memory for `TEI_MODEL`.
- A missing embedding provider can surface as ingestion failure, retrieval failure, or first-user setup confusion.

## HTTPS, nginx, And Upload Size

- For HTTPS, mount certificate and key files read-only into the container and use the HTTPS nginx config.
- Ensure DNS points to the host and ports `80` and `443` are available.
- Replace placeholder server names in nginx config before restart.
- Keep backend `MAX_CONTENT_LENGTH` and nginx `client_max_body_size` aligned.
- For local self-signed certificates, warn users that browser trust errors are expected until the certificate is trusted.

## Sandbox And gVisor

- gVisor is only required for the sandbox/code-executor feature.
- Enabling sandbox support requires the sandbox Compose profile and executor-manager image settings.
- Sandbox manager access to Docker is privileged and should be reviewed carefully in production.

## Helm Failures

- Run `helm lint` and inspect `helm template` output before applying.
- Helm supports `infinity`, `elasticsearch`, and `opensearch` document engines.
- If disabling in-cluster MySQL, MinIO, or Redis, provide the corresponding external host, port, and credentials.
- Confirm Secrets contain required sensitive values and Pods receive the rendered environment.
- If ingress works but API calls fail, check service ports, ingress path routing, and backend health separately.
