# Remote Troubleshooting

## Purpose

Read this when remote setup, sync, or job orchestration fails.

## Common issues

### `labml_remote` warns that no servers were found

**Symptoms**
- The CLI prints `No servers found. Run labml_remote init...`.

**Likely cause**
- The project has no `.remote/configs.yaml` file or no `servers` entry.

**Recovery**
- Run `labml_remote init` in the project directory.
- Add at least one server entry and re-run the command.

### SSH key or username problems

**Symptoms**
- Authentication errors when the tool tries to connect.
- Permission denied messages from SSH.

**Likely cause**
- The username, host, or private key path is wrong.
- The key file has permissive permissions or does not match the server.

**Recovery**
- Re-check the `hostname`, `username`, and `private_key` settings.
- Fix the key permissions and confirm that SSH works manually first.

### `setup` or `prepare` cannot install Python on the server

**Symptoms**
- Conda setup fails, or the server stays on an old Python version.

**Likely cause**
- Conda is missing or the remote host lacks the expected shell/runtime tools.

**Recovery**
- Confirm that the server can install conda and that the shell can run it.
- Retry `prepare` after the server-side Python stack is healthy.

### `rsync` copies too much or too little

**Symptoms**
- Unwanted caches or logs show up on the server.
- Expected files are not present on the server.

**Likely cause**
- `.remote/exclude.txt` is missing a pattern or is too broad.

**Recovery**
- Edit the exclude file and re-run `rsync`.
- Compare the local project tree with the synced tree before launching jobs.

### `job-tail` never updates

**Symptoms**
- The tail command shows old output only.

**Likely cause**
- The job is not running, the sync interval is too long, or the remote job never
  started.

**Recovery**
- Run `job-list` first.
- Sync the job metadata with `job-rsync`.
- Confirm the job actually started on the server.

### Distributed launch variables look wrong

**Symptoms**
- The launched processes do not agree on rank, world size, or master address.

**Likely cause**
- The configured server list or `--nproc-per-node` value does not match the
  intended topology.

**Recovery**
- Re-check the server list and the helper options.
- Verify the generated environment variables with the workflow reference.

### The server cannot import a training package

**Symptoms**
- The remote command fails after sync because the package stack is incomplete.

**Likely cause**
- The remote host has not been prepared with the required dependencies.

**Recovery**
- Run `prepare` or `update-packages` again.
- If the remote script uses GPU training, confirm that CUDA and the driver are
  already available on the host image; the remote tool does not install them.

## Read next

- `remote/scripts/remote_config_smoke.py` for a local config sanity check.
- `remote/references/cli-reference.md` for the exact command set and options.
