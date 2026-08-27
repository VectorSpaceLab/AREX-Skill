# Remote Workflows

## Purpose

Read this for the normal LabML remote-project lifecycle: bootstrap, sync,
prepare, run, and launch distributed jobs.

## 1) Bootstrap a project

1. Run `labml_remote init` in the project directory.
2. Fill in the project name, host, username, and private key prompts.
3. Confirm that `.remote/configs.yaml` and `.remote/exclude.txt` were created.
4. Add at least one server entry before using the runtime commands.

## 2) Prepare a server

Use `prepare` when you want the full setup flow in one command.

1. `setup` installs Python with conda on the server.
2. `rsync` copies the project files.
3. `update-packages` installs dependencies from `requirements.txt` or a
   `Pipfile`.
4. `prepare` does all three in sequence.

This flow is the one to use when the remote host is new or has been reset.

## 3) Run commands and background jobs

- Use `run` for a foreground command on one server.
- Use `job-run` for background work that should keep logs and a job record.
- Use `job-list` to inspect the tracked jobs.
- Use `job-tail` to watch a job's latest output.
- Use `job-kill` to stop a tracked job.

The job system stores per-job metadata locally and syncs outputs back to the
client machine.

## 4) Launch distributed PyTorch jobs

`helper-torch-launch` is the distributed-training helper.

- It computes `RUN_UUID` once and shares it across all processes.
- It derives `MASTER_ADDR`, `MASTER_PORT`, `WORLD_SIZE`, `NODE_RANK`, `RANK`,
  and `LOCAL_RANK` for each process.
- It optionally passes `--local_rank` unless `--use-env` is set.
- It works best when the remote project already has the expected Python stack.

This helper is the right choice when you want the remote job manager to fan out
training processes across one or more configured servers.

## 5) Avoid common sync mistakes

- Keep the exclude file up to date so generated logs, caches, and virtual
  environments do not get copied.
- Make sure the private key file path is correct before running `prepare`.
- Confirm that the server has the right Python packages before launching jobs
  that import PyTorch or other heavy libraries.

## 6) When to use the smoke script

Use `scripts/remote_config_smoke.py` when you want to validate the local config
file generation and configuration parsing without reaching a real server.
