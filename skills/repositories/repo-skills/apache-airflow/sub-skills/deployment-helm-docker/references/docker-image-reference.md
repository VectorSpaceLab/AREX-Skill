<!-- SPDX-License-Identifier: Apache-2.0 -->

# Docker image reference for Airflow deployments

This reference distills how to reason about the official Airflow Docker images when deployment work touches dependencies, providers, Dag code, entrypoints, build arguments, or Kubernetes image values.

## Image strategy

| Strategy | Use when | Advantages | Risks and cautions |
|---|---|---|---|
| Use official reference image directly | Quick start, demos, or deployments whose dependencies are already present | Simple and release-aligned | Missing custom providers, system libraries, or Dag-local dependencies cause parser/task import failures. |
| Extend official image with `FROM apache/airflow:<tag>` | Most teams adding Python packages, providers, apt packages, configs, or Dags | Familiar Dockerfile pattern, fast builds, easy to automate | Can grow large; dependency conflicts must be resolved against the exact Airflow version. |
| Customize/build optimized image | Heavy compiled dependencies, vetted base packages, air-gapped build, custom Airflow sources, or size-sensitive production | More control and smaller runtime images | More complex; requires deeper ownership of build arguments and dependency split. |
| Runtime package install at container start | Hobby/prototype iteration only | Quick experimentation | Fragile, slow, repeated on every start, can differ across pods, and commonly explains imports that work in one component but fail in another. Avoid for production. |

## Extending the official image

Use the `airflow` user for Python package installation and switch to `root` only for OS packages. Always switch back to `airflow` after `apt` work.

Minimal patterns:

```Dockerfile
FROM apache/airflow:3.3.0
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends vim \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
USER airflow
```

```Dockerfile
FROM apache/airflow:3.3.0
RUN pip install --no-cache-dir "apache-airflow==3.3.0" lxml
```

When installing Python dependencies, explicitly pin the same `apache-airflow` version as the base image if the install command could resolve Airflow dependencies. This catches conflicts instead of letting `pip` silently downgrade or upgrade Airflow.

For requirements files:

```Dockerfile
FROM apache/airflow:3.3.0
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir "apache-airflow==3.3.0" -r /requirements.txt
```

For baking Dags into the image:

```Dockerfile
FROM apache/airflow:3.3.0
COPY dags/ ${AIRFLOW_HOME}/dags/
```

Then configure the chart image values:

```yaml
images:
  airflow:
    repository: registry.example.com/team/airflow
    tag: "2026-06-23-a1b2c3d"
    pullPolicy: IfNotPresent
```

Prefer immutable tags or digests for production. Constant tags require `pullPolicy: Always` and a rollout trigger such as a pod annotation change, but constant tags should be limited to development/testing.

## Build arguments and customization concepts

The official production image supports build arguments for full customization. Common arguments include:

| Build argument | Use |
|---|---|
| `AIRFLOW_VERSION` | Airflow version installed in the image. |
| `AIRFLOW_PYTHON_VERSION` | Python version for the image. |
| `AIRFLOW_EXTRAS` | Base Airflow extras included in the image. |
| `ADDITIONAL_AIRFLOW_EXTRAS` | Extra Airflow extras to add. |
| `ADDITIONAL_PYTHON_DEPS` | Extra Python dependencies during image build. |
| `AIRFLOW_HOME` | Airflow home directory, commonly `/opt/airflow`. |
| `AIRFLOW_UID` | Default Airflow user ID, commonly `50000`. |
| `AIRFLOW_CONSTRAINTS` and `AIRFLOW_CONSTRAINTS_REFERENCE` | Constraint source for reproducible dependency resolution. |
| `ADDITIONAL_DEV_APT_DEPS`, `ADDITIONAL_RUNTIME_APT_DEPS` | Split build-time and runtime OS packages for optimized images. |
| `INSTALL_POSTGRES_CLIENT`, `INSTALL_MYSQL_CLIENT`, `INSTALL_MSSQL_CLIENT` | Control database client libraries. |

Use customization when extending creates an image that is too large, when compiled dependencies require build/runtime separation, when sources must come from a private fork, or when security policy requires a vetted package mirror/base image.

## Entrypoint behavior

The production entrypoint performs startup checks and command routing:

- It waits for the Airflow database connection by running an Airflow DB check until success or `CONNECTION_CHECK_MAX_COUNT` is reached. Set `CONNECTION_CHECK_MAX_COUNT=0` only when intentionally disabling this wait.
- For Celery scheduler/worker commands, it waits for the broker connection. Supported broker URL schemes include `amqp(s)://`, `redis://`, `postgres://`, and `mysql://`.
- If the first command is `bash`, `python`, or `airflow`, it runs that command directly. Other arguments are treated as `airflow` subcommands.
- For a custom pre-entrypoint script, keep `dumb-init` and `exec` the original Airflow entrypoint as the final handoff so signal propagation still works.

The image supports arbitrary user IDs when the group ID is `0`. This matters for Kubernetes/OpenShift and mounted volumes:

- Writable directories are designed around group `0` permissions.
- Mounted Dag/log volumes must be writable by the runtime user/group model.
- When creating directories at build time that must later be group-writable, use an appropriate `umask` in the build step.

## Dependency placement rules

Use these rules to debug provider imports and missing packages:

1. The scheduler, Dag processor, API server, triggerer, and workers must all use an image that contains any imports needed to parse Dags or execute tasks.
2. Dag parse-time imports must be present in the Dag processor image. If a provider or library only exists in a worker image, Dag parsing can still fail.
3. Task runtime-only dependencies can sometimes live in isolated task mechanisms such as virtualenv-style task execution, but production deployments usually remain simpler when common provider dependencies are in the Airflow image.
4. System libraries needed by Python wheels must be in the image. Installing a Python package without its required OS library often appears as import or shared-object errors at runtime.
5. Avoid runtime `pip install` in container startup hooks. If packages disappear after restart, differ between pods, or only work after manual shell steps, rebuild the image.

## Chart image alignment

When using the Helm chart:

- `defaultAirflowRepository` and `defaultAirflowTag` set the fallback image for Airflow components.
- `images.airflow.repository`, `images.airflow.tag`, and `images.airflow.digest` override the fallback for Airflow workloads. Digest takes precedence over tag.
- `images.pod_template.repository` and `images.pod_template.tag` apply to KubernetesExecutor pod templates only when not overridden by `config.kubernetes_executor.worker_container_repository` and `worker_container_tag`.
- `images.useDefaultImageForMigration=true` can make migration jobs use the default Airflow image instead of a user-code image. Use carefully if migrations need exactly the same package set or if user code in the image breaks migration pods.
- Private registries require `imagePullSecrets` or the chart's registry Secret wiring.

## Docker image review checklist

When asked to review or design a custom image:

1. Identify the exact base image tag and Airflow version. Keep chart `airflowVersion` and deployed image aligned.
2. List Python packages/providers and OS packages required at Dag parse time versus task runtime.
3. Confirm Python packages are installed as `airflow`, OS packages as `root`, and the Dockerfile switches back to `airflow`.
4. Pin Airflow compatibility explicitly in dependency install commands when dependency resolution can touch Airflow.
5. Avoid secrets in image layers. Use Kubernetes Secrets, environment variables, or secret backends at runtime instead.
6. Prefer immutable image tags/digests and automated rebuilds when Airflow or dependencies change.
7. Check mounted volume ownership and arbitrary UID/GID `0` compatibility.
8. Update Helm values for image repository/tag/digest and pull secrets, then render manifests locally before rollout.

## Why repo scripts are not bundled here

Airflow's source tree includes many Docker and in-container helper scripts for building official images, CI images, provider validation, and development environments. They are intentionally not copied into this runtime skill because they are large, environment-specific, often mutate images or local/container state, and are not needed for future agents to safely reason about user deployment values. This skill provides distilled deployment guidance and one safe static values summarizer instead.
