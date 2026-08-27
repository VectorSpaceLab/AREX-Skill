# Tracking Troubleshooting

## Purpose

Read this when client-side experiment logging, monitoring, or app publishing
fails.

## Common issues

### `.labml.yaml` is missing or points at the wrong project

**Symptoms**
- `labml` warns that the config file is missing.
- Runs are written under an unexpected path.

**Likely cause**
- The project root is not configured or the command is running from the wrong
  directory.

**Recovery**
- Create `.labml.yaml` at the project root.
- Set `path`, `data_path`, and `experiments_path` explicitly.
- Re-run the smoke script to verify the resolved paths.

### `experiment.record` publishes to the app unexpectedly

**Symptoms**
- The run tries to connect to a remote app backend when you only wanted local
  logging.

**Likely cause**
- The default writer set includes the app writer, or `app_url` is configured in
  the project config/environment.

**Recovery**
- Use `writers={"screen", "file"}` when you want a local-only run.
- Check `app_url` in `.labml.yaml` and any `labml_app_url` environment
  variable.

### GPU metrics do not appear in `labml monitor`

**Symptoms**
- CPU and memory counters appear, but GPU counters do not.

**Likely cause**
- `py3nvml` is not installed, the NVIDIA driver is missing, or the host has no
  supported GPU.

**Recovery**
- Install `py3nvml`.
- Confirm `torch.cuda.is_available()` and `nvidia-smi` work.
- If you do not have an NVIDIA host, keep the CPU-only monitoring path.

### `labml service` fails or never starts

**Symptoms**
- `systemctl --user` fails, or the service is enabled but never comes up.

**Likely cause**
- The host does not support a user-level systemd service, or the user manager is
  not running.

**Recovery**
- Run `labml monitor` directly first.
- Confirm that `systemctl --user` is available on the machine.
- Recreate the service only after the monitor works interactively.

### A legacy internal analytics import fails

**Symptoms**
- `ModuleNotFoundError: No module named 'labml.internal.analytics'`
- A source-only model-probe or analytics helper no longer imports from the installed package.

**Likely cause**
- The installed public distribution does not include that internal module path.

**Recovery**
- Use the public tracking APIs and the bundled smoke script instead.
- Treat the missing internal path as a package gap, not a local configuration mistake.
- If you are refreshing from source evidence, confirm whether the path is still part of the current checkout before relying on it.

### Git metadata is missing

**Symptoms**
- Run metadata shows `commit=unknown` or git status is empty.

**Likely cause**
- `gitpython` is missing, or the current folder is not a Git repository.

**Recovery**
- Install `gitpython`.
- Run the command from inside a Git checkout.

### `AppAPI` rejects the request or the backend version looks wrong

**Symptoms**
- Network errors, `API client is outdated`, or connection refused.

**Likely cause**
- The backend URL is wrong, the server is down, or the client/server versions do
  not match.

**Recovery**
- Verify the base URL and port.
- Check that the backend is running.
- Compare the installed client version against the server version before digging
  into the payload.

### Rich metrics appear flat or truncated

**Symptoms**
- Histogram or tensor output looks collapsed, truncated, or not updated.

**Likely cause**
- The indicator type was not declared, or the queue/save pattern is too sparse.

**Recovery**
- Call `set_scalar`, `set_histogram`, or the matching indicator helper before
  tracking values.
- Save often enough for the UI to receive updates.

## Read next

- `tracking/scripts/tracking_smoke.py` for a safe local health check.
- `tracking/scripts/hardware_probe.py` for a read-only GPU/monitor probe.
