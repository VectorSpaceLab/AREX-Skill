# Installation, home layout, and profiles

## Choose an installation path

DB-GPT 0.8.1 is published as `dbgpt-app` and requires Python 3.10 or newer. The normal public-package path is an isolated virtual environment followed by one of:

```bash
# Recommended package installer
uv venv .venv
. .venv/bin/activate
uv pip install dbgpt-app

# pip fallback inside an already-selected environment
python -m pip install dbgpt-app
```

Use the provider/storage/RAG extras appropriate to the task, for example:

```bash
python -m pip install "dbgpt-app[proxy_openai,storage_chromadb,rag]"
```

Do not assume every provider, parser, database driver, vector store, or local-model backend is part of the base installation. Add the matching extra and rerun an import/help check before starting the service. GPU/local-model stacks are a separate capability; a CPU package import does not prove CUDA support.

After installation:

```bash
dbgpt --version
dbgpt --help
dbgpt setup --show
```

If `dbgpt` is not found, activate the environment, check `python -m pip show dbgpt-app`, and use `python -m dbgpt.cli.cli_scripts ...` as an equivalent diagnostic. The latter confirms the package import but does not fix an incorrectly installed console script.

### About the upstream installer

The project also documents a shell installer. It is not bundled here because it can download code, clone/update a workspace, install dependencies, write configuration, and process credential-bearing environment variables. If that path is required, download it to a local file, inspect it, pin/review the revision, and run it only in a disposable or explicitly approved environment. Prefer the public package flow when a reviewable, minimal install is required.

## Home, workspace, and files

`DBGPT_HOME` selects the DB-GPT user home. Without it, the default is `~/.dbgpt`.

```text
$DBGPT_HOME/
├── config.toml              # active-profile pointer: [default].profile
├── configs/
│   └── NAME.toml            # one managed profile per file
└── workspace/                # pip-install runtime root
    ├── pilot/meta_data/      # metadata database and migration files
    ├── pilot/data/           # vector/data storage by default
    ├── pilot/datasets/       # default knowledge-load location
    ├── logs/                 # runtime logs and local trace JSONL
    └── ...
```

The pip-installed runtime detects that it is not a source checkout and uses `$DBGPT_HOME/workspace` as its root. Relative values such as `pilot/meta_data/dbgpt.db`, `pilot/data`, and `pilot/datasets` therefore resolve under that workspace rather than under the directory containing an arbitrary config file. Use absolute paths only when intentionally binding storage to a known location, and ensure the service user can read/write them.

Set `DBGPT_HOME` before invoking a command or importing DB-GPT modules when isolation matters:

```bash
DBGPT_HOME="$PWD/.dbgpt" dbgpt profile list
DBGPT_HOME="$PWD/.dbgpt" dbgpt setup --profile default --yes
```

The profile writer creates the home/configs directories with owner-only permissions where the platform supports POSIX modes. Profile TOML files are written with mode `0600` and the profile directory with mode `0700` on POSIX. The active pointer contains a profile name, but still keep the whole home directory private.

`DBGPT_LOG_DIR` overrides the log directory used by the CLI/server. When unset, logs are under the selected runtime root. `DBGPT_LANG` is used by generated profiles for the UI language. Configuration may also set `[system].language` and `[system].log_level`.

## Profile registry and provider mapping

The setup registry in 0.8.1 contains these names:

| Name | LLM provider/model default | Embedding provider/model default | Key environment |
|---|---|---|---|
| `openai` | `proxy/openai`, `gpt-4o` | `proxy/openai`, `text-embedding-3-small` | `OPENAI_API_KEY` |
| `kimi` | `proxy/moonshot`, `kimi-k2` | `proxy/openai`, `text-embedding-3-small` | LLM: `MOONSHOT_API_KEY`; embeddings: `OPENAI_API_KEY` |
| `qwen` | `proxy/tongyi`, `qwen-plus` | `proxy/tongyi`, `text-embedding-v3` | `DASHSCOPE_API_KEY` |
| `minimax` | `proxy/openai`, `abab6.5s-chat` | `proxy/openai`, `embo-01` | `MINIMAX_API_KEY` |
| `glm` | `proxy/zhipu`, `glm-4-plus` | `proxy/zhipu`, `embedding-3` | `ZHIPUAI_API_KEY` |
| `custom` | `proxy/openai`, `gpt-4o` | `proxy/openai`, `text-embedding-3-small` | `OPENAI_API_KEY` |
| `default` | env-overridable `proxy/openai`, `gpt-4o` | env-overridable OpenAI embedding | `OPENAI_API_KEY` |

The `default` entry is a “skip for now” profile: it does not require a key during setup and emits environment interpolation for model/provider/base/model names. `ollama` is not a setup registry entry even though a hand-authored model config can use `proxy/ollama`; route that configuration and backend setup to `models-and-serving`.

The profile help text in some builds lists an older provider subset. Use the installed registry and generated file as the source of truth, not an unverified copy of prose.

## Setup and credential precedence

### Interactive

```bash
dbgpt setup
# or skip provider selection and use a named registry profile
dbgpt setup --profile custom
```

Interactive setup behavior:

1. `--profile` preselects the provider; an invalid name reports the valid registry names.
2. For a key-requiring provider, `--api-key` wins; otherwise the provider's key environment variable is used; otherwise a hidden prompt is offered.
3. `openai` and `custom` ask for an API base URL.
4. Non-default profiles ask for LLM and embedding model names.
5. The resulting profile is activated and written to `configs/NAME.toml`.

### Non-interactive

```bash
# No prompts; profile defaults are used
DBGPT_HOME="$PWD/.dbgpt" dbgpt setup --profile default --yes

# Explicit key (avoid shell history and process listings where possible)
dbgpt setup --profile openai --api-key "$OPENAI_API_KEY" --yes
```

The Click option `--api-key` reads `DBGPT_API_KEY` when the option is omitted. The non-interactive helper then resolves a missing explicit key from the selected profile's provider environment variable if that profile needs a key. Consequently, `setup --profile openai --yes` with `OPENAI_API_KEY` set writes the resolved key literally into the TOML (the file is permission-restricted, but the secret is still at rest). If the objective is to keep the key out of the file, use a reviewed config containing `${env:OPENAI_API_KEY}`/`${env:OPENAI_API_KEY:-...}` and validate it without printing it, or use the `default` profile's interpolation pattern and then make deliberate non-secret model/provider edits.

Never use `profile show` in a CI log. The command prints literal values without redaction. The bundled inspector reports only key status and environment-variable names.

## Managed profile lifecycle

```bash
dbgpt profile list
dbgpt profile show NAME
dbgpt profile create NAME
dbgpt profile switch NAME
dbgpt profile delete NAME          # prompts
dbgpt profile delete NAME --yes   # explicit non-interactive deletion
```

`profile show` expects an existing `configs/NAME.toml`; `switch` refuses a missing file. `delete` removes only that profile file and clears the active pointer if it was active. Re-running `setup --profile NAME` overwrites/reconfigures the profile. Before switching, validate the target file and verify that its provider package and environment variables are available.

## Recommended safe installation check

Run these checks in the selected environment, with `DBGPT_HOME` pointed at a temporary directory when testing setup:

```bash
python -m pip check
DBGPT_HOME="$PWD/.dbgpt-check" dbgpt --version
DBGPT_HOME="$PWD/.dbgpt-check" dbgpt start web --help
DBGPT_HOME="$PWD/.dbgpt-check" dbgpt setup --show
```

The help checks import command integrations but do not prove web startup, model availability, embeddings, vector storage, or a live API key. Keep remote-provider and external-service verification separate and explicit.
