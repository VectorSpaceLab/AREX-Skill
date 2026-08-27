# Cross-Cutting Troubleshooting

## Purpose

Read this when an install, import, or startup issue cuts across more than one
LabML package. Package-specific failures live in the owning subskill.

## Common failures

### A package imports, but a submodule does not

**Symptoms**
- `import labml` works, but `labml_helpers`, `labml_remote`, or `labml_app`
  fail later.
- `ModuleNotFoundError` for a package that the root import seemed to expose.

**Likely cause**
- Only part of the stack was installed.

**Recovery**
- Install the distribution that owns the submodule.
- Re-run `python -m pip check` and the root smoke script.

### `labml_app.db` or `labml_app.flask_app` fails to import

**Symptoms**
- `No module named 'labml_app.settings'`
- `RuntimeError: Static folder not found`
- The app server starts only partially in an editable source checkout.

**Likely cause**
- The app backend needs a settings module and built static frontend assets.
- A plain editable install of the source tree is not enough for the full UI.

**Recovery**
- Provide the app settings module expected by the package.
- Make sure the server has compiled static assets or use the published
  `labml-app` wheel that already bundles them.
- If you only need route and data-model inspection, use the server smoke script
  instead of starting the full backend.

### `labml_remote` says no servers were found

**Symptoms**
- `No servers found. Run labml_remote init...`

**Likely cause**
- The project has no `.remote/configs.yaml` file or it contains no servers.

**Recovery**
- Run `labml_remote init` in the project and add at least one server entry.
- Re-check `.remote/exclude.txt` and the server names in the YAML.

### `labml monitor` shows CPU data but no GPU data

**Symptoms**
- The command runs, but GPU indicators are missing.

**Likely cause**
- `py3nvml` is missing or NVIDIA tools are not available.

**Recovery**
- Install `py3nvml`.
- Confirm `torch.cuda.is_available()` and `nvidia-smi` work on the host.
- If the machine has no NVIDIA GPU, keep the CPU-only monitoring path.

### A source test imports `labml.internal.analytics`, but the installed package does not provide it

**Symptoms**
- A repo-native test or old sample raises `ModuleNotFoundError: No module named 'labml.internal.analytics'`.
- Public tracking APIs work, but a legacy internal analytics import fails.

**Likely cause**
- The installed public distribution does not ship that internal module path.

**Recovery**
- Prefer the public tracking APIs and the bundled smoke script.
- Treat the missing internal module as a repo/package gap rather than a user error.
- If you need that exact source path, verify whether the checkout contains a private or version-specific helper before relying on it.

### `labml` exits because the config file is missing

**Symptoms**
- Warnings about missing `.labml.yaml` or unexpected project paths.

**Likely cause**
- The project does not have a LabML config file at the root or the path is not
  what you expect.

**Recovery**
- Create `.labml.yaml` with the project path and desired data/experiment paths.
- Re-run the smoke script or the original command from the project root.

### `labml_app` cannot connect to MongoDB

**Symptoms**
- Startup or request handling fails with connection errors.

**Likely cause**
- MongoDB is not running, not reachable, or pointed at the wrong host/port.

**Recovery**
- Start MongoDB and verify the configured host and port.
- Re-check the app settings and then retry the server smoke script.

### `labml_remote` or the app server needs a higher backend than the current install

**Symptoms**
- GPU-backed checks fail, or a backend-specific command aborts early.

**Likely cause**
- The host lacks the requested hardware/runtime, or the dependency variant does
  not match the available backend.

**Recovery**
- Narrow the workflow to the CPU path when the package supports it.
- Otherwise install the backend-specific wheel or provide the required host
  service before retrying.

## Read next

- `sub-skills/tracking/references/troubleshooting.md` for client and monitoring issues.
- `sub-skills/helpers/references/troubleshooting.md` for helper/training-loop issues.
- `sub-skills/remote/references/troubleshooting.md` for SSH, rsync, and job issues.
- `sub-skills/server/references/troubleshooting.md` for app-backend startup and route
  issues.
