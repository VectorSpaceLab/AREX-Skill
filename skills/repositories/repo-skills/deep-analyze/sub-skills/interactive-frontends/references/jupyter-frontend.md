# Jupyter frontend reference

This surface is a notebook-first DeepAnalyze client built around a local Jupyter Lab workspace and MCP notebook control.

## Prerequisites

- `uv`
- Node.js, for the MCP bridge
- An OpenAI-compatible API server
- A matching model name and base URL in `.env`

## Setup

1. Sync dependencies with `uv sync`.
2. Copy `.env.example` to `.env`.
3. Edit `.env` and `config.toml`.
4. Start the terminal client with `uv run CLI.py`.

## Config files

### `.env`

| Key | Default | Meaning |
|---|---|---|
| `OPENAI_API_KEY` | `dummy` | Key passed to the OpenAI-compatible client |
| `OPENAI_BASE_URL` | `http://localhost:8000/v1` | Model endpoint base |
| `OPENAI_MODEL` | `DeepAnalyze-8B` | Model name used by the notebook agent |

### `config.toml`

| Key | Default | Meaning |
|---|---|---|
| `START_JUPYTER` | `true` | Start a local Jupyter Lab process or connect to an existing one |
| `JUPYTER_PORT` | `8888` | Local Jupyter Lab port |
| `PROMPT_TEMPLATE` | `general` | Prompt template name from `prompt/index.json` |

## Runtime flow

1. The server loads `.env` and `config.toml`.
2. It verifies the model endpoint by listing models.
3. It creates a local `workspace/` directory and a `deep_analyze.ipynb` notebook.
4. If `START_JUPYTER=true`, it launches Jupyter Lab with `uv run --project ... jupyter lab --port <port>`.
5. If `START_JUPYTER=false`, it expects an already running Jupyter Lab on that port.
6. The MCP bridge connects to `http://127.0.0.1:<port>/mcp` through `npx mcp-remote`.
7. The notebook is edited by inserting markdown and code cells, then executing them.

## Workspace behavior

- `workspace/` is created next to the Jupyter frontend files.
- `deep_analyze.ipynb` is the analysis notebook.
- Data can be uploaded through Jupyter Lab or copied directly into the workspace directory.
- The interactive loop keeps all analysis inside that notebook.
- The workspace file listing only looks a few levels deep, so very deep nesting is not ideal.
- Code-cell execution uses a bounded timeout in the notebook helper.

## Prompt selection

- `PROMPT_TEMPLATE` selects a file from the local prompt registry.
- If the named template is missing, the system falls back to no extra prompt.

## Troubleshooting

- Missing `.env` or `config.toml` is a hard failure.
- Port already in use means you need a different `JUPYTER_PORT` or an existing Lab instance.
- `uv run` failures usually mean the dependency sync or Python runtime is broken.
- `npx` or Node.js failures usually mean the MCP bridge cannot start.
- If the model base URL is wrong, the first `client.models.list()` call fails.
- If `START_JUPYTER=false`, the configured port must already be serving Jupyter Lab.
