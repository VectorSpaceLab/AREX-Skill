# Remote Execution Troubleshooting

Use this checklist when `clearml-task`, `Task.create`, `Task.enqueue`, or `Task.execute_remotely` does not create, enqueue, or run a task as expected.

## Preflight Without Side Effects

- Run `scripts/validate_clearml_environment.py` to check whether credential/config signals exist without printing secrets.
- Run `scripts/build_clearml_task_command.py` to validate a command shape before contacting a server.
- Confirm a ClearML agent is polling the intended queue before enqueueing; otherwise tasks remain queued.
- Confirm the selected code source, entrypoint, requirements/packages, Docker image, and queue all describe the same runnable environment.

## Missing Project, Name, or Entrypoint

Symptoms:

- `Task name must be provided, use --name <task-name>`.
- Task creation fails before server-side launch.
- The task is created but has no meaningful script/module to run.

Fixes:

- Supply `--project` and `--name` for normal task creation.
- `--project` may be omitted only when `--base-task-id` is used and the base task supplies enough context.
- `--name` may be omitted only with `--import-offline-session`.
- Choose exactly one entry style: `--script`, `--module`, `--base-task-id`, or `--import-offline-session`.
- Do not combine `--script` and `--module`.

## Missing Queue or No Agent Polling

Symptoms:

- `clearml-task` succeeds but prints that no queue was provided and leaves the task in draft mode.
- Task status remains `queued`.
- CI polling times out waiting for iterations.

Fixes:

- Add `--queue QUEUE` when the intent is actual remote execution.
- Verify a `clearml-agent` is running and listening to that exact queue name.
- Check that the queue is appropriate for the requested Docker/GPU/CPU workload.
- If a task should remain editable for later launch, omit `--queue` intentionally and document that it is draft-only.

## Credentials and Configuration

Symptoms:

- Authentication or connection errors when creating/enqueueing tasks.
- `clearml-debug config dump` fails to connect.
- CI works locally but not in the runner.

Fixes:

- Provide `CLEARML_API_ACCESS_KEY`, `CLEARML_API_SECRET_KEY`, and `CLEARML_API_HOST` as environment variables, or run `clearml-init` to create a config file.
- Use `CLEARML_CONFIG_FILE` when a non-default config file should be used.
- Ensure API, web, and files server URLs are not confused; `clearml-init` infers API/files hosts from common web host patterns.
- Avoid `clearml-debug token` unless the user explicitly accepts sensitive output risk.
- Never paste or log secret values; report presence/absence only.

## Repository Detection and Source Capture

Symptoms:

- The agent cannot clone the repository.
- The task captures the wrong folder, branch, or uncommitted diff.
- Local changes are missing remotely.
- ClearML complains about missing repository/script entries.

Fixes:

- Use `--repo` for a remote cloneable URL and `--branch`/`--commit` for reproducibility.
- Use `--folder` for a local git checkout when ClearML should capture commit and uncommitted changes.
- Keep `--script` relative to the repo root for `--repo`; keep it inside the local checkout for `--folder`.
- Use `--skip-repo-detection` only when intentionally launching without repository metadata.
- If repository detection is slow before `execute_remotely(clone=True)`, remember ClearML waits for repository/package detection before cloning.

## Requirements, Packages, and Docker

Symptoms:

- Agent starts but fails during environment setup.
- Package versions differ between local and remote.
- Docker task starts but uses an unexpected Python environment.
- Requirements and package flags contradict each other.

Fixes:

- Choose one clear dependency strategy: repository `requirements.txt`, explicit `--requirements`, explicit `--packages`, or prebuilt Docker with `--force-no-requirements` / `--skip-python-env-install`.
- Do not use `--force-no-requirements` if the agent image lacks dependencies; it intentionally clears requirements and packages.
- Use `--skip-python-env-install` only for Docker/Kubernetes agents with preinstalled dependencies.
- When using `--docker_bash_setup_script`, pass either inline bash text or a script file path that exists where the command is run; ClearML reads the file before creating the task.
- Pin Docker image tags instead of using mutable defaults when CI reproducibility matters.

## `--skip-task-init` and Script Initialization

Symptoms:

- Duplicate task initialization.
- Task is created but script metrics/logs are not connected as expected.
- `clearml-task` modifies an entrypoint in a way the user did not expect.

Fixes:

- Add `--skip-task-init` when the target script already calls `Task.init()`.
- Omit `--skip-task-init` when launching a plain script and you want `clearml-task` to inject ClearML initialization.
- For metrics/artifacts inside the script, route to `../experiment-tracking/SKILL.md`.

## Shell Scripts and Binary Selection

Symptoms:

- Shell entrypoints run with the wrong binary.
- `.sh` script launch behavior differs from Python scripts.

Fixes:

- `.sh` scripts are detected and default to `/bin/bash` if `--binary` is omitted.
- Use `--binary /bin/bash` explicitly when clarity matters.
- Ensure shell scripts are included in the repo/folder and are executable or runnable by the selected binary.

## Offline Session Import

Symptoms:

- Import fails with missing offline task object.
- Import succeeds but artifacts/models are missing.
- Import uploads to an unexpected storage destination.

Fixes:

- Pass a valid offline session folder or zip to `--import-offline-session` or `Task.import_offline_session()`.
- Ensure the session contains the ClearML offline task metadata file and any referenced data files.
- Configure storage/output URI before import when model/artifact upload destination matters.
- Remember import contacts the ClearML server and may upload artifacts.

## SDK Remote Execution Edge Cases

Symptoms:

- `execute_remotely()` does nothing on an agent.
- Local process exits unexpectedly.
- ValueError about `clone==False` and `exit_process==False`.

Fixes:

- `execute_remotely()` is a no-op for the main task when already running remotely.
- If `clone=False`, keep `exit_process=True`; ClearML requires the local process to exit after enqueueing itself.
- Use `clone=True, exit_process=False` when the local process should continue after creating a remote clone.
- Provide `queue_name` for actual enqueueing.
- Call it on the main task returned by `Task.init()`; non-main tasks fall back to clone/enqueue behavior with warnings.

## Inconsistent User Request Triage

When the request mixes incompatible choices, stop and clarify or produce a corrected command with notes:

- Both `--script` and `--module` were requested: choose one.
- `--force-no-requirements` plus `--requirements`/`--packages`: either clear dependencies intentionally or remove the force flag.
- `--skip-python-env-install` without Docker/Kubernetes/prebuilt environment: ask how dependencies are provided.
- `--queue` names a GPU queue but Docker image lacks CUDA/runtime support: ask for a compatible image or CPU queue.
- Local folder launch with `--skip-repo-detection`: warn that source capture will be disabled.
