# Settings and Configuration Troubleshooting

Use this table before modifying query/index code. All checks here are configuration-only and can be performed without calling an LLM or embedding endpoint.

## Quick diagnostic commands

```bash
python sub-skills/settings-and-configuration/scripts/print_named_settings.py --names fast debug openreview tier1_limits
python sub-skills/settings-and-configuration/scripts/validate_settings_json.py my-settings.json
python sub-skills/settings-and-configuration/scripts/validate_settings_json.py my-settings.json --check-extra local --check-extra qdrant
```

## Failure modes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Provider error says an OpenAI key is missing after switching to Claude/Gemini/local LLM. | Only `llm` was changed. `summary_llm`, `agent.agent_llm`, `embedding`, or `parsing.enrichment_llm` still uses an OpenAI default. | Update all model roles together. For Anthropic-only, set `llm`, `summary_llm`, `agent.agent_llm`, and use a non-OpenAI embedding such as `st-...`, `hybrid-st-...`, or `sparse`. |
| Anthropic key is set but debug config still asks for OpenAI. | `debug` changes `llm` and `summary_llm` to Claude Haiku, but inherits default `agent.agent_llm` and default OpenAI embedding. | Override `agent.agent_llm`, `agent.agent_llm_config`, and `embedding`. Validate with `validate_settings_json.py`. |
| Gemini or Ollama setting loads but fails at live call time. | Model name, local server, or provider config is incomplete. | Use a Router config with `model_list`; verify `model_name` matches the PaperQA role and `litellm_params.model` is the provider/local model. For local servers, ensure the server is running before the live run. |
| `gpt-5` or `o1` model reports unsupported temperature. | Reasoning models require `temperature=1`. This PaperQA version auto-overrides only when top-level `llm` starts with `gpt-5` or `o1`. | Set `temperature=1`, especially when the reasoning model is only `summary_llm` or `agent.agent_llm`. Treat the warning as expected when top-level `llm` triggers the override. |
| Settings JSON validates but a field has no effect. | Root `Settings` ignores unknown top-level keys; the field may be misplaced. | Use nested paths: `answer.*`, `parsing.*`, `prompts.*`, `agent.*`, `agent.index.*`. Do not use root `paper_directory`; use `agent.index.paper_directory`. |
| JSON fails with extra-field errors inside nested settings. | Nested models forbid unknown keys. | Move or remove the key. Print the schema with Python if needed, or compare against `settings-reference.md`. |
| CLI nested setting value is malformed. | Nested CLI flags must be passed as valid JSON-like values accepted by the settings parser; shell quoting may strip braces or quotes. | First write the settings as a JSON file and validate it with `validate_settings_json.py`; then route CLI usage to `../cli-and-indexing/`. |
| `PromptSettings` raises a validation error about variables. | Custom prompt includes variables that PaperQA does not provide to that prompt. | Use only the default prompt’s variable set. `context_inner` must include `{name}` and `{text}`. `pre` can use `{question}`. `post` can use `PQASession` field names. |
| Custom QA prompt compiles but citations break. | Prompt removed citation-key instructions or valid-key constraints. | Preserve the context and citation variables, and keep instructions to cite only valid keys from context. |
| `QdrantVectorStore` raises an import error. | `qdrant-client` is missing. | Install the `qdrant` extra or `qdrant-client`. Then construct `Docs(texts_index=QdrantVectorStore(...))`; vector store choice is not a JSON `Settings` field. |
| `st-...` or `hybrid-st-...` embedding fails to import. | The `local` extra / `sentence-transformers` is missing, or model weights are unavailable. | Install the local extra and ensure the model is available. If no downloads are allowed, choose `sparse` or a provider embedding already available. |
| Default or plain embedding model fails with provider/auth error. | Plain embedding names route through LiteLLM and may need the provider key. | Change `embedding`, set `embedding_config`, or choose `sparse` / `st-...` if cloud embeddings are not available. |
| Hybrid embedding fails even though sparse should work. | The dense component after `hybrid-` failed. | Validate the dense component separately. For no-cloud fallback, use `sparse` instead of `hybrid-...`. |
| Office files fail to parse. | The `office` extra is missing or parser dependencies are unavailable. | Install only if Office docs are in scope; route parser details to `../docs-and-parsing/`. |
| Zotero helper import fails. | The `zotero` extra is missing. | Install only if Zotero source ingestion is in scope; route setup to `../metadata-and-sources/`. |
| OpenReview helper import fails. | The `openreview` extra is missing. | Install only if OpenReview workflows are in scope; route setup to `../metadata-and-sources/`. |
| Rate limits are still exceeded while using `tier*_limits`. | Tier configs throttle `llm_config`, `summary_llm_config`, and embedding config; the agent LLM may still use an unthrottled default config, or actual account limits differ. | Add compatible `agent.agent_llm_config` rate limits and reduce `answer.max_concurrent_requests` / batch size. |
| LiteLLM complains about a missing `model_list` or unknown deployment. | Config used a single-model shape where Router config was expected, or `model_name` does not match the PaperQA role string. | Wrap custom routes in `model_list` and make `model_name` equal the value of `llm`, `summary_llm`, or `agent.agent_llm`. |
| Callback settings cannot be serialized to JSON. | `agent.callbacks` contains Python callables and is intentionally excluded from JSON. | Attach callbacks in Python when constructing/running the agent. Use `../agentic-rag/` for callback execution patterns. |

## Minimal validation checklist

Before a live run:

- [ ] JSON validates with `validate_settings_json.py`.
- [ ] No unknown top-level settings are reported.
- [ ] `llm`, `summary_llm`, `agent.agent_llm`, `embedding`, and parser `enrichment_llm` all point to intended providers.
- [ ] Required provider keys or local servers exist, without storing secrets in settings files.
- [ ] Router configs use `model_list` for custom models.
- [ ] Reasoning models use `temperature=1`.
- [ ] Optional extras are installed only for workflows in scope.
- [ ] Prompt templates pass variable validation and retain citation/context variables where needed.
