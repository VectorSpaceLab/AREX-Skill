<!-- SPDX-License-Identifier: Apache-2.0 -->

# Deployment workflows

Use these decision flows to plan Airflow deployments without requiring Kubernetes cluster access. Start with the user's goal, identify the deployment mode, then choose a validation path.

## Flow 1: choose the deployment mode

```text
Need a quick local/demo environment?
  -> Use official images and local container tooling.
  -> Keep secrets fake, data disposable, and image changes minimal.

Need production-like Kubernetes?
  -> Use the official Helm chart.
  -> Prefer external metadata DB, stable secrets, immutable Airflow image, and local rendering before upgrade.

Need custom operators/providers/libraries?
  -> Build a custom Airflow image.
  -> Install parse-time dependencies in the same image used by Dag processor/scheduler/workers.

Need to change chart-rendered Kubernetes resources?
  -> Change values first.
  -> If values cannot express it, consider a wrapper chart or overlay rather than editing rendered manifests.
```

For local-only CLI/API operations, route to the Airflow operations sub-skill instead of this deployment sub-skill.

## Flow 2: build or select the Airflow image

```text
Do Dags import only packages already in official image?
  YES -> Use official image directly or pin official image by tag/digest.
  NO  -> Build a custom image.

Are missing dependencies small Python packages or apt packages?
  YES -> Extend official image with a Dockerfile.
  NO  -> Consider image customization for compiled, large, vetted, or air-gapped dependency sets.

Will dependencies be installed in startup commands?
  YES -> Redesign for image build-time installation for production.
  NO  -> Continue.
```

Image handoff to Helm values:

```yaml
images:
  airflow:
    repository: registry.example.com/team/airflow
    tag: "2026-06-23-a1b2c3d"
    pullPolicy: IfNotPresent
```

If using a private registry, configure image pull secrets. Do not put registry credentials in plain values.

## Flow 3: choose a Dag distribution approach

| Approach | Best fit | Operational notes |
|---|---|---|
| Bake Dags into the image | Stable release workflow; Dags change with app versions | Requires image rebuild and Helm rollout for Dag updates. Best reproducibility. |
| Airflow 3 Dag bundles | Structured Airflow-native bundle configuration | Configure `dagProcessor.dagBundleConfigList`; ensure required bundle provider and credentials are in the image/secrets. |
| git-sync without persistence | Git-based Dag delivery where each relevant pod syncs locally | Avoids shared filesystem consistency issues but creates git traffic from multiple pods. KubernetesExecutor uses init container behavior for workers. |
| git-sync with persistence | Shared checkout on a PVC | Requires storage that handles git-sync symlink swaps correctly. Use only after testing POSIX behavior, latency, and consistency. |
| Externally populated PVC | A separate process controls Dag delivery | Chart only mounts the claim; user-owned process must update it safely. |

Review details:

- `dags.persistence.enabled=true` creates or mounts a Dag PVC.
- `dags.persistence.existingClaim` uses a pre-existing claim.
- `dags.gitSync.enabled=true` adds git-sync behavior.
- `dags.gitSync.repo`, `ref`/`rev`/`branch`, `subPath`, credentials, SSH key, known hosts, sync period, and resources must match the user's repository and security requirements.
- When both git-sync and persistence are enabled, only the syncing component writes to the PVC and other pods read it. This requires careful filesystem validation.
- For multiple Git repositories, prefer an umbrella repository/submodule strategy or Airflow 3 bundle design rather than expecting one chart git-sync instance to sync many unrelated repos.

## Flow 4: database and broker

```text
Is this production-like?
  YES -> Disable bundled Postgres and use external managed database or user-managed PostgreSQL.
  NO  -> Bundled Postgres can be acceptable for quick starts.

Is executor Celery-based?
  YES -> Need Redis/broker URL. Use bundled Redis for simple setups, external broker for production needs.
  NO  -> Redis may be disabled unless another component needs it.

Is PostgreSQL metadata DB busy or connection count high?
  YES -> Enable/configure PgBouncer and size pools.
```

Production-oriented values skeleton:

```yaml
postgresql:
  enabled: false
data:
  metadataSecretName: airflow-metadata-connection
  resultBackendSecretName: airflow-result-backend-connection
pgbouncer:
  enabled: true
  metadataPoolSize: 10
  resultBackendPoolSize: 5
  maxClientConn: 100
```

Use `data.metadataConnection` only for non-sensitive examples or throwaway environments. For real credentials, reference Kubernetes Secrets and avoid printing connection strings in review output.

## Flow 5: secrets and Airflow config

Prefer Secret references over inline credential values:

- Metadata DB: `data.metadataSecretName` with key `connection`.
- Result backend: `data.resultBackendSecretName` with key `connection`.
- Broker URL: `data.brokerUrlSecretName`.
- Fernet key: `fernetKeySecretName` with key `fernet-key`.
- API secret: `apiSecretKeySecretName` with key `api-secret-key`.
- JWT secret: `jwtSecretName` with key `jwt-secret`.
- Custom env secrets: `secret` entries referencing `secretName` and `secretKey`.

Use `config` for non-secret Airflow configuration. Use environment variables (`env`, `extraEnv`, `extraEnvFrom`) when a chart parameter explicitly expects env injection or when overriding official image defaults such as `AIRFLOW__CORE__LOAD_EXAMPLES` for example Dags.

Review for these hazards:

- Plain passwords under `data.metadataConnection.pass`, `redis.password`, `fernetKey`, `apiSecretKey`, `jwtSecret`, `extraSecrets`, or `env` values.
- Templated `config` values containing unescaped `{{`.
- Rotating generated secrets on upgrade because stable existing Secret names were not provided.
- In Airflow 3, using old `webserver` secret/config names instead of `api` and `api_auth` settings.

## Flow 6: logging choices

| Choice | Values | Fit | Cautions |
|---|---|---|---|
| No persistence | `logs.persistence.enabled=false` | Disposable/local or external log collection | Logs disappear with pods. For Celery, also consider worker log persistence behavior. |
| Celery worker persistence | `workers.celery.persistence.enabled=true` | Persist task logs for Celery workers | Does not persist scheduler logs the same way as shared log persistence. |
| Shared logs PVC | `logs.persistence.enabled=true` | Shared local log storage | Requires RWX-compatible storage and writable permissions for the Airflow runtime user/group. |
| Existing logs PVC | `logs.persistence.existingClaim` | Pre-provisioned shared storage | Claim must be writable and support access from relevant components. |
| Remote backend | `elasticsearch.*`, `opensearch.*`, or Airflow logging config | Centralized logs | Configure exactly one backend path and provide required Secret/connection details. |

If a user reports missing logs, first identify whether logs were ever persistent, whether workers wrote to the expected backend, and whether the API server has permission/configuration to read task logs.

## Flow 7: scaling workers and services

KEDA and HPA are different scaling mechanisms:

- `workers.celery.keda.enabled=true` creates a KEDA ScaledObject for Celery workers. It can scale to zero and uses a SQL query against Airflow metadata DB by default.
- `workers.celery.hpa.enabled=true` creates a standard HPA for Celery workers. Do not enable both KEDA and HPA for the same worker target.
- `apiServer.hpa.enabled=true` can scale API server replicas by resource metrics.
- `triggerer.keda.enabled=true` can scale triggerers based on trigger table load.

KEDA review points:

1. KEDA must be installed in the cluster before applying ScaledObjects.
2. `config.celery.worker_concurrency` should be set through Helm values so the KEDA SQL divisor matches actual worker concurrency.
3. `workers.celery.keda.minReplicaCount`, `maxReplicaCount`, `cooldownPeriod`, and `pollingInterval` should reflect workload and shutdown time.
4. If PgBouncer is enabled, confirm whether the KEDA scaler should use PgBouncer (`usePgbouncer`) and whether database credentials/Secrets are available.
5. Multiple queues require checking `workers.celery.queue` and any worker sets.

## Flow 8: safe review sequence

1. Run the bundled summarizer against the proposed values file.
2. Remove or redact secrets before sharing output.
3. If Helm is available, run `helm lint` and `helm template` locally.
4. Inspect rendered Deployments, StatefulSets, Jobs, Secrets, ConfigMaps, PVCs, ServiceAccounts, RBAC, KEDA/HPA resources, and Ingress/HTTPRoute resources.
5. For upgrades, compare old and new values and render a diff before live upgrade.
6. Only after no-cluster checks pass should the user run live cluster diagnostics or upgrades.

## Cross-skill routing

- Route CLI help, Airflow metadata commands, `airflowctl`, Dag triggering, task clearing, and REST API usage to `operations-cli-api`.
- Route Dag authoring, TaskFlow, assets, dynamic task mapping, or provider operator usage to the relevant authoring/provider sub-skill.
- Route repository contribution mechanics to the Airflow contribution or chart-development workflow only when the user is editing chart source/tests/docs, not deploying Airflow.
