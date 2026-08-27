# Cross-Cutting Troubleshooting

Read this before diving into a sub-skill when OptiLLM fails to install, import, start, select a provider, or load optional features.

## Import fails immediately

**Symptoms**

- `ModuleNotFoundError` for `cerebras`, `openai`, `flask`, `torch`, `transformers`, `mcp`, `presidio_*`, or another dependency.
- `optillm --version` fails before printing a version.

**Likely causes**

- The package was installed with missing runtime dependencies.
- A minimal/proxy-only install is being used for a plugin or local-inference workflow that needs full dependencies.
- The MCP plugin expects an MCP package version with `mcp.client.websocket`.

**Recovery**

1. Run `python scripts/inspect_optillm.py --plugins --backend` from this skill to identify missing imports without provider calls.
2. For full package work, install the package normally (`pip install optillm`) or install the source checkout editable with dependencies.
3. If MCP import fails on `mcp.client.websocket`, use an MCP package version below `2` until the repo code is updated for MCP 2.x.
4. If the task only needs lightweight external proxying, avoid enabling plugins/local inference that need heavy optional packages.

## Wrong provider path selected

**Symptoms**

- OptiLLM tries to load a HuggingFace model when the user expected OpenAI/Cerebras/Azure/LiteLLM.
- The service reports local inference behavior after a provider key was configured.

**Likely cause**

`OPTILLM_API_KEY` takes precedence and activates built-in local inference. It is also the server-auth flag name, so it can be confused with upstream API keys.

**Recovery**

- For external OpenAI-compatible routing, unset `OPTILLM_API_KEY` and set `OPENAI_API_KEY` plus `--base-url` if needed.
- For server-side auth, prefer `--optillm-api-key` only when you intentionally want clients to authenticate to the OptiLLM server; check the provider env separately.
- Read [configuration.md](configuration.md) for the exact provider precedence.

## Server starts but clients fail

**Symptoms**

- `401 Invalid Authorization header`.
- Connection refused or client points to the wrong path.
- Streaming returns unexpected chunks.

**Recovery**

- Confirm `/health` works on the chosen port.
- Use base URL `http://<host>:<port>/v1`, not the root URL.
- If `--optillm-api-key` is set, clients need `Authorization: Bearer <server-key>`.
- For OpenAI SDKs, set both `base_url` and `api_key`; a placeholder key is fine for local inference when server auth is not enabled.
- Read [../sub-skills/proxy-server/references/troubleshooting.md](../sub-skills/proxy-server/references/troubleshooting.md).

## Approach composition errors

**Symptoms**

- `Unknown approach: ...`
- Error says `'none' approach cannot be combined with other approaches`.
- A model name is split incorrectly.

**Recovery**

- Use `approach-model`, `a&b-model`, or `a|b-model` with known approach/plugin slugs before the first non-slug model segment.
- Do not combine `none` with other approaches.
- Run `python sub-skills/optimization-approaches/scripts/approach_matrix.py --parse 'bon|moa|mcts-gpt-4o-mini'` to verify parsing offline.

## Provider/API limitations

**Symptoms**

- BoN/MoA/self-consistency style methods fail or give only one answer.
- Anthropic, llama.cpp, or Ollama endpoints reject request fields.
- Responses are empty, `None`, or truncated.

**Recovery**

- Prefer approaches that do not require multiple completions when the provider lacks `n` support: `cot_reflection`, `leap`, `plansearch`, `rstar`, `rto`, `self_consistency`, `re2`, or `z3` depending on task and endpoint behavior.
- Reduce token budgets or multi-agent counts for cost/latency.
- Inspect whether the endpoint supports system messages, `n`, streaming, and max-token field names.

## Local model/backend failures

**Symptoms**

- CUDA/MPS/MLX import failures, out-of-memory errors, or HuggingFace download errors.
- Blank HF token causes illegal authorization header errors.
- Generation runs until token limit instead of stopping.

**Recovery**

- Run `python sub-skills/local-inference-decoding/scripts/check_local_backend.py --json` before model loading.
- Ensure blank `HF_TOKEN`/HuggingFace token env vars are unset, not empty strings.
- Set `OPTILLM_MAX_TOKENS` for small models that do not emit EOS reliably.
- Read [../sub-skills/local-inference-decoding/references/troubleshooting.md](../sub-skills/local-inference-decoding/references/troubleshooting.md).

## Plugin side effects

Some plugins perform browser automation, fetch URLs, execute code, call MCP tools, maintain memory files, or load models. Before enabling them in production or against private data, read [../sub-skills/plugins-and-tools/references/troubleshooting.md](../sub-skills/plugins-and-tools/references/troubleshooting.md) and prefer dry-run/config inspection first.
