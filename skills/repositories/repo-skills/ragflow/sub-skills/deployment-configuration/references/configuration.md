# Configuration Reference

## File Roles

- `.env` controls Docker Compose variables: selected document engine, device profile, image tags, exposed ports, service credentials, resource limits, optional embedding service, sandbox settings, and feature toggles.
- `service_conf.yaml.template` is rendered into the backend service config at container startup. It configures API/admin listen ports, database, object storage, document engine, Redis, NATS, default models, OAuth, authentication, permissions, SMTP, and logging.
- `docker-compose.yml` starts RAGFlow and includes the base dependency stack.
- `docker-compose-base.yml` defines MySQL, MinIO, Redis, document-engine services, optional TEI embedding service, optional sandbox executor manager, optional Kibana, and NATS for Go/hybrid paths.
- Helm `values.yaml` combines image, dependency, service, ingress, and environment settings for Kubernetes.

## High-Impact `.env` Keys

| Key | Meaning | Notes |
| --- | --- | --- |
| `DOC_ENGINE` | Active document engine. | Docker supports `elasticsearch`, `infinity`, `opensearch`, `oceanbase`, `seekdb`; Helm supports `infinity`, `elasticsearch`, `opensearch`. |
| `DEVICE` | DeepDoc inference device profile. | `cpu` or `gpu`; must match a RAGFlow service profile. |
| `COMPOSE_PROFILES` | Compose profiles to activate. | Should include `${DOC_ENGINE}` and `${DEVICE}`; add optional profiles such as `tei-cpu`, `tei-gpu`, `sandbox`, `kibana`, or `ragflow-go` only when needed. |
| `RAGFLOW_IMAGE` | RAGFlow container image tag. | Keep image version aligned with deployment files; v0.22+ images do not include embedding models. |
| `SVR_WEB_HTTP_PORT` | Browser-facing HTTP port. | Maps to container port `80`; default is usually the no-port browser URL. |
| `SVR_WEB_HTTPS_PORT` | Browser-facing HTTPS port. | Maps to container port `443` when HTTPS nginx config is used. |
| `SVR_HTTP_PORT` | Backend API port. | Maps to container port `9380`; not the same as the UI port. |
| `ADMIN_SVR_HTTP_PORT` | Admin service port. | Maps to container port `9381`. |
| `SVR_MCP_PORT` | MCP server port if enabled. | Must match MCP command flags when MCP is enabled. |
| `API_PROXY_SCHEME` | Python, Go, or hybrid server path. | Default Python deployment uses Python API/task-executor processes; Go/hybrid paths may need NATS. |
| `REGISTER_ENABLED` | User registration switch. | `1` enables registration, `0` disables it. |
| `MAX_CONTENT_LENGTH` | Backend upload size limit. | Keep nginx `client_max_body_size` aligned. |

## Document Engine Settings

| Engine | Required `.env` keys | Service config section | Consistency checks |
| --- | --- | --- | --- |
| Elasticsearch | `ES_HOST`, `ES_PORT`, `ELASTIC_PASSWORD`, `STACK_VERSION` | `es.hosts`, `es.username`, `es.password` | `DOC_ENGINE=elasticsearch`, profile includes `elasticsearch`, service config points at the Elasticsearch host from the backend context. |
| Infinity | `INFINITY_HOST`, `INFINITY_THRIFT_PORT`, `INFINITY_HTTP_PORT`, `INFINITY_PSQL_PORT` | `infinity.uri`, `infinity.postgres_port`, `infinity.db_name` | `DOC_ENGINE=infinity`, profile includes `infinity`, URI uses the thrift host/port reachable by the backend. |
| OpenSearch | `OS_HOST`, `OS_PORT`, `OPENSEARCH_PASSWORD` | `os.hosts`, `os.username`, `os.password` | `DOC_ENGINE=opensearch`, profile includes `opensearch`, OpenSearch password satisfies complexity requirements. |
| OceanBase | `OCEANBASE_HOST`, `OCEANBASE_PORT`, `OCEANBASE_USER`, `OCEANBASE_PASSWORD`, `OCEANBASE_DOC_DBNAME` | `oceanbase.scheme`, `oceanbase.config` | Host file descriptor/core limits are prepared; database and credentials match. |
| SeekDB | `SEEKDB_HOST`, `SEEKDB_PORT`, `SEEKDB_USER`, `SEEKDB_PASSWORD`, `SEEKDB_DOC_DBNAME` | `seekdb.scheme`, `seekdb.config` | Profile includes `seekdb`; credentials and database name match. |

Document engine changes can make existing indexes incompatible or unreachable. Always confirm whether to preserve, migrate, or discard existing engine volumes before using volume-deleting commands.

## Core Service Settings

### MySQL

`.env` keys: `MYSQL_HOST`, `MYSQL_PORT`, `EXPOSE_MYSQL_PORT`, `MYSQL_DBNAME`, `MYSQL_PASSWORD`, `MYSQL_MAX_PACKET`.

`service_conf.yaml` keys: `mysql.name`, `mysql.user`, `mysql.password`, `mysql.host`, `mysql.port`, `mysql.max_connections`, `mysql.stale_timeout`, `mysql.max_allowed_packet`.

Inside Docker Compose, `MYSQL_PORT` is the port RAGFlow uses to reach MySQL from the container network. `EXPOSE_MYSQL_PORT` is the host-facing port. In source mode, backend processes run on the host, so hostnames and exposed ports must be reachable from the host process.

### MinIO And Object Storage

`.env` keys: `MINIO_HOST`, `MINIO_PORT`, `MINIO_CONSOLE_PORT`, `MINIO_USER`, `MINIO_PASSWORD`, optional `STORAGE_IMPL`, and object-storage provider keys.

`service_conf.yaml` keys: `minio.user`, `minio.password`, `minio.host`, `minio.bucket`, `minio.prefix_path`, optional `minio.secure`, optional `minio.verify`, or provider sections such as `s3`, `oss`, `azure`, and `opendal`.

For in-Compose MinIO, backend traffic normally uses the container-network API port `9000`. For external object storage, configure the provider section completely and avoid leaving unused MinIO defaults that confuse diagnosis.

### Redis And NATS

`.env` keys: `REDIS_HOST`, `REDIS_PORT`, `REDIS_USERNAME`, `REDIS_PASSWORD`, `NATS_HOST`, `NATS_PORT`.

`service_conf.yaml` keys: `redis.host`, `redis.db`, `redis.username`, `redis.password`, `nats.host`, `nats.port`.

Default Python deployments rely on Redis for task-executor queues. NATS is mainly relevant to Go/hybrid deployment paths where the NATS service profile is enabled.

### Embedding Service And Default Models

`.env` keys: `TEI_IMAGE_CPU`, `TEI_IMAGE_GPU`, `TEI_MODEL`, `TEI_HOST`, `TEI_PORT`, and optional `COMPOSE_PROFILES` additions `tei-cpu` or `tei-gpu`.

`service_conf.yaml` keys: `user_default_llm`, especially `default_models.embedding_model`, `base_url`, and API key or provider-specific credentials.

Because current images do not bundle embedding models, either configure a real provider in the UI/service config or enable and size a TEI service profile. The default `Qwen/Qwen3-Embedding-0.6B` model requires much more memory than small test models.

## Helm Values

Helm settings mirror the Docker environment but are expressed in `values.yaml`:

- `env.DOC_ENGINE` chooses `infinity`, `elasticsearch`, or `opensearch`.
- `ragflow.image.repository` and `ragflow.image.tag` select the RAGFlow image.
- `mysql.enabled`, `minio.enabled`, and `redis.enabled` decide whether the chart deploys in-cluster dependencies or expects external services.
- `ragflow.service_conf` can supply service config overrides written inside the RAGFlow container.
- `ingress.enabled`, `ingress.className`, `ingress.hosts`, and `ingress.tls` expose the UI through Kubernetes ingress.
- `global.repo` and image pull secret settings apply registry mirrors and credentials.

Helm defaults to `DOC_ENGINE: infinity`; Docker defaults to `DOC_ENGINE=elasticsearch`. Always confirm the deployment mode before assuming the engine.

## Validation Helper

Use the bundled validator for read-only checks of provided config files:

```bash
python scripts/validate_env.py --env docker/.env --service-conf docker/service_conf.yaml.template
```

Useful options:

```bash
python scripts/validate_env.py --env docker/.env --service-conf docker/service_conf.yaml.template --deployment source
python scripts/validate_env.py --env values.yaml --deployment helm --strict
```

The validator checks allowed engines, profile alignment, common credential mismatches, default-password warnings, active port collisions, service-config sections, embedding-service consistency, and source/Helm mode caveats. It does not modify files, start Docker, contact services, or require third-party Python packages.
