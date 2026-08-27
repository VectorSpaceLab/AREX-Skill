# Docker Compose and Helm Deployment

This reference summarizes the RocketRide container and Kubernetes deployment
surfaces. Use it to plan commands, values, networking, secrets, probes, and
rollback steps without needing to reopen deployment source files.

## Choose Compose or Helm

| Mode | Use when | Avoid when |
|---|---|---|
| Docker Compose | Local or staging-like full stack; quick engine plus PostgreSQL/vector stores | Production HA, cluster autoscaling, managed secrets |
| Helm | Kubernetes production or shared cluster; external databases/secrets/ingress | Single-machine smoke tests or no cluster access |

Both modes expose the engine task service on port `5565`. Health is checked with
`GET /ping`; task execution uses a WebSocket at `/task/service`.

## Docker Compose overview

Prerequisites:

- Docker Engine `>= 24.0`
- Docker Compose V2 `>= 2.17`

A Compose stack starts the engine from a source-managed image. It is intended for
source-checkout or image-build workflows, not for a standalone release archive.
Before non-local use, copy the environment template and change every placeholder
password.

Typical commands:

```bash
# From the Compose stack directory distributed with RocketRide:
cp .env.example .env
# Edit .env before exposing anything beyond localhost.

docker compose up engine   # engine and its declared Compose dependencies
docker compose up          # engine plus PostgreSQL, Milvus, MinIO, etcd, ChromaDB
docker compose up -d       # detached mode
docker compose ps
docker compose logs -f engine
docker compose down
docker compose down -v     # also removes persisted data volumes
```

If the engine image is built from source, assemble the runtime first:

```bash
./builder build server
```

This is heavy and may download or compile runtime components. Do not run it just
to answer a planning question.

### Compose services and ports

| Service | Default host port | Purpose |
|---|---:|---|
| `engine` | `5565` | RocketRide processing engine |
| `postgres` | `5432` | PostgreSQL 16 with pgvector; required by engine stack |
| `milvus` | `19530` | Milvus vector database |
| `minio` | `9000` / `9001` | Object storage for Milvus plus console |
| `etcd` | `2379` | Milvus metadata store |
| `chroma` | `8000` | ChromaDB vector database |

Key `.env` variables:

| Variable | Meaning |
|---|---|
| `ENGINE_PORT` | Host port mapped to container port `5565` |
| `ROCKETRIDE_LOG_LEVEL` | Engine log verbosity |
| `ENGINE_CPU_LIMIT`, `ENGINE_MEMORY_LIMIT` | Compose resource limits |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT` | PostgreSQL credentials/port |
| `MILVUS_PORT`, `MILVUS_GRPC_PORT` | Milvus exposed ports |
| `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_API_PORT`, `MINIO_CONSOLE_PORT` | MinIO credentials/ports |
| `CHROMA_PORT` | ChromaDB exposed port |

The engine container receives a `POSTGRES_URL` built from Compose variables and
service names, plus `MILVUS_HOST=milvus`, `MILVUS_PORT=19530`,
`CHROMA_HOST=chroma`, and `CHROMA_PORT=8000`.

### Compose health and startup behavior

The engine healthcheck is:

```bash
curl -f http://localhost:5565/ping
```

`postgres` must be healthy before the engine starts. Milvus and Chroma are
optional vector stores from the engine's perspective: Compose waits for them to
start, not necessarily become healthy. If a pipeline node later requires Milvus
or Chroma while that service is unhealthy, the error appears at request time.

Named volumes persist data between restarts: `pgdata`, `etcddata`, `miniodata`,
`milvusdata`, and `chromadata`. `docker compose down -v` removes them.

### Compose networking rules

- From the host, use the published port: `ws://localhost:${ENGINE_PORT:-5565}`
  or `http://localhost:${ENGINE_PORT:-5565}/ping`.
- From another container on the Compose network, use service DNS:
  `ws://engine:5565/task/service`.
- Inside Compose, do not point the engine at `localhost` for PostgreSQL, Milvus,
  or Chroma. Use service names such as `postgres`, `milvus`, and `chroma`.
- If a workflow outside Docker cannot reach the engine, first check port mapping
  and firewall rules before debugging SDK code.

### Compose security checklist

- Change all placeholder passwords before non-local use.
- Do not commit `.env` with real secrets.
- Put model-provider API keys in the engine environment and reference them from
  pipeline config by environment variable, not as literals.
- Bind to localhost for local development; add TLS/auth/proxy rules before
  exposing the task socket to a network.

## Helm chart overview

Prerequisites:

- Kubernetes `>= 1.25`
- Helm `>= 3.10`
- External PostgreSQL/pgvector, or a separately managed PostgreSQL deployment

The chart deploys the RocketRide engine. It does **not** bundle databases or
vector stores. Configure external services through `engine.env` and provide
credentials through `engine.secrets` or `engine.existingSecret`.

Generic install commands:

```bash
helm install rocketride <chart-dir>
helm install rocketride <chart-dir> --values my-values.yaml
helm install rocketride <chart-dir> --dry-run --debug
helm upgrade rocketride <chart-dir> --values my-values.yaml
helm uninstall rocketride
```

PVCs are not removed automatically by `helm uninstall`; delete them separately if
your values create persistent volumes.

### Helm service, probes, and access

Default engine service settings:

| Parameter | Default | Meaning |
|---|---:|---|
| `engine.service.type` | `ClusterIP` | Internal service by default |
| `engine.service.port` | `5565` | Service port |
| `engine.service.targetPort` | `5565` | Container port |
| `ingress.enabled` | `false` | No external ingress unless enabled |

Readiness, liveness, and startup probes all call `/ping` on port `5565`. For a
ClusterIP service, port-forward for a local validation:

```bash
kubectl --namespace <namespace> port-forward svc/<release-fullname>-engine 5565:5565
curl http://127.0.0.1:5565/ping
```

For a chart installed as release `rocketride` with the default chart name, the
service name is commonly `rocketride-engine`; if overrides are used, derive the
actual name from the Helm release notes or `kubectl get svc`.

`helm test <release> --namespace <namespace>` runs a connectivity check that
curls `/ping` on the engine service.

### Required secrets

The chart validates that credentials exist. A render/install fails if neither
`engine.existingSecret` nor `engine.secrets` is set.

Development-style chart-managed secrets:

```yaml
engine:
  secrets:
    OPENAI_API_KEY: "sk-..."
    POSTGRES_PASSWORD: "change-me"
```

Production-style externally managed Secret:

```yaml
engine:
  existingSecret: "rocketride-credentials"
  existingSecretChecksum: "2026-04-09-rotation-1"
```

Use `existingSecretChecksum` as a manual rollout bump when external secret
contents rotate. Chart-managed secrets automatically affect the pod checksum when
values change.

### Engine values that often matter

| Parameter | Default | Use |
|---|---|---|
| `engine.replicaCount` | `1` | Set `2+` for HA when autoscaling is disabled |
| `engine.image.repository` | `ghcr.io/rocketride-org/rocketride-engine` | Engine image repository |
| `engine.image.tag` | chart appVersion | Override image version |
| `engine.resources.requests/limits` | modest CPU/memory defaults | Tune for workload size |
| `engine.autoscaling.enabled` | `false` | CPU/memory HPA |
| `engine.env.LOG_LEVEL` | `info` | Engine log level |
| `engine.env.WORKER_THREADS` | `4` | Worker thread count |
| `engine.podSecurityContext` | non-root user/group | Pod security defaults |
| `engine.securityContext` | no privilege escalation, read-only root FS | Container hardening |

For production HA, use at least two replicas or autoscaling and add anti-affinity
so replicas do not all land on one node.

### External PostgreSQL pattern

RocketRide expects PostgreSQL/pgvector to exist outside the chart. Put non-secret
connection details in `engine.env` and the password in a Secret:

```yaml
engine:
  env:
    POSTGRES_HOST: "postgres.example.com"
    POSTGRES_PORT: "5432"
    POSTGRES_USER: "rocketride"
    POSTGRES_DB: "rocketride"
  existingSecret: "rocketride-postgres"
```

Create the Secret with a `POSTGRES_PASSWORD` key, or use your platform's secret
manager to materialize that key.

### External Chroma pattern

```yaml
engine:
  env:
    CHROMA_HOST: "chroma.example.com"
    CHROMA_PORT: "8000"
  # If Chroma needs auth, provide its token through engine.secrets or existingSecret.
```

Milvus is not bundled by default. Add an official Milvus chart or managed Milvus
service separately and pass its connection details through `engine.env` and
secrets.

### GPU and autoscaling pattern

GPU support is optional and was not part of the minimum verified skill runtime.
Use it only when cluster nodes and the NVIDIA stack are ready.

GPU values pattern:

```yaml
engine:
  gpu:
    enabled: true
    count: "1"
    nodeSelector:
      accelerator: nvidia-gpu
    tolerations:
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
  resources:
    requests:
      cpu: "1"
      memory: 4Gi
    limits:
      cpu: "4"
      memory: 8Gi
  autoscaling:
    enabled: false
```

CPU/memory HPA cannot see GPU utilization. For GPU inference workloads, disable
built-in HPA and use an external scaler such as KEDA with Prometheus/DCGM metrics
or queue-depth metrics. A KEDA `ScaledObject` is a Kubernetes manifest to apply
with `kubectl`, not a Helm values file.

### Ingress and WebSocket upgrades

If exposing the engine through ingress:

- Enable TLS and use `https://` or `wss://` in clients.
- Ensure the ingress controller supports WebSocket upgrade headers and long-lived
  connections.
- Keep `/ping` reachable for probes and `/task/service` reachable for WebSocket
  task traffic.
- Treat Cloud and public on-prem endpoints as authenticated; do not expose a
  no-auth local engine to the internet.

## Deployment validation checklist

Before declaring a deployment usable:

1. Confirm the service listens on port `5565`.
2. Confirm `GET /ping` succeeds from the same network path clients will use.
3. Confirm auth variables are set for Cloud/production.
4. Confirm provider and database secrets are present in the engine environment.
5. Confirm client URI scheme matches the target: secure Cloud/ingress, WebSocket
   for direct task protocol, and correct host name for host/container/cluster.
6. For observability dashboards, confirm a client subscribes over WebSocket and
   resubscribes on reconnect.
