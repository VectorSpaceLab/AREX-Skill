# Platform ops troubleshooting

## Symptoms and fixes

### `mage start` opens the wrong URL or the browser renders oddly
- Use `127.0.0.1:<port>` instead of `localhost:<port>` if the app is not loading correctly on a non-default port.
- Check that `MAGE_BASE_PATH`, `MAGE_REQUESTS_BASE_PATH`, and `MAGE_ROUTES_BASE_PATH` agree with any reverse proxy prefix.

### Authentication keeps redirecting or no owner user exists
- Current Mage OSS versions enable authentication by default.
- Verify `REQUIRE_USER_AUTHENTICATION` only when working with older OSS deployments.
- Set `DEFAULT_OWNER_EMAIL`, `DEFAULT_OWNER_PASSWORD`, and `DEFAULT_OWNER_USERNAME` if you need deterministic bootstrap credentials.

### Startup fails because of DB migrations
- Run `mage db diagnose` first.
- Then follow the migration history, schema, rollback, and stamp recovery steps in the production docs.

### Local database cannot be reached from Docker
- Use `host.docker.internal` for a database that runs on the host machine.

### Browser freezes on the pipeline edit page
- Clear cached variable outputs for the affected pipeline.
- The safest built-in action is `mage clean-cached-variables <project_path>`.

### Too many open files
- Raise `ULIMIT_NO_FILE` in production.
- For a local shell, increase the shell limit with `ulimit -n` before launching Mage.

### Logs or run output are too noisy
- Lower `SERVER_VERBOSITY`.
- Switch to `SERVER_LOGGING_FORMAT=json` when structured logs are easier to ingest.
- Use `clean-old-logs` to prune retained log files.

### Repo unit tests disagree with the default data directory
- The repo code treats `ENV=test` or `unittest`-style invocation differently.
- If a test expects `.` as the data directory, set `ENV=test` before running the test command.

### AWS S3 credential token errors
- If S3 raises `InvalidToken`, remove an invalid `AWS_SESSION_TOKEN` entry from `io_config.yaml` or the active environment.

### Cloud health checks keep restarting the service
- Increase the startup timeout or initial delay in the deployment health checks.

## Safety note

Do not use `create-spark-cluster` unless the user explicitly wants AWS EMR cluster creation and the project has the required cloud settings.
