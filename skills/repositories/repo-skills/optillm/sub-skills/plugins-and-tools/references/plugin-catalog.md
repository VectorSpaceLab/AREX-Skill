# Plugin Catalog

Read this to choose plugin slugs and understand verified plugin call signatures.

## Verified plugin slugs and signatures

| Slug | Signature shape | Main use |
| --- | --- | --- |
| `memory` | `run(system_prompt, initial_query, client, model)` | Short-term/unbounded context memory with optional file persistence. |
| `readurls` | `run(system_prompt, initial_query, client=None, model=None)` | Fetch URLs from the prompt and add webpage content. |
| `privacy` | `run(system_prompt, initial_query, client, model)` | PII anonymization before provider call and deanonymization after. |
| `genselect` | `run(system_prompt, initial_query, client, model, request_config=None)` | Generate candidates and select the best response. |
| `majority_voting` | `run(system_prompt, initial_query, client, model, request_config=None)` | Generate multiple answers and vote/normalize. |
| `web_search` | `run(system_prompt, initial_query, client=None, model=None, request_config=None)` | Google search via browser automation. |
| `deep_research` | `run(system_prompt, initial_query, client, model, request_config=None)` | Iterative deep research reports with search/fetch/evaluation loops. |
| `deepthink` | `run(system_prompt, initial_query, client, model, request_config=None)` | Self-discover and uncertainty-routed reasoning. |
| `longcepo` | `run(system_prompt, initial_query, client, model)` | Long-context divide-and-conquer QA with `<CONTEXT_END>`. |
| `spl` | `run(system_prompt, initial_query, client, model, request_config=None)` | System Prompt Learning strategies and optional learning mode. |
| `proxy` | `run(system_prompt, initial_query, client, model, request_config=None)` | Provider load balancing/failover and optional approach wrapping. |
| `mcp` | `run(system_prompt, initial_query, client, model)` | Model Context Protocol tool/resource/prompt integration. |
| `compact` | `run(system_prompt, initial_query, client, model, request_config=None)` | Compress older conversation turns to fit context limits. |
| `coc` | `run(system_prompt, initial_query, client, model)` | Chain-of-code style execution/simulation. |
| `executecode` | `run(system_prompt, initial_query, client, model)` | Execute Python code found in requests or model outputs. |
| `json` | `run(system_prompt, initial_query, client, model, request_config=None)` | Structured outputs with JSON schema/Pydantic/outlines. |
| `router` | `run(system_prompt, initial_query, client, model, **kwargs)` | Classifier-based automatic approach routing. |

## Usage patterns

Plugins can be selected the same way as approaches when loaded:

```text
memory-gpt-4o-mini
privacy&moa-gpt-4o-mini
proxy-gpt-4
```

Or through request config when the server is in auto mode:

```python
extra_body={"optillm_approach": "json", "response_format": {...}}
```

For the proxy plugin, `request_config` can include `proxy_wrap`, `wrapped_approach`, or `wrap` to run another approach/plugin through proxy-selected providers.

## Side-effect classification

| Plugin | Side effects to consider |
| --- | --- |
| `memory` | Optional file writes when `OPTILLM_MEMORY_FILE` is set. |
| `readurls` | Network fetches arbitrary URLs in prompt. |
| `privacy` | Loads Presidio/spaCy analyzer resources; handles sensitive text. |
| `web_search` | Browser automation, external web requests, CAPTCHA risk. |
| `deep_research` | Multiple web searches/fetches and long provider calls. |
| `executecode`, `coc` | Executes or simulates code; sandbox untrusted inputs. |
| `json` | Can load a default HuggingFace model for outlines generation. |
| `router` | Can load a classifier model from local or remote model storage. |
| `mcp` | Calls external MCP tools/resources/prompts; tool side effects depend on server. |
| `spl` | May create/update strategy storage in learning mode. |
| `proxy` | Sends requests to configured provider pool. |
| `longcepo`, `deepthink`, `genselect`, `majority_voting`, `compact` | Additional provider calls and token cost. |

## Load-time notes

Plugin loading scans package plugin files and, when configured, a local plugin directory. A module missing either `SLUG` or `run` is skipped. Per-plugin import errors are logged, and successfully loaded plugins remain available.

In the inspected environment, MCP 2.x lacked `mcp.client.websocket`; using `mcp<2` restored the current repo plugin import. Treat this as version-sensitive plugin evidence until the package updates its MCP imports.
