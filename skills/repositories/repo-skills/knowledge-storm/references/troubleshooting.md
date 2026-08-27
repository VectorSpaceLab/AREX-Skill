# Cross-cutting troubleshooting

Start with the workflow-specific sub-skill troubleshooting files. Use this root reference for package-wide install, import, credential, optional dependency, output, and version problems.

## Install and import checks

Run:

```bash
python scripts/check_knowledge_storm_runtime.py --json
```

Common symptoms:

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: knowledge_storm` | The public package is not installed in the active Python environment. | `pip install knowledge-storm`; then rerun the runtime checker. |
| `pip check` reports incompatible dependencies | Existing environment has conflicting `dspy`, `litellm`, `pydantic`, `torch`, or retrieval packages. | Use a fresh Python 3.10+ environment, install `knowledge-storm`, then add only the optional packages needed for the selected workflow. |
| `knowledge_storm.__version__` differs from distribution metadata | The source used for this skill declared `setup.py` version `1.1.1` while live import reported `1.1.0`. | Treat as a warning. Prefer API behavior verified by the installed package, and check `references/repo-provenance.md` if staleness matters. |
| Legacy examples import `OpenAIModel` or `AzureOpenAIModel` | Older repo examples predate the LiteLLM integration. | Prefer `LitellmModel` patterns in this skill's bundled helpers and references. |

## Credential errors

| Error surface | Required action |
| --- | --- |
| OpenAI chat or embedding calls fail | Set `OPENAI_API_KEY` or pass a TOML file with that key. |
| Azure chat or embedding calls fail | Set `AZURE_API_KEY`, `AZURE_API_BASE`, and `AZURE_API_VERSION`; use Azure deployment names in LiteLLM model strings. |
| STORM/Co-STORM search retriever fails immediately | Set the retriever key (`BING_SEARCH_API_KEY`, `YDC_API_KEY`, `BRAVE_API_KEY`, `SERPER_API_KEY`, `TAVILY_API_KEY`) or switch to a configured retriever. |
| Co-STORM `Encoder()` fails with missing `ENCODER_API_TYPE` | Set `ENCODER_API_TYPE=openai` or `ENCODER_API_TYPE=azure` before constructing `CoStormRunner`. |
| SearXNG says no API URL | Pass `--searxng-api-url ...` or set `SEARXNG_API_URL`; the key is optional and depends on your SearXNG instance. |
| Qdrant Cloud connection fails | Set the online vector DB URL and `QDRANT_API_KEY`; verify collection name and embedding model match the collection. |

Dry-run modes report missing env vars without making model/search/embedding calls.

## Optional dependency errors

| Symptom | Workflow | Fix |
| --- | --- | --- |
| `duckduckgo_search` import error | Internet retriever `duckduckgo` | Install the optional package or choose a credentialed retriever. |
| `tavily` import error | Internet retriever `tavily` | Install `tavily-python` and set `TAVILY_API_KEY`. |
| `qdrant_client`, `langchain_qdrant`, or `langchain_huggingface` import error | VectorRM / Qdrant | Install the vector-store and embedding dependencies required by `knowledge-storm` for VectorRM. |
| `sentence_transformers` or Hugging Face model download error | VectorRM embeddings | Check model name, internet/cache access, and device selection; retry with `--device cpu`. |
| `torch.cuda.is_available()` is false | Optional embedding acceleration | Use CPU or install a CUDA-capable torch build only if local embedding throughput requires it. |

## Rate limits, cost, and latency

STORM and Co-STORM can issue many LLM and search calls. For smoke tests:

- STORM Wiki: lower `--max-conv-turn`, `--max-perspective`, `--max-search-queries-per-turn`, `--search-top-k`, `--retrieve-top-k`, and `--max-thread-num`.
- Co-STORM: lower `--warmstart-max-thread`, `--warmstart-max-num-experts`, `--warmstart-max-turn-per-experts`, `--max-search-thread`, `--retrieve-top-k`, `--max-search-queries`, and `--observe-turns`.
- VectorRM: validate CSV first, index a tiny fixture first, and use CPU before trying CUDA/MPS.

If a provider returns quota, overloaded, or capacity errors, do not treat it as a skill failure. Reduce concurrency, wait for cooldown, or switch providers.

## Output and resume issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| STORM resume run says files are missing | Skipped an earlier stage without existing `conversation_log.json`, `storm_gen_outline.txt`, `storm_gen_article.txt`, or `url_to_info.json`. | Use the STORM helper's dry-run to inspect resume prerequisites, or rerun the missing stage. |
| Output directory is empty after a failed full run | Provider errors can be swallowed by `LoggingWrapper` or happen before post-run writing. | Inspect stderr and any partial `log.json`; repeat with smaller turn/search settings. |
| Co-STORM `report.md` is empty | The knowledge base has no useful section nodes or cited information after warm start/turns. | Ensure warm start completed, use at least one useful observed/generated turn, call `knowledge_base.reorganize()`, and inspect `instance_dump.json`. |
| `instance_dump.json` may contain model kwargs | `CollaborativeStormLMConfigs.to_dict()` serializes LM wrapper kwargs. | Use the bundled Co-STORM helper, which redacts secret-looking fields, or redact before sharing. |

## Workflow-specific next references

- STORM stage/resume/callback/output details: `sub-skills/storm-wiki/references/troubleshooting.md`.
- CSV/Qdrant/VectorRM/data-format details: `sub-skills/vector-corpus/references/troubleshooting.md`.
- Co-STORM `step()`, `from_dict`, logging, warm-start, and mind-map details: `sub-skills/co-storm/references/troubleshooting.md`.
