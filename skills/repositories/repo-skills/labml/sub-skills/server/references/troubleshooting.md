# Server Troubleshooting

## Purpose

Read this when the LabML app backend, route inspection, or deployment fails.

## Common issues

### `labml_app.settings` is missing

**Symptoms**
- `ImportError: cannot import name 'settings' from 'labml_app'`
- Server modules fail before MongoDB is reached.

**Likely cause**
- The app source checkout uses a sample settings file, but the runtime settings
  module is missing.

**Recovery**
- Stop before invoking `labml app-server`; this is a hard prerequisite, not a
  MongoDB symptom.
- Copy `settings.sample.py` to `settings.py` and
  `analyses_settings.sample.py` to `analyses_settings.py` in the package, then
  configure the values in `configuration.md`.
- Use the published package only when it includes the required settings supplied
  by your deployment; pip installation alone does not invent site-specific
  settings.
- Run `python scripts/server_smoke.py --require-server-prereqs`; its default
  mode injects test stubs and is not evidence that the real server is ready.

### Static assets are missing

**Symptoms**
- `RuntimeError: Static folder not found` while importing `flask_app.py`.

**Likely cause**
- The frontend was not built into the expected package/static folder.

**Recovery**
- Stop before invoking the server. In `app/ui`, run `npm install && npm run
  build`, or install a distribution that explicitly includes static assets.
- If you only need backend analysis inspection, use `server_smoke.py` without
  treating its stub-only exit status as a real-server pass.

### MongoDB connection fails

**Symptoms**
- Startup fails with a message that MongoDB is not installed or not running.

**Likely cause**
- `init_mongo_db` cannot reach `MONGO_HOST` or localhost on port `27017`.

**Recovery**
- Do not interpret either smoke script or `check_labml_stack.py --check-server`
  as a MongoDB check; both intentionally skip network access.
- Start MongoDB and verify the configured `MONGO_HOST` (or localhost) and port
  `27017` before running `labml app-server`.
- Set `MONGO_HOST` or pass the address explicitly, then retry the real server.

### The client says the API version is outdated

**Symptoms**
- `AppAPI` init or app-client calls fail with a version message.

**Likely cause**
- Client and server API versions do not match.

**Recovery**
- Upgrade the older side or keep client/server packages aligned.

### Run status or analysis data is missing

**Symptoms**
- Routes respond, but run metrics, logs, or statuses are empty.

**Likely cause**
- The run was not created, the distributed parent/child UUID mapping is wrong,
  or analysis models were not registered.

**Recovery**
- Check the run UUID and distributed run mapping.
- Verify `AnalysisManager` has the expected experiment and computer analyses.
- Re-send a small tracking payload from a known client.

### Nginx proxy works locally but not remotely

**Symptoms**
- The app works on localhost but not through the public host/port.

**Likely cause**
- Missing proxy headers, wrong upstream port, firewall rules, or a stale enabled
  site link.

**Recovery**
- Confirm the backend port is listening.
- Check the Nginx site file and restart Nginx.
- Verify firewall and DNS settings separately.

## Read next

- `server/scripts/server_smoke.py` for a safe prerequisite and series-object
  check.
- `server/references/configuration.md` for expected settings and static asset
  rules.
