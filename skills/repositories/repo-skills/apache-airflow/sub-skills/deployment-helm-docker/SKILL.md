---
name: deployment-helm-docker
description: "Reason about Apache Airflow deployments with the official Helm
  chart and Docker images, including values, image customization, Dag delivery,
  logging, secrets, scaling, and safe rendering checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

<!-- SPDX-License-Identifier: Apache-2.0 -->

# Airflow deployment with Helm and Docker

Use this sub-skill when the task is about deploying Airflow with the official Helm chart, extending or customizing official Docker images, reviewing chart values, planning Kubernetes operational choices, or debugging deployment failures.

## Start here

1. Read `references/deployment-workflows.md` to choose the deployment path: local container image iteration, Helm on Kubernetes, Dag distribution, logs, secrets/config, or scaling.
2. Read `references/helm-reference.md` when reviewing or drafting chart values, rendering manifests safely, or checking component ownership.
3. Read `references/docker-image-reference.md` before advising on packages, providers, image tags, entrypoints, or custom image builds.
4. Read `references/troubleshooting.md` when pods fail to start, rendered manifests are wrong, Dags do not appear, imports fail in the scheduler, logs disappear, migrations hang, or autoscaling behaves oddly.
5. Use `scripts/render_helm_values_summary.py` for a no-cluster, no-Helm summary of a values file before suggesting deeper chart rendering.

## Scope boundaries

This sub-skill covers:

- Official Airflow Docker image extension/customization, dependency installation timing, build arguments, entrypoint behavior, and image selection.
- Helm chart values for API server, scheduler, Dag processor, workers, triggerer, Redis, PgBouncer, metadata database, secrets, logging, Dag delivery, KEDA/HPA, and rendering checks.
- Safe validation commands such as local values summary, `helm template`, `helm lint`, `helm diff`, and chart test selection when the user is already changing chart code.
- Kubernetes deployment reasoning that does not require cluster access by default.

Do not use this sub-skill for:

- Day-to-day Airflow CLI, REST API, `airflowctl`, or metadata operations; route those to `operations-cli-api`.
- Task SDK authoring, Dag syntax, assets, or provider APIs except when deployment packaging affects imports.
- Broad provider implementation deep dives or generated client work.
- General contribution workflow, release workflow, or non-chart CI maintenance except chart-specific rendered manifest tests and generated-doc cautions.

## High-signal reminders

- Prefer building an immutable image for production dependencies. Runtime `pip install` during pod startup is fragile, slow, and repeated on every container start.
- For Airflow 3 chart values, think in components: `apiServer`, `scheduler`, `dagProcessor`, `triggerer`, `workers`, and optional services such as Redis, PgBouncer, StatsD, and OpenTelemetry.
- Treat secrets as Secret references whenever possible. Avoid plain credentials in values files, and never echo secrets into handoffs or generated examples.
- Normal skill usage should not require a Kubernetes cluster. Start with values inspection and local rendering; use cluster commands only when the user explicitly asks for live troubleshooting.
- Use title-case Dag in prose. Preserve literal tokens such as `dags.gitSync`, `airflow dags list`, `DAG`, and `dag_id` exactly when they are code/config/CLI tokens.
