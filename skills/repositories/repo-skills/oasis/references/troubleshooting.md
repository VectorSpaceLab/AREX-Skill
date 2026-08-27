# OASIS troubleshooting

Use this cross-cutting reference when installation, import, credentials, optional backends, database lifecycle, or large-experiment constraints block an OASIS task. Route workflow-specific errors to the nearest sub-skill after this first triage.

## Install and import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'oasis'` | `camel-oasis` is not installed in the active Python. | Install with `pip install camel-oasis` or local editable install; then run `python scripts/check_oasis_install.py`. |
| Import fails with `cannot import name 'FastMCP' from 'mcp.server'` | CAMEL `0.2.78` resolved an incompatible `mcp>=2` package. | Install a compatible MCP line with `pip install 'mcp<2'`, or move to a CAMEL release that supports MCP 2.x. |
| `pip check` reports conflicts after installation | Resolver picked incompatible transitive packages. | Create a clean Python 3.10/3.11 environment; reinstall `camel-oasis`; pin known problematic packages such as `mcp<2` if needed. |
| `python` is 3.12+ or 3.9- | Package metadata requires `>=3.10,<3.12`. | Use Python 3.10 or 3.11. |
| Cairo/igraph visualization fails | Graph PDF/plotting needs igraph plus cairo/cairocffi and system libraries. | Skip visualization for logic tests, or install the missing cairo stack before `AgentGraph.visualize`. |

## Credentials and model backends

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Missing or empty required API keys... OPENAI_API_KEY` during `SocialAgent` creation | `model=None` asks CAMEL to create a default OpenAI model. | Provide a real model/backend and credentials for LLM runs, or use the bundled manual smoke helper which avoids provider calls. |
| `LLMAction` hangs or fails with provider errors | Provider key, base URL, function/tool calling support, or rate limits are wrong. | Verify provider with a tiny external call, lower `semaphore`, and set a token/cost budget before rerunning. |
| VLLM/local-server examples fail | Server URL, served model name, GPU allocation, or network route is missing. | Confirm the server is reachable and exposes the expected OpenAI-compatible model name before running OASIS agents. |
| DeepSeek/OpenAI-compatible backend accepts key but no tool calls occur | Model or provider does not support the tool-calling shape used by CAMEL. | Switch to a model with tool/function calling or restrict to `ManualAction` for that run. |

## Optional backends and services

| Surface | Blocker | Recovery |
| --- | --- | --- |
| TwHIN-BERT / personalized recommendation | Model downloads, transformer cache, torch/CUDA, or OpenAI embeddings may be required. | Use `recsys_type="reddit"` or `"random"` for small local checks; approve/cache models before optional personalized runs. |
| Neo4j graph backend | `NEO4J_URI`, username, password, and reachable service required. | Use in-memory `igraph` unless Neo4j persistence/visualization is explicitly needed. |
| OpenAI embeddings | Requires provider credentials and budget. | Keep `use_openai_embedding=False` or provide credentials and cost limits. |
| Large VLLM experiments | Need downloaded model, GPU/server, host/port, and enough VRAM. | Downscale first or treat as blocked until runtime details are supplied. |

## Runtime and database lifecycle

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `database_path is required for DefaultPlatformType` | `oasis.make` used `DefaultPlatformType` without a DB file path. | Pass `database_path="...db"`, or pass a custom `Platform` with its own `db_path`. |
| DB is locked or missing final rows | Platform loop was not closed. | Always run `await env.close()` in `finally`. Inspect the DB only after close returns. |
| Old rows remain in a run | Existing DB was reused. | Delete the DB before the run or choose a fresh path. |
| No recommended posts | `rec` table updates before current-step actions, or no posts exist. | Create content, then run another step; use `platform-actions` DB summary to inspect `rec` and `trace`. |
| Logs appear in `./log` | OASIS creates log files relative to the current working directory. | Run from a disposable working directory for smoke tests or clean up logs after the run. |

## Data and profile issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Reddit generator fails with missing key | Profile JSON lacks `realname`, `username`, `bio`, `persona`, `age`, `gender`, `mbti`, or `country`. | Use `agent-profiles/scripts/validate_oasis_profiles.py --kind reddit-json --path ...`. |
| Twitter generator fails with missing column | CSV lacks `name`, `username`, `user_char`, or `description`. | Use `agent-profiles/scripts/validate_oasis_profiles.py --kind twitter-csv --path ...`. |
| Custom prompt raises `Missing required keys` | `TextPrompt.key_words` are not all present in flat `UserInfo.profile`. | Add missing keys or simplify the template; nested keys are not resolved by the built-in validator. |
| Extra prompt keys warning | `UserInfo.profile` has keys not used by the custom template. | Safe to ignore if intentional; otherwise remove unused keys to reduce confusion. |

## Safe first checks

1. Run `python scripts/check_oasis_install.py` from the root skill directory.
2. Validate profile files with `sub-skills/agent-profiles/scripts/validate_oasis_profiles.py`.
3. Run a no-LLM simulation with `sub-skills/simulation-workflows/scripts/oasis_manual_smoke.py`.
4. Inspect generated DBs with `sub-skills/platform-actions/scripts/oasis_db_summary.py`.
5. Only then attempt real `LLMAction`, TwHIN, VLLM, Neo4j, or large experiment workflows with explicit credentials and budget.
