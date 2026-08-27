# ZenML Setup and Package Facts

Use this reference when deciding how to install, import, or inspect ZenML before using a focused sub-skill.

## Verified Package Facts

- Distribution name: `zenml`.
- Import root: `zenml`.
- Version at skill generation: `0.95.1`.
- Python requirement from package metadata: `>=3.10,<3.15`.
- Console script: `zenml = zenml_cli:cli`.
- Base install includes Click, Docker SDK, GitPython, Pydantic v2, Rich, PyYAML, Structlog, OpenTelemetry logging SDK, `psutil`, `cloudpickle`, `jsonref`, and packaging utilities.

Safe probes:

```bash
python -c "import zenml; print(zenml.__version__)"
zenml --help
python scripts/check_zenml_environment.py --json
```

## Extras Policy

Install the smallest extra that matches the task.

| Need | Suggested extra | Notes |
| --- | --- | --- |
| Core pipeline authoring, CLI help, public APIs | base `zenml` | Start here for most code-writing and static guidance tasks. |
| Local SQL store/server-adjacent development | `zenml[local]` | Adds Alembic/SQLAlchemy/SQLModel and local DB dependencies. |
| Run local ZenML server or server internals | `zenml[server]` | Adds FastAPI, Uvicorn, auth, multipart, JWT, and server runtime packages. |
| OpenTelemetry server instrumentation | `zenml[otel]` | Add only when tracing/instrumentation behavior is in scope. |
| Redis-backed streaming | `zenml[server-streaming]` | Add only for streaming/SSE backend tasks. |
| Templates | `zenml[templates]` | Adds Copier/Jinja template tooling. |
| Repository maintenance | `zenml[dev]` | Heavy: lint, tests, docs, mypy, pre-commit, and dev tools. |
| Cloud connectors/secrets/filesystems | connector-specific extras | Use `connectors-aws`, `connectors-gcp`, `connectors-azure`, `s3fs`, `gcsfs`, `adlfs`, or secret-store extras only when required. |
| Managed ML platforms | platform-specific extras | Use `sagemaker`, `vertex`, `azureml`, `terraform`, or integration extras only for selected backends. |

Do not install all extras, broad integration dependencies, or dev tooling unless the user’s task requires that coverage.

## Important Public APIs

Live inspection confirmed these surfaces exist and should be verified again when the installed version differs:

- `zenml.pipeline(...)` accepts pipeline-level names, cache/logging flags, environment/secrets, settings dictionaries, tags, hooks, model binding, retry, substitutions, execution mode, and cache policy.
- `zenml.step(...)` accepts step names/types, cache/logging/visualization flags, experiment tracker/step operator binding, output materializers, environment/secrets, settings, hooks, model binding, retry, runtime, heartbeat threshold, group, and cache policy.
- `zenml.config.DockerSettings` controls image build/package behavior such as parent image, requirements, stack requirements, source copy behavior, installer, environment variables, registry/repository, and build options.
- `zenml.config.ResourceSettings` controls CPU/GPU/memory/pool resources, preemptibility, replicas, autoscaling, and concurrency when supported by the execution backend.
- `zenml.config.Schedule` supports names, cron expressions, interval schedules, start/end time, catchup, and one-shot run start time.
- `BaseMaterializer.save(self, data)` and `BaseMaterializer.load(self, data_type)` define custom artifact persistence contracts.
- `BaseOrchestrator.prepare_or_run_pipeline(...)` coordinates pipeline snapshot execution/submission.
- `Stack(...)` composes orchestrator, artifact store, and optional components such as registries, step operators, feature stores, model deployers, experiment trackers, alerters, data validators, image builders, deployers, log stores, and sandboxes.

## CLI Command Families

The top-level Click command includes command families such as:

- `init`, `login`, `logout`, `connect`, `disconnect`, `status`, `info`, `version`, `up`, `down`, `go`.
- Resource commands: `project`, `pipeline`, `deployment`, `artifact`, `model`, `stack`, stack component aliases, `secret`, `tag`, `trigger`, `resource-pool`, `resource-request`, `service-account`, `service-connector`, `authorized-device`.
- Maintenance/server commands: `server`, `backup-database`, `restore-database`, `migrate-database`, `clean`, `downgrade`, `logs`, `logging`, `analytics`.

Use `sub-skills/cli-and-client/scripts/zenml_cli_help_snapshot.py` for non-mutating help snapshots.
