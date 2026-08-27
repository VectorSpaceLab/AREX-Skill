# App and UI troubleshooting

Start with the safe checker:

```bash
python sub-skills/app-and-ui/scripts/check_app_runtime.py --runtime-root .
```

Use `--prepare-dirs` only when you want the checker to create the missing application directories. Use `--check-url http://localhost:10101/` only after you have intentionally started a server.

## Startup command exits before Wave starts

**Symptoms**

- `make llmstudio` exits immediately.
- The terminal shows an `nvidia-smi` failure or no Wave server banner.
- Port `10101` is not listening.

**Likely causes**

- The `make llmstudio` target intentionally runs `nvidia-smi && wave ...`; without a working NVIDIA driver/tooling path, the Wave command is skipped.
- Docker was started without the NVIDIA runtime or toolkit.

**Actions**

1. Run `nvidia-smi` directly.
2. If your goal is only to inspect app import/UI startup and not to run training, use the direct Wave command from [runtime setup](runtime-setup.md#direct-wave-command).
3. If your goal is production fine-tuning, fix the NVIDIA driver/container runtime first, then restart `make llmstudio`.
4. Route failures after clicking **Run experiment** to the training sub-skill.

## Browser cannot connect to the GUI

**Symptoms**

- Browser shows connection refused, gateway timeout, or a blank proxied page.
- Local `curl http://localhost:10101/` fails.
- Docker container is running but the host URL does not load.

**Likely causes**

- Wave is not running or is bound inside a container without `-p 10101:10101`.
- Host firewall, SSH tunnel, reverse proxy, or cloud ingress is not forwarding port `10101`.
- Remote browser origin is rejected by Wave.
- Wave app connection/read/write timeouts are too small for a slow remote deployment.

**Actions**

1. Confirm the process is listening: `lsof -i :10101` or `docker ps`.
2. For Docker, confirm the run command includes `-p 10101:10101`.
3. For remote/proxied access, set an explicit allowed origin when possible. For a controlled diagnostic, the documented broad setting is:

   ```bash
   export H2O_WAVE_ALLOWED_ORIGINS="*"
   ```

4. Increase remote Wave timeouts:

   ```bash
   export H2O_WAVE_APP_CONNECT_TIMEOUT=15
   export H2O_WAVE_APP_WRITE_TIMEOUT=15
   export H2O_WAVE_APP_READ_TIMEOUT=15
   export H2O_WAVE_APP_POOL_TIMEOUT=15
   ```

   Use `-1` only when you intentionally want to disable a timeout for diagnosis.
5. If the public URL differs from the internal Wave URL and downloads are affected, align `H2O_WAVE_BASE_URL` with the public route and ensure cloud mode is configured by the deployment.

## Uploads fail or large local files are rejected

**Symptoms**

- Dataset upload fails at the browser/server boundary.
- Wave or a proxy reports a request too large.

**Likely causes**

- `H2O_WAVE_MAX_REQUEST_SIZE` is too small.
- An upstream reverse proxy has a lower request-size limit.
- File extension is not in the app's `ALLOWED_FILE_EXTENSIONS` list.

**Actions**

1. Check the app launch has `H2O_WAVE_MAX_REQUEST_SIZE=25MB` or the deliberate size you need.
2. Check any proxy/load balancer body-size limit.
3. Confirm the file extension is one of the app-allowed CSV, parquet/PQ, or ZIP forms, or set `ALLOWED_FILE_EXTENSIONS` before starting the app.
4. For dataset schema/content problems after upload succeeds, route to the configuration-and-data sub-skill.

## Download buttons open 404s or wrong paths

**Symptoms**

- **Download logs**, **Download predictions**, **Download model**, or **Download adapter** opens a missing URL.
- Files exist under experiment output but not under the served download URL.

**Likely causes**

- `H2O_WAVE_PRIVATE_DIR` does not map `/download` to the same workdir's `output/download` directory.
- The app cannot create symlinks under `output/download`.
- A reverse proxy/base URL mismatch changes the URL path seen by the browser.

**Actions**

1. Resolve the workdir from `H2O_LLM_STUDIO_WORKDIR` or the app startup directory.
2. Ensure `H2O_WAVE_PRIVATE_DIR` uses `/download/@<workdir>/output/download`.
3. Ensure the process user can create directories and symlinks in `output/download`.
4. If behind a public base path, configure the deployment's `H2O_WAVE_BASE_URL` consistently.
5. If the requested artifact itself was not produced, route to training or export guidance.

## App starts slowly or default datasets do not appear

**Symptoms**

- First browser session shows a long “Creating default datasets” dialog.
- Logs mention default dataset download failure.
- Default OASST/DPO/classification/regression datasets are absent, but the app remains usable.

**Likely causes**

- First client initialization attempted to fetch public datasets because `H2O_LLM_STUDIO_DEMO_DATASETS` was not set.
- Network access, dataset cache, or package dependencies are unavailable.

**Actions**

1. Treat this as nonfatal if the app continues to render.
2. Import your own dataset through the UI.
3. For offline or containerized deployments, provide the demo parquet directory through `H2O_LLM_STUDIO_DEMO_DATASETS` before starting the app.
4. If dataset import or schema validation fails later, route to the configuration-and-data sub-skill.

## Keyring warning or credentials are not persisted

**Symptoms**

- Startup logs say keyring failed, timed out, or was disabled.
- Settings page does not offer Keyring.
- Credentials disappear after restart.
- Save settings shows a credential handler error dialog.

**Likely causes**

- The OS keyring backend is unavailable, locked, or slow to respond.
- The selected credential saver is “Do not save credentials permanently”.
- The app cannot write `<workdir>/data/dbs`.
- Wave authentication subject changed, causing a different per-user settings filename.

**Actions**

1. Use the Settings page to select an available credential handler.
2. Prefer Keyring when the host supports it, or no permanent storage when re-entry is acceptable.
3. Use `.env File` only on a machine whose filesystem access is restricted to the user/operator.
4. Check that `<workdir>/data/dbs` is writable by the app process.
5. Check whether the browser/deployment login identity changed between sessions.
6. If an old `.settings` migration warning appears, back up the database directory if needed, remove the old settings file, and re-enter credentials through the Settings page.

## Settings changes do not take effect

**Symptoms**

- A setting changes for the current page but is lost after restart.
- Saved connector defaults do not show during dataset import.

**Likely causes**

- The user did not click **Save settings persistently**.
- Settings were saved under a different Wave user id.
- The settings YAML file is not writable or contains stale values.

**Actions**

1. Click **Save settings persistently** after changing Settings page values.
2. Click **Load settings** to re-read persisted settings into the current session.
3. Confirm the app process can write the database directory.
4. Confirm the same login/auth subject is used across sessions.

## Runtime root assets are missing

**Symptoms**

- `import llm_studio.app` succeeds, but first browser request fails.
- Logs mention missing icons, `llm_studio/python_configs`, `prompts`, `model_cards`, or `pyproject.toml`.

**Likely causes**

- The app was launched from an arbitrary directory instead of an H2O LLM Studio runtime root.
- A packaging or container build omitted required runtime assets.

**Actions**

1. Start Wave from the runtime root containing `llm_studio/`, `pyproject.toml`, `prompts/`, and `model_cards/`.
2. Rebuild the container/package including the runtime assets.
3. Run the checker with `--runtime-root <runtime-root>` to report missing assets before starting Wave.

## Port 10101 is already in use

**Symptoms**

- Wave fails to bind the default port.
- Browser opens an old/stale app instance.

**Actions**

1. Identify the existing listener:

   ```bash
   lsof -i :10101
   ```

2. Stop the old service with `Ctrl-C`, `make stop-llmstudio`, or the relevant container/process manager.
3. Restart the intended app instance.

## Docker mount, permissions, or GPU runtime problems

**Symptoms**

- Container starts but cannot write data/output.
- Container exits at `nvidia-smi`.
- Datasets or experiments disappear after container restart.

**Likely causes**

- Host mount directory is not writable by the container user.
- NVIDIA Container Toolkit/runtime is missing.
- The `/mount` volume was not supplied, so state was not persisted.

**Actions**

1. Create and permission the mount before running Docker:

   ```bash
   mkdir -p "$(pwd)/llmstudio_mnt"
   chmod 777 "$(pwd)/llmstudio_mnt"
   ```

2. Include `--runtime=nvidia`, `--shm-size=64g`, `-p 10101:10101`, and `-v "$(pwd)/llmstudio_mnt:/mount"`.
3. Use `docker ps` and container logs to confirm the app reached the Wave command after `nvidia-smi`.
4. Keep `/mount` stable across restarts; it is the app workdir in the container.

## App error page appears

**Symptoms**

- UI shows “Oops! Something went wrong”.
- There are **Restart** and **Report** buttons.

**Actions**

1. Click **Restart** to return to the home route when the error was transient.
2. Inspect the server terminal logs for the full Python stack trace.
3. Use this routing:
   - Missing runtime assets or Wave/server issues: stay in this sub-skill.
   - Dataset import/schema/config errors: configuration-and-data.
   - Training launch/runtime errors: training-and-experiments.
   - Export, model download, or publish errors: export-and-prompt.
4. Do not paste secrets from settings or environment variables into issue reports. The app report card attempts to redact keys and tokens, but terminal logs and external commands may not.

## Optional UI test failures

**Symptoms**

- Browser tests cannot log in.
- Playwright cannot find selectors or the app URL.
- UI tests hang while waiting for experiment completion.

**Likely causes**

- `PYTEST_BASE_URL` does not match the actual Wave URL.
- `LOCAL_LOGIN=True` was omitted for local no-auth testing.
- Remote tests need valid Okta/Keycloak credentials.
- The test's tiny experiment moved into training and is waiting for backend/model/cache resources.

**Actions**

1. For local UI tests, start the app separately, then set:

   ```bash
   export LOCAL_LOGIN=True
   export PYTEST_BASE_URL=localhost:10101
   ```

2. Verify the home page manually before running the browser suite.
3. Treat browser tests as optional integration checks; they are not a safe default preflight for every app task.
4. If the failure happens after **Run experiment**, route training-specific diagnosis to the training sub-skill.
