<!-- SPDX-License-Identifier: Apache-2.0 -->

# Deployment troubleshooting

Start with safe local inspection. Do not assume Kubernetes cluster access unless the user explicitly asks for live troubleshooting and provides the context they want inspected.

## Fast triage questions

1. Is the problem in image build, image pull, pod startup, Dag parsing, task execution, chart rendering, migration, logging, or scaling?
2. Which image tag/digest is used by each component, especially Dag processor, scheduler, workers, and KubernetesExecutor pod templates?
3. Which values file changed recently? Run `scripts/render_helm_values_summary.py` before proposing a live rollout.
4. Are credentials stored as existing Secrets or inline values? Redact before sharing.
5. Was this an Airflow 2 to Airflow 3 chart upgrade? Check `apiServer`, `dagProcessor`, `api` secret key, and JWT settings.

## Image build and dependency failures

| Symptom | Likely cause | Safe checks | Fix direction |
|---|---|---|---|
| `pip install` fails with permission errors | Python packages installed as `root` in an extended image | Inspect Dockerfile user switches | Install Python packages as `airflow`; use `root` only for `apt`, then switch back. |
| Import fails with missing `.so` or system library | Python wheel needs an OS package absent from runtime image | Review package docs and image build logs | Add runtime OS package with `apt`; for compiled deps, consider customization with build/runtime split. |
| Airflow version changes unexpectedly after adding a package | Dependency resolver upgraded/downgraded Airflow | Check image build logs or `pip freeze` inside image | Include `apache-airflow==<base-version>` in install command and resolve conflicts explicitly. |
| Packages appear after manual shell install but disappear after restart | Dependencies installed at runtime in a pod/container filesystem | Review startup hooks, init scripts, and Dockerfile | Build dependencies into the image and roll out the new immutable image. |
| Worker can import a provider but Dag processor cannot | Different images or package sets across components | Compare `images.airflow`, `images.pod_template`, and executor config | Ensure parse-time dependencies are in the image used by Dag processor/scheduler and task runtime images. |
| Image cannot pull from registry | Missing pull secret or wrong repository/tag/digest | Render manifests and inspect image references/pull secret names | Configure `imagePullSecrets`/registry Secret and immutable tags/digests. |

Avoid advising runtime `pip install` as a production fix. It is acceptable only as a temporary experiment when the user understands it must become an image build change.

## Chart rendering and values failures

| Symptom | Likely cause | Safe checks | Fix direction |
|---|---|---|---|
| `helm template` fails with Redis/broker errors | Celery executor with Redis disabled and no broker URL/Secret | Check `executor`, `redis.enabled`, `data.brokerUrl`, `data.brokerUrlSecretName` | Provide external broker Secret or enable Redis for non-production/simple setups. |
| Render fails with Elasticsearch/OpenSearch conflict | Both backend values or missing connection/Secret | Check `elasticsearch.*` and `opensearch.*` | Enable only one backend and provide either existing Secret or connection values, not both. |
| Secrets render from inline credentials | Values use `metadataConnection.pass`, `redis.password`, `fernetKey`, etc. | Run values summary and inspect Secret templates locally | Replace inline credentials with existing Secret names where possible. |
| API server settings ignored after Airflow 3 upgrade | Old `webserver` values remain | Search values for `webserver` and old `[webserver] secret_key` | Move settings to `apiServer` and `[api] secret_key`; configure JWT secret. |
| Manifests still use old image | Override set in wrong image field or digest overrides tag | Inspect rendered image fields | Check `defaultAirflowTag`, `images.airflow.*`, digest precedence, and KubernetesExecutor pod template overrides. |
| Values containing `{{` render unexpectedly | Chart `config` values pass through template rendering | Inspect values for literal Go-template delimiters | Escape literal `{{` as a templated string pattern or move content to Secret/ConfigMap as appropriate. |

## Dag delivery failures

| Symptom | Likely cause | Safe checks | Fix direction |
|---|---|---|---|
| Dags do not appear after rollout | Image not updated, git-sync not enabled/configured, wrong subpath, or Dag bundle mismatch | Summarize values and inspect rendered volumes/env | Confirm one delivery strategy and the correct `dags` or `dagProcessor.dagBundleConfigList` settings. |
| Dags appear inconsistently across pods | git-sync with networked persistence or shared filesystem inconsistency | Check `dags.persistence.enabled` plus `dags.gitSync.enabled` | Prefer baked image, Airflow 3 bundles, or git-sync without networked persistence unless storage is tested. |
| Private Git repo sync fails | Missing SSH key, credentials Secret, known hosts, or proxy env | Inspect `dags.gitSync.credentialsSecret`, `sshKeySecret`, `knownHosts`, `envFrom` | Create Secret references and avoid inline private keys in shared values. |
| Scheduler/Dag processor cannot parse provider imports | Custom dependency missing from image used for parsing | Compare image values and Dockerfile | Put provider/import dependencies in the Airflow image used by Dag processor and scheduler. |
| KubernetesExecutor worker starts with old code | Pod template image differs from main Airflow image | Inspect `images.pod_template.*` and `config.kubernetes_executor.worker_container_*` | Align pod template image with Dag/runtime dependency requirements. |

In Airflow prose, write Dag. Preserve literal values such as `dags.gitSync` and `dagProcessor.dagBundleConfigList` exactly.

## Database migrations and connection failures

| Symptom | Likely cause | Safe checks | Fix direction |
|---|---|---|---|
| Migration job hangs or fails connecting | Bad metadata connection Secret, DB network, or credentials | Render migration Job/Secret references; inspect redacted connection source | Fix `data.metadataSecretName` or external DB values; confirm DB reachable from cluster with user-approved live checks. |
| Production deployment uses bundled Postgres | `postgresql.enabled=true` default left in place | Values summary | Disable bundled Postgres and use external database/Secret for production. |
| Many DB connections exhaust database | No PgBouncer or undersized pools | Check `pgbouncer.enabled`, pool sizes, worker count, scheduler/Dag processor count | Enable PgBouncer for PostgreSQL and size pool/client limits. |
| PgBouncer stats/exporter fails | Missing stats Secret or config Secret mismatch | Inspect `pgbouncer.metricsExporterSidecar.statsSecretName` and `pgbouncer.configSecretName` | Provide required Secret keys and matching connection strings. |
| JWT/API auth errors during rollout | Generated secret changed or custom Secret missing key | Check `jwtSecretName`, `apiSecretKeySecretName`, rendered Secret keys | Use stable existing Secrets with expected key names. |

The Helm chart normally runs database migrations. If the built-in migration job is disabled, migration becomes an explicit deployment responsibility.

## Logs are missing or inaccessible

| Symptom | Likely cause | Safe checks | Fix direction |
|---|---|---|---|
| Logs disappear after pod restart | `logs.persistence.enabled=false` and no remote backend | Values summary | Enable remote logging or a suitable persistent volume if retention is required. |
| Celery task logs persist but scheduler logs do not | Worker persistence differs from shared log persistence | Check `workers.celery.persistence` and `logs.persistence` | Choose shared log persistence or remote logging based on requirements. |
| Pods cannot write to log PVC | Volume permissions incompatible with Airflow arbitrary UID/GID model | Inspect storage class, access mode, security context, and mounted path ownership | Ensure volume is writable by the Airflow runtime user/group, commonly group `0`. |
| Remote log backend Secret conflict | Both inline connection and Secret set, or neither set | Check `elasticsearch.*`/`opensearch.*` | Provide exactly one connection source and enable only one remote backend. |
| API server cannot read task logs | Missing pod log RBAC/config or wrong backend settings | Inspect `apiServer.allowPodLogReading`, RBAC, and logging config | Align log backend and read permissions with chosen executor/logging mode. |

## KEDA/HPA and worker scaling issues

| Symptom | Likely cause | Safe checks | Fix direction |
|---|---|---|---|
| Worker replicas behave erratically | KEDA and HPA both enabled for Celery workers | Values summary | Enable only one scaler for a worker target. |
| KEDA ScaledObject not created | KEDA disabled or executor not Celery-based | Check `executor` and `workers.celery.keda.enabled` | Use Celery executor path and enable KEDA values; install KEDA CRDs in cluster separately. |
| Scale calculation seems wrong | Helm value `config.celery.worker_concurrency` differs from worker runtime | Inspect values and rendered KEDA SQL | Set worker concurrency through Helm values so KEDA query matches actual worker concurrency. |
| Scale-to-zero interrupts tasks | Cooldown shorter than shutdown/termination grace period | Check `workers.celery.keda.cooldownPeriod` and worker termination settings | Set cooldown slightly above graceful termination time. |
| KEDA cannot query DB | Missing connection Secret or PgBouncer routing mismatch | Check `workers.celery.keda.usePgbouncer`, `pgbouncer.enabled`, metadata Secret | Align KEDA DB connection with PgBouncer/external DB settings. |
| Queue-specific workers do not scale as expected | Queue list or worker sets mismatch KEDA query | Check `workers.celery.queue` and `workers.celery.sets` | Ensure queues in KEDA SQL match intended worker queues. |

## Kubernetes version and chart compatibility

- The chart evidence for Airflow 3 requires Airflow `3.1.0` or newer.
- Airflow 3 upgrade guidance calls out Kubernetes `1.30+` for chart `1.19.0` and newer.
- If resources fail because an API version is unavailable, render manifests locally and compare against the target cluster version before applying.
- CRD-backed features such as KEDA require the CRDs/controllers to exist in the cluster; the Airflow chart values do not install KEDA itself.

## Safe escalation path

1. Run the values summarizer and inspect the warnings.
2. Render locally with `helm template` if Helm/chart access exists.
3. Inspect rendered images, env vars, Secret references, volumes, service accounts, migration jobs, and scaler resources.
4. Ask the user before live cluster commands or commands that could mutate a release.
5. For live troubleshooting, start read-only: `helm status`, `kubectl get`, `kubectl describe`, and logs for specific failing pods. Avoid upgrades, restarts, or Secret changes without explicit approval.
