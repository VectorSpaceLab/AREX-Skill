# Setup and CLI troubleshooting

Use a temporary `DBGPT_HOME` for diagnosis. Record command, exit status, selected config basename/profile, and redacted error text; never record keys or full `profile show` output.

## `uv` or `dbgpt` is missing

**Symptoms:** `uv: command not found`, `dbgpt: command not found`, or a shell invokes a different Python than the installed environment.

1. Check the interpreter and package in the intended environment:

   ```bash
   python --version
   python -m pip show dbgpt-app
   python -m dbgpt.cli.cli_scripts --version
   ```

2. Activate the virtual environment or add its `bin`/`Scripts` directory to `PATH`.
3. Install `uv` through an approved package-management path if it is required; do not pipe a network installer into a shell without review.
4. Use `python -m pip install dbgpt-app` when `uv` is unavailable. `app install` can use `poetry`, `build`, or `setuptools`, but it warns when `uv` is absent and fails when no supported build tool is found.
5. Re-run `dbgpt --help` and the relevant subcommand help after correcting the environment.

Do not “fix” a missing console entry point by adding a source checkout to `PYTHONPATH`; that makes the result non-portable and can mask package/extra problems.

## Invalid or missing profile

**Symptoms:** “Unknown profile”, “Profile NAME not found”, setup wizard failure, or `start web --profile NAME` falls through to setup unexpectedly.

- Registry names are `openai`, `kimi`, `qwen`, `minimax`, `glm`, `custom`, and `default`.
- A profile name is case-normalized by the registry, but the managed file path is `<name>.toml`.
- `profile switch` requires an existing file; it does not create one.
- Run `dbgpt profile list`, then `dbgpt setup --profile NAME` or `dbgpt profile create NAME`.
- Use `dbgpt setup --show` to inspect only the active name/path. If the file is missing, regenerate it; if the file exists, run the bundled read-only checker.

Do not silently substitute `openai` for a requested provider. Ask for a deliberate fallback or report the exact supported registry names.

## Key precedence and credential errors

**Symptoms:** setup succeeds but provider calls return authentication errors, or a run appears to use an old key.

For `setup`/`start web`, distinguish these sources:

1. explicit `--api-key` value;
2. Click's `DBGPT_API_KEY` environment fallback when the option is omitted;
3. the provider-specific environment variable used by the profile wizard/non-interactive setup;
4. a literal key or `${env:...}` value already stored in TOML;
5. provider SDK/environment behavior after DB-GPT starts.

In 0.8.1, non-interactive setup reads a provider environment key and writes it literally. A profile created earlier may therefore contain a stale key even after the shell environment changed. Recreate it deliberately or edit the config to a reviewed interpolation reference. Never print the file to compare keys; compare only the environment variable name and redacted status.

For a profile with separate LLM and embedding credentials, verify both references. Kimi's setup spec uses `MOONSHOT_API_KEY` for the LLM and `OPENAI_API_KEY` for embeddings. A successful LLM call does not prove embeddings are configured.

## Config parse/schema/path failures

**Symptoms:** TOML parse errors, missing required section, “No config file found”, database path errors, or a server that starts and fails during initialization.

1. Check the exact path passed to `--config`; explicit `--config` bypasses profile lookup and is used as-is.
2. Run `python scripts/inspect_config.py CONFIG.toml` and fix syntax, table types, port range, missing `models.llms`/`models.embeddings`, or malformed interpolation markers.
3. Inspect only the config basename and expected sections; do not use `cat`/`profile show` on secret-bearing files in a shared log.
4. Confirm the runtime environment contains all required interpolation variables and that relative paths are valid under `$DBGPT_HOME/workspace` for a pip installation.
5. Check optional extras for the selected provider/vector store/parser. A TOML block can parse while its implementation import is unavailable.
6. Use `dbgpt start web --help` and a package import/version check to separate CLI import errors from application initialization errors.

For SQLite, ensure the parent directory is writable. The migration helper currently supports SQLite only; a MySQL/Postgres config needs the normal app startup path and connector extra, not the integrated migration command.

## Port conflicts and process stop

**Symptoms:** “Address already in use”, a daemon starts but the UI is unreachable, or stop reports “process not found”.

- Read `[service.web].port` from the selected TOML; `start web` has no `--port` option in 0.8.1.
- Check the port with an OS tool such as `ss -ltnp`, `lsof -i :PORT`, or an approved process monitor.
- Stop narrowly: `dbgpt stop webserver --port PORT`. Without `--port`, the process matcher may terminate another matching DB-GPT web process.
- If daemonized, inspect the runtime `webserver_uvicorn.log` and the printed PID. A returned PID only proves `Popen` succeeded.
- If the process is stale or the command line no longer contains the expected fragments, stop it with the approved process manager after verifying the PID. Do not use `kill -9` as the first response.
- Pick another port by editing the TOML, validate it, and start with that same config. Do not invent `start web --port`, which Click rejects.

## Optional CLI integrations

The root command imports model, app/web, knowledge, trace, serve, dbgpts, client, and network integrations in separate guarded blocks. If an optional import fails:

- the core CLI can still render help;
- the corresponding command may be absent;
- a warning identifies the failed integration, but the root exit may remain successful.

Check `python -m pip show`/the package extra for the missing component, then rerun only the needed command's help. Do not install every optional backend just to make the root command tree look complete. Model command help can be special: dynamic model discovery may make a remote controller request and return a 502 even though the package import is fine. See the next section.

## Dynamic model/remote-request failures

**Symptoms:** `model` help or a model command returns 502/connection refused, `knowledge list/load/delete` fails against `127.0.0.1:5670`, or `repo/app list-remote` attempts a network operation.

- The knowledge CLI is an HTTP client. Confirm the target DB-GPT API is running, its address is correct, and `API_ADDRESS`/`--address` is intentional. It cannot list or load data offline.
- `model` operations may query a controller while constructing help or discovering models. Treat a 502 as “controller unreachable/remote discovery failed”, not as evidence that the model command is missing. Use the static root/start/config help that does not trigger remote discovery, then route controller/model recovery to `models-and-serving`.
- `repo add/update`, `app list-remote/install/reinstall`, and some flow operations can contact remote repositories or build packages. Use a reviewed endpoint, an isolated environment, and explicit approval for network/filesystem effects.
- Do not retry a remote request indefinitely or report success after a partial response. Capture status code/target class without recording authorization headers or query secrets.

## Knowledge CLI failures

**Symptoms:** document upload fails, a space is missing, or `--skip_wrong_doc` seems ineffective.

- Confirm the local path exists and is readable before invoking `knowledge load`.
- Confirm the server address and that the required server-side RAG/vector extras are installed.
- `load` creates a space, uploads documents, and synchronizes each document through API calls; `--overwrite` may delete and re-upload a same-named document. `--skip_wrong_doc` skips an individual upload failure, but a failed space/API request still fails the command.
- Use `knowledge list --output json` for machine-readable response formatting only after confirming the server. Route chunk/embedding/vector diagnosis to `data-and-rag`.
- `knowledge delete` asks for confirmation when deleting a document or whole space unless `-y`. Treat omission of `--doc_name` as whole-space deletion, not “delete all documents one by one”.

## Migration safety and recovery

**Symptoms:** migration command asks for confirmation, SQLite-only error, revision not found, or a migration changed metadata unexpectedly.

1. Copy/backup the metadata database and record the selected config/revision before writing.
2. Run parent help with a harmless config path to inspect flags. The parent requires `-c/--config`.
3. Prefer `upgrade --sql-output FILE` to generate SQL for review. It does not apply that SQL to the database.
4. `downgrade` defaults to revision `-1` and prompts unless `-y`.
5. `clean` prompts unless `-y`; `--drop_all_tables` additionally requires `--confirm_drop_all_tables` or a second interactive confirmation. Treat this as destructive even if a command is run in a test home.
6. If a downgrade/clean was interrupted, stop using the database, restore the backup or inspect Alembic current revision, and only then retry. Do not immediately repeat a destructive command.
7. The integrated helper currently rejects non-SQLite database parameter classes. Use the owning database/operations workflow for external databases.

A successful `migration list` may create workspace metadata directories because it initializes the app database/config context. Use a disposable home for a first inspection.

## Secret/path leak review

Before publishing output or handing off a diagnosis, search the report/command transcript for:

- `api_key`, provider key names, passwords, `encrypt_key`, bearer tokens;
- full home/workspace paths, temporary checkout paths, or user names;
- URLs containing credentials or private query parameters;
- full trace JSONL lines containing prompts/responses.

Replace secrets with `<redacted>` and private paths with semantic placeholders such as `$DBGPT_HOME` or `CONFIG.toml`. The runtime skill itself must remain usable after the original source checkout is removed.
