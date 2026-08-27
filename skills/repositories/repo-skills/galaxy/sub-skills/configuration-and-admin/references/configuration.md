# Galaxy Configuration Reference

## Core file roles

- `config/galaxy.yml` is the primary Galaxy server configuration file. It is a YAML file with a required `galaxy` section and an optional `gravity` section.
- `gravity` controls process management for `run.sh`, `galaxyctl`, Gunicorn, Celery, and handler service processes.
- `galaxy` controls application settings such as database connection, dataset storage paths, job config pointers, dependency resolvers, auth config pointers, and many server behavior options.
- Sample files are templates. Copy a `*.sample` file to the non-sample filename before editing; do not expect edits to sample files to affect a running server.
- Relative paths in Galaxy config are intended to be interpreted relative to the Galaxy root/config context, not the agent's current directory.

## Commonly edited files

| File | Purpose | Notes |
| --- | --- | --- |
| `galaxy.yml` | Core application and optional Gravity process configuration | Main entry point for most admin changes. |
| `job_conf.yml` or `job_conf.xml` | Job runners, handlers, destinations, dynamic routing, and concurrency controls | Pointed to by `galaxy.job_config_file`; defaults to a local runner if absent. |
| `object_store_conf.yml` or `object_store_conf.xml` | Advanced dataset storage layout and remote/object storage | Use this sub-skill for pointers only; route implementation depth to `data-and-storage`. |
| `dependency_resolvers` in `galaxy.yml` | Ordered resolver list for command-line tool dependencies | Preferred modern configuration. |
| `dependency_resolvers_conf.xml` | Legacy dependency resolver file | Still supported, but deprecated compared with `galaxy.dependency_resolvers`. |
| `auth_conf.xml` and OIDC/SAML config files | External/pluggable authentication configuration | Do not expose credentials or provider secrets. |
| `tool_conf.xml`, `datatypes_conf.xml`, `tool_data_table_conf.xml` | Tool panel, datatype, and data table configuration | Route tool authoring and data-table depth to sibling sub-skills. |

## Minimal local-development shape

A minimal local-development config usually starts with the sample and changes only a small `galaxy` subset:

```yaml
galaxy:
  brand: Local Galaxy
  database_connection: sqlite:///./database/universe.sqlite?isolation_level=IMMEDIATE
  file_path: database/files
  new_file_path: database/tmp
```

For local development, avoid adding production-only complexity unless the user asks: external PostgreSQL, reverse proxy sockets, systemd units, cloud object storage, remote DRM runners, and external identity providers are separate deployment decisions.

## Top-level YAML smoke checks

Use the bundled helper for safe checks:

```bash
python scripts/validate_galaxy_config.py --config config/galaxy.yml
python scripts/validate_galaxy_config.py --config config/galaxy.yml --sample config/galaxy.yml.sample
```

What the helper checks:

- The file exists and parses as YAML.
- The YAML document is a mapping, not a list/string/scalar.
- The config has at least one recognized top-level section: `galaxy` or `gravity`.
- `galaxy` and `gravity`, when present, are mappings or `null` placeholders.
- Suspicious sample-file usage and common misplaced keys are reported as warnings.
- Common referenced paths are summarized so the agent can ask the user whether they are intentional.

What the helper does not check:

- Full Galaxy schema compatibility.
- Database connectivity, migrations, or credentials.
- Whether object-store paths are writable or safe.
- Whether job runners, containers, Conda, Pulsar, or external services are installed.
- Whether a web server or proxy can bind to a port/socket.

## Full schema validation when Galaxy is installed

When a working Galaxy Python environment is available and the user wants full config validation, Galaxy's native config management path validates `galaxy.yml` against the packaged schema. In source-based installs this is exposed through Galaxy's config management code and tests as a `validate galaxy` action. Prefer using the project-supported command in the user's environment if they already have one; otherwise use the bundled helper first and avoid installing broad dependencies just to validate a single edit.

Native evidence shows that Galaxy validation drops unrelated top-level sections and validates the `galaxy` section against the schema; `gravity` is managed separately by Gravity startup behavior. This means a config can pass basic YAML shape checks while still failing Galaxy option validation or runtime startup.

## High-risk settings checklist

Before changing these, ask for environment details, backup expectations, and whether the target is local development or production:

- `database_connection` and related install/database cache settings.
- `file_path`, `new_file_path`, `tool_data_path`, `template_cache_path`, and other filesystem paths.
- `object_store_config_file` and embedded object-store definitions.
- `job_config_file`, dynamic job destinations, handler assignment, and cluster/DRM/Pulsar settings.
- `dependency_resolvers`, Conda auto-install/init options, container resolvers, and tool dependency directories.
- `admin_users`, auth/OIDC/SAML configuration, Vault settings, and trusted proxy headers.
- `gravity.gunicorn.bind`, UNIX sockets, forwarded headers, worker counts, and system process manager settings.

## Safe edit workflow

1. Confirm target: local dev smoke run, staging, or production.
2. Ask for the active `galaxy.yml` path and whether it was copied from a sample.
3. Run the bundled read-only helper against the file.
4. Review only the relevant section (`galaxy`, `gravity`, or a referenced file) and propose the smallest change.
5. For storage/database/job/auth changes, ask for backup/rollback and do not mutate external services.
6. If a full Galaxy environment exists, run native validation or startup only after the YAML smoke check passes.
7. If startup fails after config changes, separate configuration errors from missing external services, dependency resolver issues, and web-client build problems.
