# Remote Launch Workflows

Use these patterns to decide whether to create a ClearML task from the CLI, create one programmatically, clone an existing task, enqueue a task, or switch a local script into remote execution.

## Pattern Selection

- Use `clearml-task` when building CI/CD commands, launching a repository from the shell, importing offline sessions, or producing a command for humans to review.
- Use `Task.create()` when Python code needs to create a task definition programmatically from repo/script/module/package/docker metadata.
- Use `Task.clone()` plus `Task.enqueue()` when starting from an existing task template and overriding parameters separately.
- Use `task.execute_remotely()` inside a script when the script should run a small local preflight and then continue on a ClearML agent.
- Use `clearml-init` only for interactive setup; use environment variables or an existing config file for non-interactive CI.

## Local Folder Launch

Use a local git folder when the user is developing locally and wants ClearML to capture the current commit and uncommitted diff.

1. Confirm the folder is a git checkout and contains the entry script.
2. Use `--folder` and an entry `--script` inside that folder.
3. Keep repo detection enabled unless the user intentionally wants no source capture.
4. Specify requirements/packages/Docker explicitly when remote agents may not match the local environment.
5. Add `--queue` only after confirming an agent is polling that queue.

Template:

```bash
clearml-task --project "PROJECT" --name "TASK_NAME" --folder "." --script "train.py" --requirements "requirements.txt" --queue "default"
```

If the script already calls `Task.init()`, add `--skip-task-init` to avoid duplicated initialization.

## Remote Repository Launch

Use a remote repository when CI/CD or a shared branch/commit should be reproduced by an agent.

1. Provide `--repo` with a cloneable URL.
2. Pin at least `--branch`; use `--commit` for exact reproducibility.
3. Use repo-relative `--script` or `--module`.
4. Supply `--requirements` or `--packages` unless the repository default requirements are correct.
5. Use Docker when agent host environments are heterogeneous.

Template:

```bash
clearml-task --project "PROJECT" --name "TASK_NAME" --repo "https://example.com/org/repo.git" --branch "main" --script "src/train.py" --docker "python:3.11" --queue "gpu"
```

## Module Entrypoint

Use `--module` when the remote invocation should resemble `python -m package.module` or a module command. Do not combine `--module` with `--script`.

Template:

```bash
clearml-task --project "PROJECT" --name "TASK_NAME" --repo "https://example.com/org/repo.git" --module "package.train" --args epochs=5 --queue "default"
```

## Existing Task Clone

Use an existing base task when the ClearML server already has the source, environment, and parameters captured.

CLI path:

```bash
clearml-task --name "CLONE_NAME" --base-task-id "TASK_ID" --args General/lr=0.001 --queue "default"
```

SDK path:

```python
from clearml import Task

base_task = Task.get_task(task_id="TASK_ID")
cloned_task = Task.clone(source_task=base_task, name="CLONE_NAME")
Task.enqueue(cloned_task, queue_name="default")
```

`Task.clone(source_task, name=None, comment=None, parent=None, project=None)` returns a cloned `Task`. `Task.enqueue(task, queue_name=None, queue_id=None, force=False)` enqueues by queue name or id.

## Programmatic Task Creation

Use `Task.create()` when Python code must build task definitions without shelling out.

Important parameters from the live API include:

- Identity: `project_name`, `task_name`, `task_type`.
- Source: `repo`, `branch`, `commit`, `script`, `working_directory`, `module`, `detect_repository`.
- Environment: `packages`, `requirements_file`, `docker`, `docker_args`, `docker_bash_setup_script`, `binary`.
- Behavior: `base_task_id`, `add_task_init_call`, `force_single_script_file`, `argparse_args`.

Template:

```python
from clearml import Task

task = Task.create(
    project_name="PROJECT",
    task_name="TASK_NAME",
    repo="https://example.com/org/repo.git",
    branch="main",
    script="src/train.py",
    requirements_file="requirements.txt",
    docker="python:3.11",
    argparse_args=[("epochs", "5")],
)
Task.enqueue(task, queue_name="default")
```

Use `detect_repository=False` only when repository discovery should be skipped.

## Execute Remotely From a Script

Use `Task.execute_remotely(queue_name=None, clone=False, exit_process=True)` after `Task.init()` when local execution should stop and resume on an agent. When already running under a ClearML agent, the call is a no-op for the main task.

Behavior to remember:

- `queue_name` is required for actual enqueueing. If omitted, the task is reset/draft-like and the local process may exit.
- `clone=True` creates and enqueues a cloned copy while preserving the local task.
- `clone=False` enqueues the same task and requires `exit_process=True`.
- `exit_process=True` terminates the local process after enqueueing.
- The method is supported on the main `Task` created with `Task.init()`; on non-main tasks, ClearML warns and falls back to clone/enqueue behavior.

Template:

```python
from clearml import Task

task = Task.init(project_name="PROJECT", task_name="TASK_NAME")
# Optional local sanity checks here.
task.execute_remotely(queue_name="default", clone=False, exit_process=True)
# Heavy training code continues here on the agent.
```

## Offline Session Import

Use offline import when a task was recorded in ClearML offline mode and needs to be uploaded later.

CLI:

```bash
clearml-task --import-offline-session "offline-session.zip"
```

SDK:

```python
from clearml import Task

new_task_id = Task.import_offline_session("offline-session.zip")
```

The SDK accepts a session folder or zip file. It reads the offline task object, imports task data, uploads available artifacts/models through the configured storage target, and reports offline logs/metrics.

## Docker, Requirements, and Package Choices

- Prefer `--requirements requirements.txt` for repository-controlled dependencies.
- Use `--packages` for a short explicit dependency list or when no requirements file exists.
- Use `--force-no-requirements` only when the agent image already contains every needed dependency.
- Use `--skip-python-env-install` only for Docker/Kubernetes agents with a prebuilt environment; it appends `CLEARML_AGENT_SKIP_PYTHON_ENV_INSTALL=1` to Docker args.
- Use `--docker` to stabilize CUDA, Python, and system packages across agent hosts.
- Use `--docker_args` for runtime flags and `--docker_bash_setup_script` for setup commands needed inside the container.

## CI/CD Command Pattern

1. Store ClearML credentials as CI secrets: access key, secret key, and API host.
2. Install `clearml` in the CI job.
3. Build a `clearml-task` command with branch/commit, entrypoint, requirements, `--skip-task-init` if the script already calls `Task.init()`, and a target queue.
4. Capture the created task id from command output.
5. Poll task status or last iteration through the SDK only if the CI job is allowed to contact the ClearML server.

This pattern is side-effectful. In a repo skill context, provide templates and command builders; do not run CI launch commands without explicit user approval.
