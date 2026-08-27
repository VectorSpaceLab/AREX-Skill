# Co-STORM troubleshooting

Use `scripts/run_costorm.py --dry-run ...` first. It performs no network, embedding, retriever, or LLM calls and reports missing environment variables for the selected model/retriever plan.

## Credential and environment errors

| Symptom / error | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: ENCODER_API_TYPE environment variable is not set.` during `CoStormRunner(...)` | The runner constructs `Encoder()` in `__init__`; no embedding provider was selected. | Set `ENCODER_API_TYPE=openai` or `ENCODER_API_TYPE=azure` before runner construction. |
| `Unsupported ENCODER_API_TYPE ...` | The encoder wrapper only supports OpenAI-style and Azure-style embedding configuration in this package version. | Use `openai` or `azure` for Co-STORM mind-map embeddings, even if chat LMs use another LiteLLM provider. |
| OpenAI embedding/model call fails with missing API key | `ENCODER_API_TYPE=openai` or `openai/...` models require `OPENAI_API_KEY`. | `export OPENAI_API_KEY="..."`; verify `--model openai/gpt-4o` or per-component models. |
| Azure embedding/model call fails with missing base/version/key | `ENCODER_API_TYPE=azure` or `azure/...` models require Azure variables. | Set `AZURE_API_KEY`, `AZURE_API_BASE`, and `AZURE_API_VERSION`; use LiteLLM model strings like `azure/<deployment-name>`. |
| `OPENAI_API_TYPE` is missing when calling `CoStormRunner.from_dict(...)` | `from_dict` ignores serialized LM config and initializes default LMs from `OPENAI_API_TYPE`. | Prefer explicit runner reconstruction; otherwise set `OPENAI_API_TYPE=openai` or `OPENAI_API_TYPE=azure` plus matching keys before `from_dict`. |
| Older snippets import `OpenAIModel` or `AzureOpenAIModel` | Legacy examples used provider-specific wrappers. | Use `knowledge_storm.lm.LitellmModel` for new code. |

## Search retriever errors

| Retriever | Missing credential / option symptom | Required fix |
| --- | --- | --- |
| `bing` | Runtime error requiring Bing subscription key. | Set `BING_SEARCH_API_KEY`; construct with `BingSearch(bing_search_api_key=..., k=...)`. |
| `you` | Runtime error requiring You.com key. | Set `YDC_API_KEY`. |
| `brave` | Runtime error requiring Brave key. | Set `BRAVE_API_KEY`. |
| `serper` | Runtime error requiring Serper key. | Set `SERPER_API_KEY`. |
| `duckduckgo` | Import error for `duckduckgo_search` or network/search failures. | Install package extras if needed and ensure public web access; no API key is required. |
| `tavily` | Import error for `tavily` or missing key. | Install `tavily-python` if needed and set `TAVILY_API_KEY`. |
| `searxng` | `RuntimeError: You must supply searxng_api_url`. | Pass `--searxng-api-url ...` or set `SEARXNG_API_URL`; set `SEARXNG_API_KEY` only if your instance requires it. |

If credentials are set in `secrets.toml`, make sure the helper is launched from a working directory where that file is visible, or pass `--secrets-file /path/to/secrets.toml`.

## Rate limits, timeouts, and high cost

| Symptom | Cause | Fix |
| --- | --- | --- |
| LLM provider returns rate-limit or quota errors during warm start. | Warm start runs multiple expert QA threads plus outline/report synthesis. | Lower `--warmstart-max-thread`, `--warmstart-max-num-experts`, and `--warmstart-max-turn-per-experts`; use smaller `--retrieve-top-k` and `--max-search-queries`. |
| Search provider rate-limits or returns intermittent failures. | Too many concurrent retriever calls or too many query decompositions. | Lower `--max-search-thread`, `--max-search-queries`, and `--retrieve-top-k`; retry after provider cooldown. |
| Session takes much longer than expected. | `warm_start()` is a mini-STORM process, not a cheap initialization. It performs background search, expert conversations, outline generation, knowledge-base insertion, and report-to-conversation synthesis. | Run a smoke configuration first: 1-2 warm-start experts, 1 turn per expert, 1-2 search queries, low retriever `k`, and 0-1 observed turns. |
| Report generation is slow after many turns. | `knowledge_base.reorganize()` and `generate_report()` can run section generation over many nodes. | Raise `node_expansion_trigger_count` to reduce section count, or generate reports less frequently. |
| Output has many repeated or narrow turns. | Moderator or multi-expert policy may be disabled, or the topic/user utterance is too narrow. | Enable moderator/multi-experts, lower `moderator_override_N_consecutive_answering_turn`, or inject a broader user utterance. |

## `step()` fails on empty conversation history

Symptom examples:

```text
IndexError: list index out of range
```

Cause: `CoStormRunner.step()` reads `self.conversation_history[-1]` before checking whether `user_utterance` was provided. A new runner has empty conversation history.

Fixes:

1. Normal workflow: always call `runner.warm_start()` before any `step()` call.
2. Advanced workflow: manually seed `runner.conversation_history` with a valid `ConversationTurn(role="Guest", raw_utterance="...", utterance_type="Original Question")` before first `step()`. Do this only if you intentionally skip warm start and understand that the knowledge base will be empty until a generated turn inserts cited information.
3. For `rag_only_baseline_mode=True`, inject a `Guest` question before observing a PureRAG answer; the PureRAG policy asserts that the previous turn is `Guest`.

## User injection vs system observation confusion

| Observation | Explanation | Fix |
| --- | --- | --- |
| `step(user_utterance="...")` returns immediately and no system answer appears. | User injection only appends a `Guest` turn. It does not generate a system response. | Call `step()` again to observe the system response. |
| The moderator asks a question right after warm start. | Warm start sets a moderator override so the first system turn can guide the discourse. | This is expected; set `disable_moderator=True` only if you want answer-focused behavior. |
| Multi-expert turns rotate unexpectedly. | If the previous turn is not a question and multi-experts are enabled, the discourse manager rotates through generated experts. | Set `disable_multi_experts=True` for deterministic general-provider behavior. |

## Logging stage nesting errors

| Symptom / message | Cause | Fix |
| --- | --- | --- |
| `RuntimeError: No pipeline stage is currently active.` | `log_event(...)` was used without `log_pipeline_stage(...)`. | Wrap custom events in `with logging_wrapper.log_pipeline_stage("..."):` or let runner methods handle logging. |
| `A pipeline stage is already active, ending the current stage safely.` | A pipeline stage was started while another was active. | Do not nest `log_pipeline_stage(...)`; use nested `log_event(...)` inside one stage. |
| Missing or split log stages in `log.json`. | A custom nested stage ended the current runner stage early. | Avoid custom stages around `warm_start()`, `step()`, or `generate_report()` unless you understand `LoggingWrapper` stage semantics. |

## `from_dict` restore caveat

Symptom:

- Restored runner uses default OpenAI/Azure/Together settings instead of your saved LiteLLM models.
- Restored runner defaults to Bing retriever or requires Bing credentials even if the original run used another retriever.
- Serialized state contains `lm_config`, but changing it in JSON does not affect `from_dict` behavior.

Cause: current `CoStormRunner.from_dict(data, callback_handler=None)` ignores serialized `lm_config` and initializes a fresh default `CollaborativeStormLMConfigs` from `OPENAI_API_TYPE`. It also constructs a new runner without your original custom retriever.

Fix:

```python
# Robust resume outline
state = json.load(open("instance_dump.json"))
restored = CoStormRunner.from_dict(state)  # only to rebuild state objects

# Then rebuild your intended lm_config and retriever explicitly,
# construct a new CoStormRunner, and copy restored conversation/history/KB.
```

For production resume workflows, prefer writing a separate run manifest with model names, retriever choice, and non-secret provider settings. Do not rely on `from_dict` alone.

## Empty or failed report generation

| Symptom | Cause | Fix |
| --- | --- | --- |
| `report.md` is empty. | The knowledge base has no child section nodes, or no cited information was inserted. `KnowledgeBase.to_report()` iterates root children and returns an empty string if there are none. | Ensure `warm_start()` completed, at least one generated system turn inserted cited information, and `knowledge_base.reorganize()` was called before `generate_report()`. |
| Report contains headings with little content. | Retrieved information was sparse or unrelated; citations were not inserted under useful nodes. | Increase `retrieve_top_k`, improve topic/user utterance specificity, or switch retrievers. |
| Report generation silently proceeds after earlier warm-start failure. | `LoggingWrapper.log_pipeline_stage` catches exceptions and records/logs them, so caller code may continue with an empty or partial runner state. | After `warm_start()`, check `runner.conversation_history`, `runner.knowledge_base.root.children`, and `len(runner.knowledge_base.info_uuid_to_info_dict)` before stepping/reporting. |
| RAG-only baseline report is empty despite retrieved info. | RAG-only mode can insert information under the root; report generation only emits child sections. | Use normal Co-STORM mode for report generation, lower `node_expansion_trigger_count`, or manually create section nodes before generating a report. |

Validation snippet:

```python
if not runner.conversation_history:
    raise RuntimeError("warm_start did not populate conversation_history")
if not runner.knowledge_base.root.children:
    print("Warning: knowledge base has no section nodes; report may be empty")
if not runner.knowledge_base.info_uuid_to_info_dict:
    print("Warning: no cited information in knowledge base")
```

## State dump contains secrets

Symptom: `instance_dump.json` includes `api_key` or token-looking fields under `lm_config`.

Cause: `CollaborativeStormLMConfigs.to_dict()` serializes LM `.kwargs`.

Fix: redact secret-looking fields before sharing. The bundled helper writes a redacted instance dump; if calling APIs directly, apply your own redaction for keys containing `api_key`, `token`, `password`, or `secret`.
