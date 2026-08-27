---
name: setup-and-cli
description: "Operate DB-GPT 0.8.1 installation, profiles, TOML configuration,
  the dbgpt command tree, workspace services, knowledge and trace utilities,
  dbgpts repositories/apps, and guarded database migrations without leaking
  credentials or assuming remote services."
metadata:
  disco-role: operating
license: Apache 2.0
disable-model-invocation: true
---

# Setup and CLI

Use this route when the task is about installing the public `dbgpt-app` package, creating or selecting a provider profile, editing a DB-GPT TOML file, discovering CLI commands, starting/stopping the web process, inspecting local traces, managing knowledge through the CLI, managing dbgpts repositories/apps, or running a database migration. This route is for orchestration and safe dispatch, not model-backend tuning, RAG internals, or HTTP CRUD.

## Route first

- **Provider/model flags, controller/worker/apiserver, local-model backends, CUDA, Ollama, vLLM, llama.cpp, or model deployment** → `models-and-serving`.
- **Document formats, chunking, embeddings, vector/graph stores, knowledge-space internals, or connector parameters** → `data-and-rag`.
- **HTTP endpoint CRUD, Python client calls, file/report APIs, or sandbox execution** → `apis-client-and-sandbox`.
- **Agent, skill, tool, AWEL, flow graph, or team construction** → `agents-and-awel`.
- Keep this route for selecting a config and invoking a command. Do not invent model-specific options on `start web`.

Read the smallest reference needed:

- [CLI reference](references/cli-reference.md) for the live Click command tree and exact flags.
- [Installation and profiles](references/installation-and-profiles.md) for package installation, profile lifecycle, home/workspace layout, and credential handling.
- [Configuration](references/configuration.md) for TOML shape, interpolation, path semantics, and read-only validation.
- [Troubleshooting](references/troubleshooting.md) for failures, remote-request boundaries, process recovery, and destructive-operation safety.
- [`scripts/inspect_config.py`](scripts/inspect_config.py) for a self-contained, read-only TOML/profile sanity check. It never imports DB-GPT, resolves secrets, writes files, or calls a network service.

## Standard workflow

1. **Classify the install.** Prefer a clean Python 3.10+ environment and the published `dbgpt-app` package. Use `uv` when available; `pip` is an acceptable fallback. Treat repository installer scripts as review-only automation, not as opaque commands to copy into a runtime skill.
2. **Choose the runtime home.** Set `DBGPT_HOME` before the first DB-GPT CLI import if an isolated home is needed. The default is `~/.dbgpt`; a pip installation uses its workspace below this home for relative database, vector, log, and data paths.
3. **Choose a configuration strategy.** Use an existing explicit `--config` TOML, an existing named `--profile`, the active profile, or setup/wizard in that order. For CI, pass `--yes`; never put a real key in shell history, examples, logs, or an assistant response.
4. **Validate before starting.** Run `python scripts/inspect_config.py CONFIG.toml` (from this skill directory or by using its absolute installed-skill path) and then `python -m dbgpt.cli.cli_scripts --version` plus the relevant `--help`. The validator is structural only; it does not prove provider credentials, model availability, or server startup.
5. **Start the least-surprising command.** `dbgpt start` defaults to the web command. Use `dbgpt start web --config CONFIG.toml` for deterministic selection, or `--profile NAME` for a managed profile. `--daemon` starts a child process and writes the web log under `DBGPT_LOG_DIR`/the workspace log directory.
6. **Check local state.** Confirm the process and configured port from an independent process/socket check and inspect the DB-GPT log. A successful CLI return is not proof that an LLM, embedding provider, vector store, or remote controller is reachable.
7. **Stop narrowly.** Prefer `dbgpt stop webserver --port PORT` when more than one process may exist; use `dbgpt stop webserver` only when the process match is unambiguous. Use `dbgpt stop all` only when terminating all registered model/web services is intended.
8. **Use remote-facing utilities deliberately.** `knowledge load/list/delete` calls a running API server; `repo`/`app` operations can build, install, update, or fetch remote repositories; migration commands can alter metadata. Preview help and confirm target state before execution.

## Safety rules

- Redact every API key, password, `encrypt_key`, authorization header, and literal secret. `profile show` prints the TOML verbatim, so do not capture or paste its output into logs.
- `--api-key` is a Click option backed by `DBGPT_API_KEY`; for setup, an explicit value wins, then the option's environment value, then the profile provider environment variable in the wizard/non-interactive helper. In 0.8.1, non-interactive setup resolves a provider environment key and writes that resolved value into the profile file. Prefer runtime interpolation in a reviewed TOML when avoiding a secret at rest; validate with the bundled checker, not by printing the file.
- Never run an installer fetched from the network without downloading and reviewing it first. The upstream installer can clone/update a checkout, install dependencies, write config, and handle credentials; this skill records the decision points but does not bundle or execute it.
- A config file is not a credential or backend health check. A parseable file can still fail because an environment variable is absent, an optional provider package is not installed, a model is unavailable, a local path is wrong, or an external service is down.
- `db migration downgrade` requires confirmation unless `-y` is supplied. `db migration clean` requires confirmation unless `-y` is supplied; `--drop_all_tables` additionally requires `--confirm_drop_all_tables` or an interactive confirmation. Prefer `upgrade --sql-output FILE` to review SQL before applying it.
- Do not use a guessed `--port` on `start web`: the 0.8.1 Click command exposes no start-port option. Set `[service.web].port` in TOML (or use a configuration that already has the desired port). `stop webserver` does expose `--port`.

## Completion criteria

A setup/CLI task is complete only when the selected command's help matches the installed 0.8.1 command, the config path and profile are explicit, secrets are redacted, and validation distinguishes local parsing from provider/service health. Report skipped checks when they would require credentials, a running DB-GPT server, a remote repository, a remote controller, a GPU stack, or a destructive migration.
