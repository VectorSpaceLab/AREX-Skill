<!-- SPDX-License-Identifier: Apache-2.0 -->

# Cross-Cutting Troubleshooting

Use this reference when a request spans several Airflow surfaces or when a failure does not yet have a clear owner.

## Choose the Right Owner

- Dag parse/import, TaskFlow, Task SDK, assets, Params, XCom, or mapping failures belong in `sub-skills/authoring-task-sdk/`.
- `airflow` CLI, `airflowctl`, REST API, config, auth, metadata DB, scheduler, Dag processor, triggerer, or local component failures belong in `sub-skills/operations-cli-api/`.
- Missing provider packages/extras, custom operators/hooks/sensors, plugin/listener/timetable code, provider metadata, or standard provider imports belong in `sub-skills/providers-extensions/`.
- Docker image, Helm values, Kubernetes manifests, Dag delivery, logs, secrets, migrations, workers, PgBouncer, KEDA, or ingress failures belong in `sub-skills/deployment-helm-docker/`.
- Repository edits, tests, docs, generated files, selective checks, PR prep, or code-review policy belong in `sub-skills/contribution-tooling/`.

## Install and Import Problems

- Prefer Airflow's published constraints when installing `apache-airflow`; unconstrained installs can resolve incompatible dependency sets.
- Match the Airflow version, Python version, and constraint URL. A constraints file for the wrong Python minor can create confusing resolver or import failures.
- Install only provider packages/extras needed by the workflow. Missing `airflow.providers.*` imports usually mean the provider distribution is absent or not installed in the environment used by the scheduler/Dag processor.
- Use `python -c "import airflow, airflow.sdk; print(airflow.__version__, airflow.sdk.__version__)"` to confirm the active Python environment before debugging code.

## Runtime Boundary Problems

- Airflow 3 Dag authoring should use `airflow.sdk`. Direct metadata DB access from task code is not part of the public runtime contract.
- Scheduler-side failures often come from Dag parse/import errors, missing provider packages in the scheduler/Dag processor image, stale serialized Dags, or config pointing at a different Dag bundle.
- API automation should prefer Stable REST API or `airflowctl` when remote access is needed; local `airflow` CLI commands run against the local Airflow configuration and metadata DB.

## Validation Escalation

- For quick environment sanity, run `scripts/check_airflow_skill_environment.py --json` from this skill directory or pass `--skill-root` explicitly.
- For a single Dag file, run the authoring helper in `sub-skills/authoring-task-sdk/scripts/`.
- For CLI command groups, run the operations helper in `sub-skills/operations-cli-api/scripts/`.
- For a provider directory, run the providers helper in `sub-skills/providers-extensions/scripts/`.
- For Helm values without a cluster, run the deployment helper in `sub-skills/deployment-helm-docker/scripts/`.
- For repo changes, use the contribution helper only as a first pass, then refine with Airflow's real selective-checks workflow.

## When to Stop

Stop and ask for explicit user approval before running commands that mutate databases, build or push images, create Kubernetes resources, run release-management flows, use credentials, download large assets, or execute long native test suites.
