# CLI and runtime reference

## Commands exposed by the current CLI

| Command | What it does | Notes |
| --- | --- | --- |
| `mage init <project_path>` | Create a Mage project | Uses the current working directory as the parent path when a relative project name is given. |
| `mage start [project_path]` | Start the Mage server and UI | Default host `localhost`, default port `6789`. |
| `mage run <project_path> <pipeline_uuid>` | Run a pipeline or block | Supports `--block-uuid`, `--test`, `--runtime-vars`, `--skip-sensors`, and executor/runtime options. |
| `mage clean-cached-variables <project_path>` | Remove cached variable output | Useful when a pipeline editor page freezes because variables are too large. |
| `mage clean-old-logs <project_path>` | Remove old run logs | Controlled by the repo logging retention settings. |
| `mage create-spark-cluster <project_path>` | Create an EMR cluster | AWS/EMR side effects; only use when explicitly requested. |

## Key runtime settings

| Setting | What it controls |
| --- | --- |
| `MAGE_BASE_PATH`, `MAGE_REQUESTS_BASE_PATH`, `MAGE_ROUTES_BASE_PATH` | Prefix Mage URLs behind a proxy or subpath. |
| `REQUIRE_USER_AUTHENTICATION` | Turn on authentication in older OSS deployments; current OSS versions enable auth by default. |
| `DEFAULT_OWNER_EMAIL`, `DEFAULT_OWNER_PASSWORD`, `DEFAULT_OWNER_USERNAME` | Seed or customize the first owner account. |
| `SERVER_VERBOSITY` | Server log level. |
| `SERVER_LOGGING_FORMAT` | `plaintext` or `json` server logs. |
| `SERVER_LOGGING_TEMPLATE` | Custom plaintext log format. |
| `MAGE_DATABASE_CONNECTION_URL` | Non-sqlite orchestration database URL. |
| `DISABLE_NOTEBOOK_EDIT_ACCESS` | Make the notebook read-only or partially read-only. |
| `ULIMIT_NO_FILE` | Raise the open-file limit in production or containers. |
| `LOGS_DIR_PATH` | Override the logs directory location. |
| `ENV` | Alters repo/test/runtime behavior; `ENV=test` is important for repo unit tests. |

## Package/runtime facts

- `mage_ai.run()` executes a pipeline from Python and appends the project parent directory to `sys.path`.
- `get_data_dir()` defaults to `~/.mage_data` unless the environment is treated as test.
- `get_variables_dir()` resolves through `MAGE_DATA_DIR`, `metadata.yaml`, or the default data directory.
- `mage start` and `mage run` both set the repo path before DB and server setup.

## Safe checks

- `../../../scripts/smoke_cli.py` confirms importability and prints CLI help.
- `../../../scripts/check_project_layout.py` prints a non-mutating summary of a project path.
