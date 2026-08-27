# Galaxy Configuration Troubleshooting

## Triage sequence

1. Identify the command and phase: `sh run.sh`, `galaxyctl start`, `galaxyctl restart`, a native config validation command, or a manual script.
2. Identify the active config file: explicit `-c`/environment setting, `config/galaxy.yml`, or a copied sample.
3. Run `python scripts/validate_galaxy_config.py --config PATH` before deeper diagnosis.
4. Classify the symptom as YAML shape, Galaxy schema/option, startup/process manager, database/storage, job/dependency resolver, authentication/proxy, or web-client build.
5. Ask for only the relevant redacted config excerpt and first server-side traceback/error block.

## Missing `galaxy.yml` or sample confusion

Symptoms:

- The user edited `galaxy.yml.sample` but startup behavior did not change.
- Startup warns that config is missing or uses defaults.
- The path passed to validation is a sample file.

Response:

- Explain that sample files are templates.
- Help copy or derive `config/galaxy.yml` from the sample before editing.
- Preserve a backup of any existing real config before replacing it.
- Run the bundled helper against the real config, not only the sample.

## YAML and top-level shape errors

Symptoms:

- YAML parser errors with line/column numbers.
- A top-level list or scalar where a mapping is expected.
- `galaxy` options placed at the document root instead of under `galaxy:`.
- `gravity` options placed under `galaxy:` or Galaxy app options placed under `gravity:`.

Response:

- Fix indentation first; Galaxy config is indentation-sensitive YAML.
- Ensure the top-level document is a mapping with `galaxy:` and optional `gravity:`.
- Move common misplaced keys (`database_connection`, `file_path`, `job_config_file`, `object_store_config_file`, `dependency_resolvers`, `admin_users`) under `galaxy:`.
- Move Gunicorn/process options under `gravity:`.
- Re-run the bundled helper before attempting startup.

## Schema and unknown-option errors

Symptoms:

- Native validation reports an option not found in the schema.
- Startup rejects a config option after YAML parsing succeeds.
- A deprecated option no longer behaves as expected.

Response:

- Confirm the Galaxy source/version used by the server; config options can drift across releases.
- Check spelling and section placement before assuming the option was removed.
- Prefer the packaged sample/schema for the installed Galaxy version.
- If a native validation command is available, use it after the bundled helper passes.
- Do not remove unknown options from production config without understanding whether they are local plugin/custom config or deprecated Galaxy config.

## Database and path mistakes

Symptoms:

- SQLite path or database URL errors during startup.
- Permission denied for `database/`, dataset files, temp paths, logs, or Gravity state.
- Relative paths behave differently than expected.

Response:

- Ask whether this is local development or production before changing database/storage settings.
- Redact database credentials from shared snippets.
- Check whether paths are intended to be relative to the Galaxy root/config context.
- Verify parent directories and service-user permissions conceptually before proposing writes.
- Do not delete, move, reinitialize, or migrate database/storage content without explicit backup and approval.

## Object-store path failures

Symptoms:

- Startup fails while loading object-store config.
- Dataset storage paths, cache paths, or cloud credentials are missing.
- A local dev run points to production object-store paths by accident.

Response:

- Identify whether `object_store_config_file` points to an external YAML/XML file or config is embedded.
- Validate the main `galaxy.yml` and then separately parse-check the referenced file if the user provides it.
- Warn that object-store changes can affect dataset placement and access.
- Route detailed layout/cache/quota/migration work to `data-and-storage`.

Synthetic hard case supported by this sub-skill: diagnose a failed startup where `galaxy.yml` parses, but `object_store_config_file` points to a nonexistent or unwritable object-store path. Expected behavior is to validate config shape, identify the risky storage boundary, and route detailed storage correction to `data-and-storage`.

## Dependency resolver failures

Symptoms:

- Tools fail because command-line dependencies cannot be found.
- Conda auto-install/init fails or is disallowed.
- A resolver list exists in both `dependency_resolvers` and a legacy XML file.
- Jobs run locally but fail only on a remote destination/container.

Response:

- Determine whether the failure is resolver config, package availability, job destination environment, container runtime, or tool XML requirements.
- Check the ordered `dependency_resolvers` list and whether `read_only`, `auto_install`, `auto_init`, channels, prefix, and executable are intentional.
- Avoid enabling auto-install or web downloads unless the user explicitly permits it.
- For tool XML requirements and workflow/tool authoring, route to `workflows-and-tools` when present.

## Server-not-starting vs client build confusion

Server-side config symptoms:

- Python traceback during app config load.
- YAML/schema/config option errors.
- Database, storage, handler, resolver, auth, proxy/socket, or process manager errors.

Client build symptoms:

- npm/yarn/node errors.
- Vite/webpack/static asset failures.
- JavaScript dependency or UI compilation errors.

Response:

- If `run.sh` reaches a Python server traceback, stay in this sub-skill.
- If the failure is npm/yarn/static-client build related, route to `web-client-development`.
- If both occur, solve server config first only when it blocks startup before client asset loading.

## External service and hardware boundaries

Do not promise that config edits alone can fix missing services or hardware. Ask for deployment facts when errors mention:

- PostgreSQL/MySQL/MariaDB availability or version.
- Redis, RabbitMQ/AMQP, Celery, Pulsar, Kubernetes, Slurm/DRM, Docker, Singularity/Apptainer.
- Reverse proxies, TLS certs, UNIX socket permissions, SELinux/AppArmor.
- Cloud object-store credentials or network access.
- GPUs, special filesystems, NFS permissions, or cluster scheduler policies.

The safe deliverable is a diagnosis and change plan unless the user explicitly authorizes service-level operations.

## Minimal local development hard case

Synthetic hard case supported by this sub-skill: build a minimal local `galaxy.yml` change plan that changes the brand and local filesystem paths while explicitly skipping production database, proxy, object-store, remote job runner, and external auth setup. Expected behavior is to keep the config small, validate YAML, and recommend `sh run.sh` only after checks pass.
