# DB-GPT 0.8.1 CLI reference

Use the installed command's help as the final authority:

```bash
dbgpt --version
dbgpt --help
dbgpt start web --help
dbgpt setup --help
dbgpt profile --help
```

If the console entry point is not on `PATH`, the equivalent inspection form is:

```bash
python -m dbgpt.cli.cli_scripts --version
python -m dbgpt.cli.cli_scripts --help
```

The inspected package reports version `0.8.1`. Optional command integrations are imported defensively. A missing optional package can remove a command and emit an integration warning; do not infer that an absent command is a syntax error until the package extras are checked.

## Root command tree

The root Click group exposes these commands in the standard installation:

| Command | Purpose | Boundary |
|---|---|---|
| `start` | Start a DB-GPT/web or model service | General web dispatch here; model service flags → `models-and-serving` |
| `stop` | Stop a web/model service by process match | Process control here; model-specific diagnosis → `models-and-serving` |
| `setup` | Create/activate a provider profile | Profile/config lifecycle here |
| `profile` | List/show/create/switch/delete profile files | Profile lifecycle here |
| `db migration` | Initialize, create, apply, inspect, downgrade, or clean migration state | Guarded metadata operations here |
| `knowledge` | Load/list/delete knowledge through a running API | Remote API boundary; RAG details → `data-and-rag` |
| `trace` | Read local JSONL trace files | Local trace analysis here |
| `repo` | List/add/remove/update dbgpts repositories | May touch git/network; review before mutating |
| `app` | Install/uninstall/reinstall/list dbgpts | May build/install/network; review before mutating |
| `new` | Create a template or serve module | Template generation is side-effectful; not a source checkout dependency |
| `run` | Run a dbgpt flow | Flow construction/execution → `agents-and-awel` or client route |
| `tool` | Tool/flow utilities | Flow semantics → `agents-and-awel` |
| `net` | Network utility commands | Inspect target before forwarding/network action |
| `model` | Model-serving management | `models-and-serving` |

The `start` group has `web` and the alias `webserver`, `controller`, `worker`, `apiserver`, and `none`. Calling `dbgpt start` without a subcommand invokes `web` when registered. `start none` only prints that API-only mode is planned and suggests `dbgpt start web`; it does not start an API-only service.

The `stop` group has `webserver`, `controller`, `worker`, `apiserver`, and `all`. The group help text says “Start specific server” in this release; the behavior is stop behavior.

## Setup and web start

### `dbgpt setup`

```text
Usage: dbgpt setup [OPTIONS]

-p, --profile TEXT   Provider profile
-y, --yes            Non-interactive: skip wizard and use defaults/env
--api-key TEXT       API key; Click also reads DBGPT_API_KEY
--show               Show active profile and config path, then exit
```

Interactive setup asks for a provider, key (unless the profile does not need one), provider-specific API base where applicable, and model names. `--yes` calls the non-interactive path and writes the profile without prompting. `--show` only reports the active profile and expected config path; it does not validate the TOML or credentials.

The source help string mentions a narrower/older provider list in places. The installed profile registry is the reliable list: `openai`, `kimi`, `qwen`, `minimax`, `glm`, `custom`, and `default`. `ollama` is supported by manual model configuration, but is not one of the setup profile registry entries in 0.8.1.

### `dbgpt start web` / `dbgpt start webserver`

```text
Usage: dbgpt start web [OPTIONS]

-c, --config TEXT     TOML path; highest priority
-p, --profile TEXT    Managed profile name
-y, --yes             Skip setup wizard
--api-key TEXT        API key; also reads DBGPT_API_KEY
-d, --daemon          Run in background
```

Resolution order is:

1. explicit `--config` (used as-is, even if it is outside the managed profile directory);
2. an existing file for explicit `--profile`;
3. the active profile in the DB-GPT home `config.toml`;
4. non-interactive setup when `--yes` is set;
5. the interactive wizard.

The command prints a banner unless daemonized, then prints profile/config/workspace information and calls the webserver. The start command does **not** expose `--port` in this release. Put the port in `[service.web].port`; use `stop webserver --port PORT` to select a process to stop.

Examples:

```bash
# Explicit and reproducible
DBGPT_HOME="$PWD/.dbgpt-test" dbgpt start web --config "$PWD/config.toml"

# Existing managed profile
dbgpt start web --profile openai

# First-run CI path (review secret-at-rest behavior first)
dbgpt setup --profile default --yes
dbgpt start web --profile default --yes

# Background process
dbgpt start web --profile openai --daemon
dbgpt stop webserver --port 5670
```

`--daemon` launches a child using the current Python executable with the daemon flag removed. It appends output to `webserver_uvicorn.log` under the DB-GPT log directory and prints a PID. It does not make an unreachable provider or malformed configuration healthy.

### `dbgpt stop`

```text
dbgpt stop webserver
  --port INTEGER  The port to stop

dbgpt stop all
```

The web stop operation uses process command-line fragments and, when requested, a listening-port check. It terminates matching processes; it does not first perform a graceful HTTP health check. Use a specific port and independently inspect PIDs when multiple DB-GPT instances exist. `stop all` also invokes registered model-service stop functions when the model CLI imported successfully.

## Profile commands

```bash
dbgpt profile list
dbgpt profile show NAME
dbgpt profile create NAME
dbgpt profile switch NAME
dbgpt profile delete NAME [--yes]
```

- `list` enumerates TOML files and marks the active name with `*`.
- `show` prints the file verbatim; treat it as secret-bearing output.
- `create` runs the interactive setup wizard and can overwrite/reconfigure a profile.
- `switch` only succeeds when `NAME.toml` exists and updates the active pointer.
- `delete` asks for confirmation unless `-y/--yes`; deleting the active profile clears its active name by writing an empty profile value.

## Knowledge commands

The group accepts `--address TEXT`, defaulting to `http://127.0.0.1:5670` or `API_ADDRESS` when the default is used. It calls the HTTP API; it is not an offline document tool.

```bash
dbgpt knowledge load [OPTIONS]
  --space_name TEXT          default: default
  --vector_store_type TEXT   default: Chroma
  --local_doc_path TEXT      default: DB-GPT dataset path
  --skip_wrong_doc
  --overwrite
  --max_workers INTEGER
  --pre_separator TEXT
  --separator TEXT
  --chunk_size INTEGER
  --chunk_overlap INTEGER

dbgpt knowledge list [OPTIONS]
  --space_name TEXT          list all spaces when omitted
  --doc_id INTEGER            list chunks for a document
  --page INTEGER              default: 1
  --page_size INTEGER         default: 20
  --show_content
  --output text|html|csv|latex|json

dbgpt knowledge delete [OPTIONS]
  --space_name TEXT           default: default
  --doc_name TEXT              omit to delete the whole space
  -y                          skip confirmation
```

`load` creates/uses a space and uploads local files to the API, then synchronizes documents. `--overwrite` can delete/re-upload a same-named document. `--skip_wrong_doc` converts an upload error into a warning for that file; it does not make a failed server request successful. Route parsing/chunking/vector behavior to `data-and-rag`.

## Trace commands

Trace commands read local JSONL files; they do not call the DB-GPT web API by default.

```bash
dbgpt trace list [FILES...] [--trace_id ID] [--span_id ID] [--span_type TYPE]
  [--parent_span_id ID] [--search TEXT] [-l LIMIT] [--start_time TIME]
  [--end_time TIME] [--desc] [--output text|html|csv|latex|json]
  [-j JSON_PATH] [-sj SEARCH_JSON_PATH] [-jm MATCH] [--value]

dbgpt trace tree --trace_id ID [FILES...]
dbgpt trace chat [FILES...] [--trace_id ID] [--tree] [--hide_conv]
  [--hide_run_params] [--output text|html|csv|latex|json]
```

If no files are supplied, the implementation searches the configured log directory for `dbgpt*.jsonl`. JSON-path extraction requires the optional `python-jsonpath` package and reports an actionable install message if absent. Trace data can contain prompts, outputs, and keys from metadata; redact before sharing.

## Repository/app operations

These commands can have network, git, package-build, or filesystem effects:

```bash
dbgpt repo list
dbgpt repo add --url URL [--repo NAME] [--branch BRANCH]
dbgpt repo remove REPO
dbgpt repo update [--repo NAME]

dbgpt app list
dbgpt app list-remote [--repo NAME] [--update]
dbgpt app install [--repo NAME] [--update] [NAMES...]
dbgpt app uninstall [NAMES...]
dbgpt app reinstall [--repo NAME] [--update] [NAMES...]
dbgpt new app --name NAME [--label LABEL] [--description TEXT]
  [--type TYPE] [--definition_type json|python] [--directory DIR]
```

`app install` checks for a build tool and warns when `uv` is unavailable; it can still use `poetry`, `build`, or `setuptools` when detected. No build tool causes an error. `repo add` requires `--url`; use a reviewed, trusted repository and an isolated environment. Do not treat a remote list or successful package build as source security validation.

## Migration commands

The migration group requires a config option at its parent:

```bash
dbgpt db migration -c CONFIG init [--alembic_ini_path PATH]
  [--script_location PATH] [-m MESSAGE]
dbgpt db migration -c CONFIG migrate [--alembic_ini_path PATH]
  [--script_location PATH] [-m MESSAGE]
dbgpt db migration -c CONFIG upgrade [--alembic_ini_path PATH]
  [--script_location PATH] [--sql-output FILE]
dbgpt db migration -c CONFIG downgrade [--alembic_ini_path PATH]
  [--script_location PATH] [-r REVISION] [-y]
dbgpt db migration -c CONFIG clean [--alembic_ini_path PATH]
  [--script_location PATH] [--drop_all_tables] [-y]
  [--confirm_drop_all_tables]
dbgpt db migration -c CONFIG list [--alembic_ini_path PATH]
  [--script_location PATH]
dbgpt db migration -c CONFIG show REVISION [--alembic_ini_path PATH]
  [--script_location PATH]
```

Defaults for the Alembic options are the packaged `pilot/meta_data/alembic.ini` and `pilot/meta_data/alembic` locations relative to the DB-GPT workspace. Migration currently accepts SQLite configuration only in the app integration. The command initializes/ensures the metadata database and workspace before building the Alembic config, so even read-like commands may create local runtime directories.

`upgrade --sql-output FILE` generates SQL rather than applying it. `downgrade` prompts unless `-y`; default revision is `-1`. `clean` prompts unless `-y`, and `--drop_all_tables` has a second confirmation requirement. Back up the metadata database and review the selected config/revision before any destructive operation.
