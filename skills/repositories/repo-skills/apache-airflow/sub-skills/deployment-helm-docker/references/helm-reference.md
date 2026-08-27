<!-- SPDX-License-Identifier: Apache-2.0 -->

# Helm reference for Airflow deployments

This reference distills the official Airflow Helm chart behavior for planning and reviewing values files. It is intentionally self-contained and does not require opening source documentation.

## Values families

| Family | Typical keys | Purpose | Review focus |
|---|---|---|---|
| Chart identity | `fullnameOverride`, `nameOverride`, `useStandardNaming`, `revisionHistoryLimit`, `labels` | Resource naming and shared labels | `useStandardNaming` can rename resources and recreate workloads/PVCs in existing installs. |
| Airflow image | `defaultAirflowRepository`, `defaultAirflowTag`, `airflowVersion`, `images.airflow.*`, `images.pod_template.*`, `imagePullSecrets`, `registry.secretName` | Select image for Airflow components and KubernetesExecutor pod templates | Keep `airflowVersion` aligned with deployed image. Digest overrides tag. Private registries need pull secrets. |
| Executor and pod launch | `executor`, `allowPodLaunching`, `allowJobLaunching`, `workers.*` | Select Local, Celery, Kubernetes, or multiple executors and grant launch permissions | Executor choice controls whether Redis/workers/Kubernetes pod-launch RBAC are needed. |
| Airflow config | `config`, `env`, `extraEnv`, `extraEnvFrom`, `secret`, `extraSecrets`, `extraConfigMaps`, `airflowLocalSettings` | Configure Airflow and inject environment variables | Prefer Secret-backed values for credentials. Values under `config` are templated, so literal `{{` must be escaped. |
| Core components | `apiServer`, `scheduler`, `dagProcessor`, `triggerer`, `workers` | Configure Airflow 3 workloads | In Airflow 3 the UI/API component is `apiServer`; the Dag processor is a separate deployment. |
| Database | `postgresql.enabled`, `data.metadataConnection`, `data.metadataSecretName`, `data.resultBackendSecretName`, `databaseCleanup` | Metadata database and cleanup job | Disable bundled Postgres for production and point to an external database or Secret. |
| Broker and Celery | `redis.enabled`, `redis.*`, `data.brokerUrl`, `data.brokerUrlSecretName`, `workers.celery.*` | Redis broker and Celery workers | If `redis.enabled=false` with a Celery executor, provide an external broker URL or Secret. |
| PgBouncer | `pgbouncer.enabled`, `pgbouncer.metadataPoolSize`, `pgbouncer.resultBackendPoolSize`, `pgbouncer.maxClientConn`, `pgbouncer.configSecretName` | Database connection pooling for PostgreSQL | Enable for busy PostgreSQL-backed deployments; check pool sizes, stats Secret, and external DB wiring. |
| Secrets | `fernetKeySecretName`, `apiSecretKeySecretName`, `jwtSecretName`, `enableBuiltInSecretEnvVars`, `extraSecrets` | Encryption, API, JWT, connection, and custom Secret wiring | Static API/JWT/Fernet secrets avoid accidental restarts or token invalidation during upgrades. |
| Dag distribution | `dags.persistence.*`, `dags.gitSync.*`, `dagProcessor.dagBundleConfigList`, `images.airflow.*` | Deliver Dag code through image, volume, git-sync, or Airflow 3 bundles | Avoid inconsistent remote filesystem behavior; choose one primary Dag delivery strategy. |
| Logs | `logs.persistence.*`, `workers.celery.persistence.*`, `elasticsearch.*`, `opensearch.*`, `config.logging.*` | Task and component log storage/retrieval | No persistence means pod-lifetime logs only. RWX PVCs need compatible storage and permissions. |
| Ingress and services | `ingress.apiServer.*`, `apiServer.service.*`, `ports.*`, network policies | Expose UI/API and component services | Configure proxy headers and TLS at the owning component; avoid top-level catch-all ingress patterns. |
| Autoscaling | `workers.celery.keda.*`, `workers.celery.hpa.*`, `apiServer.hpa.*`, `triggerer.keda.*` | Scale workers, API server, and triggerer | Do not enable KEDA and HPA for the same worker target; KEDA requires cluster-side KEDA CRDs. |
| Observability | `statsd.*`, `otelCollector.*`, `config.metrics.*`, `config.traces.*` | Metrics/traces collection | OpenTelemetry is the preferred chart-level telemetry path in current chart guidance. |
| Security/RBAC | `rbac.*`, `securityContexts.*`, component `serviceAccount`, network policies, pod security | Permissions and runtime identity | Defaults should stay least-privilege; ensure mounted volumes are writable by the Airflow user/group model. |

## Airflow 3 component map

| Component | Chart area | Template/resource pattern | Notes |
|---|---|---|---|
| API server | `apiServer`, `ingress.apiServer`, `config.api`, `config.api_auth` | `api-server` Deployment, Service, HPA, Ingress/HTTPRoute, ServiceAccount, PDB | Replaces the Airflow 2 webserver naming. It serves UI and public REST API. |
| Scheduler | `scheduler` | `scheduler` Deployment, Service, NetworkPolicy, ServiceAccount, PDB | Schedules from serialized Dags; it does not run user Dag code. |
| Dag processor | `dagProcessor` | `dag-processor` Deployment, ServiceAccount, PDB | Airflow 3 uses a separate Dag processor. Review resources and access to Dag code. |
| Triggerer | `triggerer`, `triggerer.keda` | `triggerer` Deployment, KEDA ScaledObject, Service, ServiceAccount, PDB | Deferred task capacity and scaling live here. |
| Celery workers | `workers.celery`, `workers.celery.sets`, `workers.celery.keda`, `workers.celery.hpa` | `worker` Deployment/StatefulSet, KEDA/HPA, ServiceAccount, PDB | Queue-specific worker sets can override parent worker values. |
| Kubernetes workers | `workers.kubernetes`, `podTemplate`, `images.pod_template`, `config.kubernetes_executor` | Pod template rendered into config | Worker image may be overridden by Kubernetes executor config values. |
| Redis | `redis`, `images.redis`, `data.brokerUrl*` | Redis StatefulSet, Service, Secret, NetworkPolicy | Bundled Redis supports quick starts; external broker is common for production. |
| PgBouncer | `pgbouncer`, `images.pgbouncer*` | PgBouncer Deployment, Service, Secrets, metrics exporter | Used mainly for PostgreSQL connection pooling. |
| Metadata database | `postgresql`, `data.metadata*` | Optional PostgreSQL subchart and generated/existing connection Secret | Bundled Postgres is not recommended for production. |
| Migrations | `migrateDatabaseJob`, `images.useDefaultImageForMigration`, `images.migrationsWaitTimeout` | Migration Job and wait init containers | The chart normally runs database migrations during install/upgrade. |
| Database cleanup | `databaseCleanup` | CronJob and ServiceAccount | Periodic `airflow db clean` for metadata retention. |
| Logs PVC | `logs.persistence` | Logs PersistentVolumeClaim | Requires storage with suitable access mode and permissions. |
| Dags PVC/git-sync | `dags.persistence`, `dags.gitSync` | Dags PVC and git-sync sidecars/init containers | See `references/deployment-workflows.md` for delivery trade-offs. |

## Safe no-cluster checks

These checks should be the default starting point because they do not require Kubernetes API access.

```bash
python skills/apache-airflow/sub-skills/deployment-helm-docker/scripts/render_helm_values_summary.py values.yaml
```

Use the bundled summarizer to identify enabled components, likely secret leaks, conflicting scaling settings, and common Dag/log/storage risks. It does not render templates, so it complements Helm checks rather than replacing them.

If Helm is available, render the published chart locally:

```bash
helm repo add apache-airflow https://airflow.apache.org
helm repo update
helm template airflow apache-airflow/airflow --namespace airflow -f values.yaml > rendered.yaml
```

When the user is actively changing chart source, use the chart directory they provide for `helm lint` and `helm template`; otherwise prefer the published chart reference.

For an installed release, a review workflow can include diffing before upgrade:

```bash
helm diff upgrade airflow apache-airflow/airflow --namespace airflow -f values.yaml
helm upgrade --install airflow apache-airflow/airflow --namespace airflow -f values.yaml --dry-run
```

Use live commands such as `kubectl get pods`, `kubectl describe`, or `helm status` only when the user explicitly asks for live cluster troubleshooting and has provided the target context expectations. Do not assume cluster access for normal skill usage.

## Chart development checks

When the user is changing the Airflow Helm chart itself, prefer chart-specific tests and docs checks instead of broad Kubernetes e2e tests:

```bash
breeze testing helm-tests --use-xdist
breeze testing helm-tests --use-xdist --test-type airflow_core
breeze testing helm-tests --use-xdist --test-type apiserver
breeze testing helm-tests --use-xdist --test-type dagprocessor
breeze testing helm-tests --use-xdist --test-type other
breeze testing helm-tests --use-xdist --test-type redis
breeze testing helm-tests --use-xdist --test-type security
breeze testing helm-tests --use-xdist --test-type statsd
```

For chart-only changes, rendered manifest tests commonly assert template output for:

- Component labels, service accounts, resources, ports, probes, annotations, env vars, and volume mounts.
- Secret rendering and mutual exclusion checks for inline connection data versus existing Secret names.
- git-sync sidecar/init-container placement for persistence and executor combinations.
- KEDA/HPA resources and SQL query generation for worker scaling.
- Remote logging, log PVCs, and Elasticsearch/OpenSearch secret behavior.

If values rules or generated chart docs change, keep generated documentation and tests in sync. Do not hand-edit generated reference tables when the repository has a generation path.

## Upgrade cautions

- Airflow 3 chart upgrades require `defaultAirflowTag` and `airflowVersion` to target Airflow 3. The chart in this evidence set supports Airflow `3.1.0` and above.
- Rename Airflow 2 `webserver` values to Airflow 3 `apiServer` values. The API server now serves the UI and public API.
- Move the API secret key to `[api] secret_key`; Airflow 3 also needs `[api_auth] jwt_secret` for short-lived JWT authentication between components.
- Ensure a `jwt-secret` key exists when using `jwtSecretName`, and prefer stable externally managed secrets for production rollouts.
- Deploy and size the standalone `dagProcessor` component; do not assume the scheduler parses Dags in-process.
- The default auth manager may rely on the FAB provider. If using a different auth manager, set `config.core.auth_manager` and ensure the image contains the required provider.
- Custom plugins that previously depended on webserver/FAB behavior may need the FAB provider and new `apiServer` mounting/configuration.
- Before upgrading, render locally with `helm template`, inspect diffs, and verify the migration job completes before sending traffic to new components.

## Values review checklist

Use this checklist when asked to draft or review a production-like values file:

1. Confirm executor choice and required backing services: Redis/broker for Celery, pod-launch RBAC for Kubernetes, worker sets or queues if multiple execution environments are used.
2. Confirm image source, tag/digest, pull policy, and whether the image already contains all providers and Dag dependencies.
3. Confirm external metadata database and optional PgBouncer. Bundled Postgres is for quick starts, not durable production.
4. Confirm static Fernet, API, and JWT secrets. Avoid inline passwords in values; prefer existing Secret names.
5. Confirm Dag delivery: immutable image, Airflow 3 bundles, git-sync, or PVC. Avoid combining git-sync with networked persistence unless the storage behavior is understood and monitored.
6. Confirm logging: no persistence, worker-only persistence, RWX logs PVC, or remote log backend. Check permissions for mounted volumes.
7. Confirm resource requests/limits, PDBs, priority classes, node placement, and network policies per component.
8. Confirm KEDA/HPA configuration does not target the same workload twice, and that KEDA SQL uses the same worker concurrency value as the workers.
9. Render manifests locally and inspect Secret, ConfigMap, volume, init-container, service account, and scaling resources before live upgrade.
