# DeepKE MCP workflows

This reference distills the local MCP wrapper behavior into operating guidance. It is intentionally self-contained and does not require opening the DeepKE checkout documentation.

## What the local service exposes

The MCP wrapper starts a FastMCP server named `DeepKE` over stdio and registers four tools:

- `deepke_ner` for standard named-entity recognition prediction.
- `deepke_re` for standard relation extraction prediction.
- `deepke_ae` for standard attribute extraction prediction.
- `deepke_ee` for event trigger and argument extraction prediction.

The tools are not standalone models. Each tool shells out to a local DeepKE example workflow under the checkout named by `DEEPKE_PATH`, using Python executable prefixes supplied through `CONDA_PY` and, for event extraction, `CONDA_EE_PY`.

## Local deployment checklist

Use this checklist before configuring an MCP client:

1. Prepare a local DeepKE checkout that contains the classic example directories for NER, RE, AE, and EE.
2. Prepare the DeepKE runtime environment(s) that can run the desired predictors. For NER, RE, and AE, the wrapper uses the `CONDA_PY` prefix. For EE, it uses `CONDA_EE_PY`.
3. Ensure the selected example workflow already has compatible config files, datasets, and trained checkpoints. The MCP layer does not train or download missing weights for you.
4. Prepare a separate Python 3.11-capable MCP wrapper environment with `mcp[cli]`, `openai`, `httpx`, `pyyaml`, and `python-dotenv` available. The FastMCP import path verified for this repo is `mcp.server.fastmcp.FastMCP`.
5. Set environment variables in the process that starts the server or in a local `.env` file loaded by the server/client code:
   - `DEEPKE_PATH`: local DeepKE checkout root.
   - `CONDA_PY`: directory prefix that the source wrapper concatenates with `python` for NER/RE/AE commands; in the unmodified wrapper this normally needs a trailing path separator.
   - `CONDA_EE_PY`: directory prefix concatenated with `python` for EE commands.
   - `API_KEY`, `BASE_URL`, `MODEL`: needed by the bundled interactive client that asks an OpenAI-compatible chat model to choose tools.
6. Run the bundled diagnostic first: `python scripts/check_mcp_env.py --env-file <optional-env-file>`. This checks imports and variable presence without launching the MCP server or calling models.

## Server invocation patterns

### MCP client configuration

For a Cursor/Cline-like client, configure a stdio server command that runs the server from the MCP tools directory. Use placeholders instead of hard-coding private paths in shared files:

```json
{
  "mcpServers": {
    "DeepKE": {
      "command": "uv",
      "args": [
        "--directory",
        "<path-to-deepke-mcp-tools>/tools",
        "run",
        "server.py"
      ]
    }
  }
}
```

The important details are:

- The working directory should make the helper import `convert_to_tsv` visible to `server.py`.
- The server process must inherit the DeepKE and API environment variables, either from the shell, the MCP client's environment settings, or a local `.env` file.
- Use a local-only server unless you have audited the shell-command and file-mutation behavior.

### Interactive client flow

The repo also provides an interactive client/launcher flow. It is reference-only for this generated skill because it depends on an OpenAI-compatible API key, an interactive terminal, and a local checkout layout.

The flow is:

1. Start the client launcher from the MCP tools project.
2. The client starts the stdio server process and initializes an MCP `ClientSession`.
3. The client lists registered tools and converts their MCP input schemas into OpenAI-style function tool definitions.
4. For each user prompt, the chat model may request one tool call.
5. The client calls the MCP tool, appends the tool result, and asks the model for the final response.

## Tool calling behavior

- Tool calls return text, not typed JSON objects.
- NER, RE, and AE return predictor stdout on success and bracketed Chinese error text on failure.
- EE returns a combined Chinese report containing trigger metrics/content and role metrics/content after reading prediction output files.
- The wrapper serializes calls through local files and subprocesses. Avoid concurrent calls against the same checkout because config and data files can be overwritten.

## Safety caveats

- The server constructs shell commands from environment-variable values. Keep those variables trusted and do not expose the server to untrusted remote callers without hardening.
- NER writes the selected text into a prediction YAML file. EE rewrites a training YAML `task_name` and regenerates event raw/TSV files before running event commands. This is a mutation of the local DeepKE checkout.
- EE invokes event `run.py` twice before prediction; depending on the local config, this may be expensive or may require checkpoints/datasets.
- The MCP project was documented as early-stage and Linux-oriented. Windows paths and shells need adaptation.

## Source wrapper import/adaptation decisions

- `tools/convert_to_tsv.py` was adapted into the bundled [../scripts/convert_text_to_tsv.py](../scripts/convert_text_to_tsv.py) because it is a pure, reusable helper.
- `tools/server.py` is not bundled as a runtime script because it shells out through local checkout paths, mutates example configs/data, and requires model checkpoints. Its behavior is distilled in this reference and the API reference.
- `tools/client.py` and the launcher are not bundled because they are interactive and API-credential bound. Their flow is documented here for users who explicitly need local client operation.
