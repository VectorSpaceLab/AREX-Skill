# Remote Execution CLI Reference

This reference covers `clearml-task`, `clearml-init`, and `clearml-debug` surfaces needed to prepare, launch, and diagnose remote ClearML jobs without relying on external repository files.

## `clearml-task` Purpose

`clearml-task` creates a ClearML task from a repository, local git folder, script, module, existing base task, or offline session. When `--queue` is supplied, it enqueues the created task for execution by a `clearml-agent`; without `--queue`, it leaves the task in draft mode.

The command prints a new task or pipeline id on success and contacts the configured ClearML server. Build and review commands before running them.

## Required Identity Flags

- `--project PROJECT`: ClearML project name. Required for normal task creation; optional when cloning with `--base-task-id`.
- `--name NAME`: ClearML task name. Required unless importing an offline session.
- `--tags TAGS...`: Optional tags added after task creation.
- `--task-type TASK_TYPE`: One of `training`, `testing`, `inference`, `data_processing`, `application`, `monitor`, `optimizer`, `service`, `qc`, or `custom`; ignored when `--pipeline` is used.

## Code Source Flags

- `--repo REPO`: Remote repository URL to clone on the agent.
- `--branch BRANCH`: Branch or tag to use; implies latest commit on that branch/tag unless `--commit` is also set.
- `--commit COMMIT`: Specific commit id. With a local folder, the local commit id and diff are captured.
- `--folder FOLDER`: Local git folder to remotely execute. ClearML records the repository state and uncommitted diff for reproduction.
- `--skip-repo-detection`: Do not infer a repository when `--repo` is absent. Use only when source capture is intentionally disabled or not possible.

## Entrypoint Flags

- `--script SCRIPT`: Entrypoint script. Supports `.py`, `.ipynb`, and `.sh`. With `--repo`, use a path relative to the repo root. With `--folder`, use a path inside the local git folder. A `.sh` script defaults to `/bin/bash` when `--binary` is omitted.
- `--module MODULE`: Python module command instead of `--script`; cannot be used with `--script`.
- `--binary BINARY`: Launcher binary such as `python3` or `/bin/bash`; otherwise ClearML auto-detects.
- `--cwd CWD`: Working directory relative to the repo/folder root.
- `--args KEY=VALUE...`: Arguments passed to the remote execution. The CLI validates only `key=value` format for pipeline creation; keep the same format for tasks because ClearML updates argparse-style parameters.

## Queue and Environment Flags

- `--queue QUEUE`: Queue to enqueue on. If omitted, the task is created but not launched.
- `--requirements REQUIREMENTS`: Requirements file to install. If omitted, the repository `requirements.txt` may be used.
- `--packages PACKAGES...`: Manual packages to install, such as `--packages "tqdm>=4" "pandas"`.
- `--force-no-requirements`: Force no requirements and no package list.
- `--skip-python-env-install`: Ask Docker/Kubernetes agents to use the preexisting Python environment by adding `CLEARML_AGENT_SKIP_PYTHON_ENV_INSTALL=1` to Docker args.
- `--docker DOCKER`: Docker image for the remote session.
- `--docker_args DOCKER_ARGS`: Single string of Docker runtime arguments.
- `--docker_bash_setup_script DOCKER_BASH_SETUP_SCRIPT`: Bash text or a path to a bash setup script. If a file path is supplied, ClearML reads the file and strips an initial shebang.
- `--output-uri OUTPUT_URI`: Default upload destination for model outputs.

## Task Creation Variants

- `--skip-task-init`: Do not inject `Task.init()` into the entrypoint. Use this when the script already initializes ClearML or when automatic insertion is unsafe.
- `--base-task-id BASE_TASK_ID`: Clone an existing task instead of building from a repo/script; project becomes optional.
- `--import-offline-session PATH`: Import a ClearML offline session folder or zip. Task name is not required for this path.
- `--pipeline`: Create a pipeline object instead of a regular task; route deeper pipeline design to `../automation-pipelines/SKILL.md`.
- `--pipeline-version VERSION`: Pipeline version when `--pipeline` is set.
- `--pipeline-dont-add-run-number`: Disable automatic pipeline run-number suffix when `--pipeline` is set.

## `clearml-init`

`clearml-init` is an interactive configuration wizard. It accepts:

- `--file FILE` / `-F FILE`: Target configuration file path. If omitted, ClearML uses its default config file discovery.

Use it when the user needs to create a config file from copied web UI credentials. It verifies credentials against the API server and writes the SDK configuration. Do not automate it in non-interactive environments unless the user provides a safe secret-handling plan.

## `clearml-debug`

`clearml-debug` provides read/debug commands and may contact the ClearML server:

- `clearml-debug token`: Print decoded token details. This can expose sensitive information; avoid unless explicitly requested.
- `clearml-debug config dump`: Dump resolved configuration.
- `clearml-debug config dump --format {json,yaml,dict,hocon}` / `-F`: Choose output format.
- `clearml-debug config dump --indent N` / `-I`: Set indentation.
- `clearml-debug config dump --path PATH` / `-p`: Dump a config subtree such as `api` or `sdk.aws.s3`.
- `-v` / `--verbose`: Print connection/version context before the action.

Prefer this sub-skill's `validate_clearml_environment.py` script for a safe preflight signal check because it does not print secret values or resolved config contents.

## Command Templates

### Local Git Folder Script

```bash
clearml-task \
  --project "PROJECT" \
  --name "TASK_NAME" \
  --folder "." \
  --script "train.py" \
  --args lr=0.003 batch_size=64 \
  --requirements "requirements.txt" \
  --docker "python:3.11-slim" \
  --output-uri "s3://bucket/path" \
  --queue "default"
```

Add `--skip-repo-detection` only when repository capture is intentionally disabled. For local folders, prefer leaving detection enabled so ClearML records commit and diff.

### Remote Repository Script

```bash
clearml-task \
  --project "PROJECT" \
  --name "TASK_NAME" \
  --repo "https://example.com/org/repo.git" \
  --branch "main" \
  --script "src/train.py" \
  --requirements "requirements.txt" \
  --queue "gpu"
```

### Python Module Entrypoint

```bash
clearml-task \
  --project "PROJECT" \
  --name "TASK_NAME" \
  --repo "https://example.com/org/repo.git" \
  --module "package.train" \
  --args epochs=5 \
  --queue "default"
```

### Existing Task Clone

```bash
clearml-task \
  --name "CLONED_TASK_NAME" \
  --base-task-id "TASK_ID" \
  --args General/epochs=10 \
  --queue "default"
```

### Offline Session Import

```bash
clearml-task --import-offline-session "offline-session.zip"
```

### CI/CD Remote Runnable Check

A typical CI job sets `CLEARML_API_ACCESS_KEY`, `CLEARML_API_SECRET_KEY`, and `CLEARML_API_HOST` as secrets, installs `clearml`, runs a `clearml-task` command with `--branch`, `--script`, `--requirements`, `--skip-task-init`, and `--queue`, then polls the created task id until it reports progress. Keep the polling script in the user's project because it necessarily contacts the ClearML server.
