# MCP troubleshooting

Start with the safe diagnostic:

```bash
python scripts/check_mcp_env.py --env-file <optional-env-file>
```

It checks Python/import compatibility and required environment-variable presence. It does not start the MCP server, call a model API, run DeepKE predictors, or mutate configs.

## Environment variables

| Variable | Used by | Required for | Common problem | Fix direction |
| --- | --- | --- | --- | --- |
| `DEEPKE_PATH` | server tools | all local tool execution | unset, points at the MCP project instead of the DeepKE checkout root, or lacks expected example folders | Set it to the local DeepKE checkout root that contains the NER/RE/AE/EE example directories. |
| `CONDA_PY` | `deepke_ner`, `deepke_re`, `deepke_ae` | NER/RE/AE subprocesses | unset, points at an executable instead of a directory prefix, or lacks a trailing path separator in the unmodified wrapper | Set it to the trusted Python directory prefix expected by the wrapper; verify that adding `python` names the intended interpreter. |
| `CONDA_EE_PY` | `deepke_ee` | EE subprocesses | same prefix issues as `CONDA_PY`; event extraction may require a different dependency set | Use the Python prefix for the EE-compatible environment. |
| `API_KEY` | interactive client | LLM tool selection | unset or invalid credential | Provide a valid key only in local env/client settings, never in shared skill files. |
| `BASE_URL` | interactive client | OpenAI-compatible endpoint | unset, wrong API route, blocked network/proxy | Use an endpoint compatible with the OpenAI chat-completions client. |
| `MODEL` | interactive client | LLM tool selection | unset or model not available at `BASE_URL` | Select a model served by the configured endpoint. |

Do not publish actual variable values in logs or generated artifacts if they reveal private paths or credentials.

## Missing or incompatible `mcp`

Symptoms:

- `ModuleNotFoundError: No module named 'mcp'`
- `ModuleNotFoundError: No module named 'mcp.server.fastmcp'`
- Server starts but the MCP client cannot initialize/list tools.

Likely causes:

- The MCP wrapper environment is not active.
- `mcp` was installed without the CLI extras needed by the source project.
- The installed `mcp` version does not include the FastMCP import path used by the wrapper.

Fix direction:

1. Use a Python 3.11-capable wrapper environment.
2. Install a compatible package set such as `mcp[cli]`, `httpx`, `openai`, `pyyaml`, and `python-dotenv`.
3. Re-run `scripts/check_mcp_env.py`; it imports `mcp.server.fastmcp.FastMCP`, client stdio helpers, and companion dependencies.

## Missing `python-dotenv`

The wrapper imports `load_dotenv()` in both server and client code. If `dotenv` is missing, the server/client can fail before reading `.env` values.

Fix direction: install `python-dotenv` in the MCP wrapper environment or export the variables in the parent process and remove the dotenv dependency only in a deliberate local fork.

## Path and working-directory failures

Symptoms:

- `No module named convert_to_tsv` when launching the server.
- Tools appear missing even though the server file exists.
- Shell commands fail with `No such file or directory`.

Likely causes:

- The server was launched from a working directory where its sibling helper module is not importable.
- The `CONDA_PY` or `CONDA_EE_PY` prefix is missing a trailing separator in the unmodified wrapper, resulting in an invalid command such as a prefix directly concatenated with `python`.
- The server assumes Linux-style shell commands (`bash`, `cd`, `&&`) and paths.

Fix direction:

- Launch the server with a working directory that contains `server.py` and the conversion helper, or set the module search path deliberately.
- Validate prefixes with the bundled diagnostic before launching.
- On Windows, expect to adapt shell/path handling in a local fork rather than using the Linux-oriented wrapper unchanged.

## Missing checkpoints, data, or incompatible configs

Symptoms:

- MCP tool returns `[运行失败]` with a predictor exception.
- Predictor stdout is empty or contains missing-file/checkpoint errors.
- EE fails while reading trigger/role result files.

Likely causes:

- The underlying DeepKE example was never trained or configured for prediction.
- Required model weights, label vocabularies, dataset files, or result directories are absent.
- Configs point to data/model paths that do not exist in the local checkout.

Fix direction:

- Validate the underlying DeepKE example workflow outside MCP in the intended environment before exposing it through MCP.
- Keep the generated skill's statements conservative: MCP availability is not equivalent to checkpoint availability.
- For EE, verify both trigger and role artifacts and result paths, because the wrapper reads both after running event commands.

## Source config and data mutation

The original server mutates local files:

- NER rewrites the standard NER prediction YAML `text` field.
- EE regenerates one raw JSONL file plus role/trigger TSV files and rewrites the EE training config `task_name` between `trigger` and `role`.

Risks:

- Concurrent requests can race and corrupt each other's inputs.
- A previously tuned config can be overwritten.
- A version-controlled checkout may become dirty.

Fix direction:

- Only run the source server when the user explicitly asks to operate a local DeepKE checkout and accepts these risks.
- Prefer a scratch checkout, a copied example directory, or a local patch that writes to task-specific temporary files.
- Do not instruct a downstream agent to mutate source configs just to answer a documentation or planning question.

## API client issues

Symptoms:

- Interactive client starts but never calls tools.
- Chat-completions call fails with authentication, model, or base URL errors.
- The model returns prose instead of an MCP tool call.

Likely causes:

- `API_KEY`, `BASE_URL`, or `MODEL` is missing or incompatible.
- The selected chat model does not support OpenAI-style tool calling.
- Network/proxy settings block the endpoint.
- The client only wraps one tool-call loop pattern and may not support provider-specific response shapes.

Fix direction:

- First verify the server independently with an MCP-capable client or a simple list-tools check.
- Use an OpenAI-compatible endpoint and a model known to support function/tool calling.
- Keep credentials in local environment/client settings only.
- If using a non-OpenAI provider, adapt the client response parsing in a local fork.

## Security notes

- Environment-variable path values are interpolated into shell commands by the original server. Treat them as trusted configuration only.
- Do not expose the stdio server through a network bridge for untrusted users unless shell execution, path validation, input size limits, and file mutation have been hardened.
- The bundled diagnostic intentionally avoids printing environment-variable values by default to reduce secret/path leakage.
