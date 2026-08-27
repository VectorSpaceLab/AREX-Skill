# ClearML Cross-Cutting Troubleshooting

Use this reference for package-level failures before drilling into a sub-skill's workflow-specific troubleshooting file.

## Import Or Install Fails

Symptoms:

- `ModuleNotFoundError: No module named 'clearml'`.
- CLI command not found for `clearml-task`, `clearml-data`, `clearml-init`, `clearml-debug`, or `clearml-param-search`.
- Optional storage/router import errors.

Actions:

1. Install the base SDK with `pip install clearml` in the same Python environment that runs the script or CLI.
2. Verify `python -c "import clearml; print(clearml.__version__)"` and `clearml-task --help` from that environment.
3. Install only needed extras: `clearml[s3]`, `clearml[gs]`, `clearml[azure]`, or `clearml[router]`.
4. Use `scripts/clearml_environment_check.py --json` for a read-only signal check.

## Credentials Or Server Are Missing

Symptoms:

- Task initialization cannot connect to a server.
- CLI calls ask for configuration or fail authentication.
- Dataset uploads, remote launches, or router deployment fail before creating work.

Actions:

1. Run `clearml-init` or provide a ClearML configuration file through the standard ClearML configuration mechanism.
2. For environment-based configuration, set `CLEARML_API_HOST`, `CLEARML_API_ACCESS_KEY`, and `CLEARML_API_SECRET_KEY` without printing their values.
3. For no-network execution, use offline mode in the experiment-tracking sub-skill and import the offline session later.

## Remote Tasks Stay Queued

Symptoms:

- `clearml-task` creates a task but it never runs.
- Pipelines or HPO launch controller tasks but child jobs do not execute.
- Scheduler/trigger jobs are created but no worker picks them up.

Actions:

1. Confirm a `clearml-agent` is polling the selected queue.
2. Confirm the task was enqueued; omitting `--queue` in `clearml-task` creates a draft task instead of launching it.
3. Check Docker image, requirements file, packages, repository access, branch/commit, and worker permissions.
4. Route command construction issues to `sub-skills/remote-execution-cli/SKILL.md` and pipeline/HPO queue issues to `sub-skills/automation-pipelines/SKILL.md`.

## Storage Upload Or Download Fails

Symptoms:

- Artifact/model/dataset upload fails.
- S3, Google Cloud Storage, or Azure URL fails to resolve.
- `StorageManager.get_local_copy()` returns no file or downloads stale content.

Actions:

1. Verify the URI scheme and install the matching optional extra.
2. Configure provider credentials through ClearML configuration or provider-default credentials; do not embed secrets in scripts.
3. Use explicit `output_uri` or `Dataset.upload(output_url=...)` when the default files server is not intended.
4. Route dataset lifecycle issues to `sub-skills/data-storage/SKILL.md` and non-dataset artifact/model upload issues to `sub-skills/experiment-tracking/SKILL.md`.

## Router Extra Is Missing

Symptoms:

- `Task.get_http_router()` raises a usage error telling the user to install `clearml[router]`.
- `fastapi`, `uvicorn`, or `httpx` imports are missing.

Actions:

1. Install `clearml[router]` in the runtime environment.
2. Run `sub-skills/routers-services/scripts/router_extra_check.py --json` to inspect optional dependency availability without starting a proxy.
3. Review port binding, telemetry, and callback guidance in `sub-skills/routers-services/references/troubleshooting.md` before deploying.

## Privacy And Secret Handling

- Never print API access keys, secret keys, token payloads, or full credential files.
- Redact environment variables by reporting only whether required signals are present.
- Do not copy local cache paths, virtualenv names, machine-specific paths, or repository checkout paths into user-facing instructions.
