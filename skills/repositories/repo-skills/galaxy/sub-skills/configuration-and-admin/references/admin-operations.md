# Galaxy Admin Operations Reference

## Startup model

Galaxy's quickstart path is `sh run.sh`, which prepares/uses the Python environment and starts Galaxy so the browser can reach the configured address, normally `http://localhost:8080/` for a local all-in-one instance.

Modern Galaxy startup uses Gravity for process management. `galaxy.yml` may include both:

- `gravity`: process manager and service settings such as Gunicorn, Celery, handlers, state/log directories, sockets, workers, and environment variables.
- `galaxy`: application settings loaded by the Galaxy app itself.

Default local startup is an all-in-one Gunicorn strategy where web workers also handle jobs. Production deployments often split web workers from job handlers and use an external database, proxy, logging, service manager, and backup plan.

## `run.sh`, Gravity, and `galaxyctl`

Use these concepts when advising a future agent:

- `run.sh` is appropriate for local development and quickstart checks.
- `run.sh --daemon` starts in the background when Gravity is configured for it.
- `galaxyctl start`, `stop`, `restart`, `graceful`, `follow`, and `update` manage Gravity-controlled services in established deployments.
- After editing `gravity` settings, Gravity-generated supervisor/service config may need an update or restart before changes take effect.
- A `gravity.gunicorn.bind` value controls the address, port, UNIX socket, or file descriptor used by Gunicorn.
- Binding to a UNIX socket usually implies a reverse proxy; if the user expected direct browser access, check whether an additional TCP bind or proxy config is required.

Do not treat client asset build failures as Galaxy server config failures. If the symptom is npm/yarn/node/Vite/static asset compilation, route to `web-client-development`.

## Job configuration at a high level

Galaxy runs jobs locally by default if no job config is present. Admins use `job_conf.yml` or `job_conf.xml` to define:

- Runner plugins, such as local, cluster/DRM, Pulsar, containerized, or dynamic runners.
- Handlers that setup, start, monitor, and clean up jobs.
- Destinations that map jobs to runner parameters.
- Tool-to-destination mappings and dynamic destination rules.
- Resubmission behavior, job resource parameters, and environment modifications.

The active job config path is controlled by `galaxy.job_config_file`. If the file is absent, Galaxy falls back to local execution with a small local concurrency default. Do not invent cluster-specific runner parameters; ask which scheduler/DRM/container backend the deployment uses.

Scaling guidance:

- More job runner worker threads does not make the web server more responsive.
- Production responsiveness usually comes from multiple web workers and separate job handlers sharing the same database.
- Handler assignment may use database locking strategies; database support/version matters.
- If the user is debugging job routing, inspect `job_config_file`, handler names, destination ids, dynamic routing files, and server process names together.

## Object-store configuration at a high level

Galaxy can store datasets in local filesystem paths by default, or in more advanced object stores configured through `object_store_config_file` or embedded object-store settings. Treat object-store edits as high risk because wrong paths or credentials can cause startup errors, missing dataset access, or data placement surprises.

For this sub-skill:

- Identify whether the config points to a separate object-store file or embeds the object-store configuration.
- Smoke-check YAML/XML existence and obvious path references when the user provides them.
- Warn before changing production dataset storage paths or remote object-store credentials.
- Route detailed object-store layout, migration, quota, cache, and data-table interactions to `data-and-storage`.

## Dependency resolvers

Galaxy tools declare command-line requirements in tool XML. Dependency resolvers decide how to find or prepare those command-line tools at job runtime.

Modern configuration uses a `galaxy.dependency_resolvers` list in `galaxy.yml`. The default resolver order is conceptually:

1. Tool Shed package dependencies.
2. Galaxy packages with exact versions.
3. Conda with exact versions.
4. Galaxy packages without exact versions.
5. Conda without exact versions.

A legacy `dependency_resolvers_conf.xml` file is still supported but deprecated for new config. If both a legacy file and embedded resolver list are present, clarify which one Galaxy is actually using before editing.

Common admin decisions:

- Whether Conda can auto-install dependencies or must be read-only.
- Which Conda prefix/executable/channels are allowed.
- Whether containers or mulled environments are enabled.
- Whether manually installed packages live under `tool_dependency_dir`.
- Whether a failure is resolver configuration, missing packages, job destination environment, container runtime, or tool XML requirements.

## Authentication and admin pointers

`auth_conf.xml` configures pluggable authentication; OIDC/SAML and Vault-style settings may introduce additional files and secrets. Keep credentials out of logs and summaries. For simple local development, Galaxy's default internal user management is usually enough.

`admin_users` controls which user emails have admin privileges after those users exist. Adding an email there is not the same as creating an account or authenticating a user. Route API-based user/admin automation to `api-automation`.

## Local-development change plan template

For a minimal local setup request, keep the plan narrow:

1. Copy `galaxy.yml.sample` to `galaxy.yml` if no active config exists.
2. Set only display and local path options required for the task.
3. Keep SQLite/local filesystem defaults unless the user explicitly needs production parity.
4. Avoid external object stores, production proxies, remote job runners, and external auth.
5. Run the bundled config helper.
6. Start with `sh run.sh` and read startup output for the first server-side error.

## Production-change plan template

For production or shared deployments, ask for explicit context before proposing edits:

- Database backend and backup/rollback plan.
- Dataset/object-store layout and ownership/permissions.
- Proxy/socket/TLS termination topology.
- Process manager and service user.
- Job execution backend and handler layout.
- Dependency resolver policy and whether auto-install is allowed.
- Authentication provider and secret management.
- Maintenance window and restart expectations.

The safe default is to produce a reviewed change plan first, not to mutate files or services.
