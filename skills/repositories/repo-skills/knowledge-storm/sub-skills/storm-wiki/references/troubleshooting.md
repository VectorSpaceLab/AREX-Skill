# STORM Wiki Troubleshooting

## Fast triage

1. Run the bundled helper with `--dry-run` and the same topic/output/retriever/model options.
2. Check missing model/retriever credentials reported by the dry-run.
3. Check the sanitized topic output directory for prerequisite files when resuming.
4. Reduce `--max-thread-num` to `1` before debugging rate limits.
5. Inspect `raw_search_results.json` before blaming article generation quality.

## Symptoms and fixes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: knowledge_storm` | Public package is not installed in the active Python environment. | Run `pip install knowledge-storm` in the environment that executes the helper or your Python app. |
| `ModuleNotFoundError: dspy` or another runtime dependency | Incomplete package install or wrong environment. | Reinstall/upgrade `knowledge-storm`; ensure the command uses the same Python environment where it was installed. |
| `File not found: secrets.toml` printed by old helper code | A helper attempted to load a local TOML file, but no file was present. | Prefer environment variables. With the bundled helper, pass `--secrets-file /path/to/secrets.toml` only if you intentionally use TOML. |
| Dry-run reports missing model credentials | Selected LiteLLM provider has no API key in environment. | For default models set `OPENAI_API_KEY`. For Azure set `AZURE_API_KEY` or `OPENAI_API_KEY`, plus `AZURE_API_BASE` and `AZURE_API_VERSION`; or pass `--api-key-env`, `--api-base`, `--api-version`. |
| `You must supply ydc_api_key...` | `YouRM` has no You.com key. | Set `YDC_API_KEY` or pass `ydc_api_key` in Python. |
| `You must supply bing_search_subscription_key...` | `BingSearch` has no Bing key. | Set `BING_SEARCH_API_KEY` or use `bing_search_api_key=...` in Python. |
| `You must supply brave_search_api_key...` | `BraveRM` has no Brave key. | Set `BRAVE_API_KEY`. |
| `You must supply a serper_search_api_key...` | `SerperRM` has no Serper key. | Set `SERPER_API_KEY`. |
| `You must supply tavily_search_api_key...` | `TavilySearchRM` has no Tavily key. | Set `TAVILY_API_KEY`. |
| `You must supply searxng_api_url` | `SearXNG` has no endpoint URL. | Set `SEARXNG_API_URL` or pass `--searxng-api-url`. `SEARXNG_API_KEY` is optional and only needed for protected endpoints. |
| `You must supply azure_ai_search_*...` | `AzureAISearch` lacks key, URL, or index name. | Set `AZURE_AI_SEARCH_API_KEY`, `AZURE_AI_SEARCH_URL`, and `AZURE_AI_SEARCH_INDEX_NAME`, or pass the matching helper flags. |
| `ImportError: Duckduckgo requires pip install duckduckgo_search` | Optional DuckDuckGo package missing. | `pip install duckduckgo_search`. |
| `ImportError: Tavily requires pip install tavily-python` | Optional Tavily package missing. | `pip install tavily-python`. |
| `ImportError: AzureAISearch requires pip install azure-search-documents` | Optional Azure Search package missing. | `pip install azure-search-documents`. |
| 429, quota, `Exceed rate limit`, provider backoff loops, or stalled threads | Too much concurrency or provider quota too low. | Retry with `--max-thread-num 1`, then lower `--max-perspective`, `--max-conv-turn`, `--max-search-queries-per-turn`, and `--search-top-k`. Use cheaper models for research components. |
| `No action is specified...` | All stage flags are false. | Enable at least one stage. The helper defaults all stages on; if using skip flags, leave one `--do-*` stage enabled. |
| `conversation_log.json not exists...` | You skipped research but the topic output directory does not contain research output. | Rerun with `--do-research`, or correct `--topic`/`--output-dir` to match the previous run. |
| `storm_gen_outline.txt not exists...` | You skipped outline generation but no refined outline exists. | Rerun with `--do-generate-outline`, or restore `storm_gen_outline.txt` into the topic directory. |
| `storm_gen_article.txt not exists...` or `url_to_info.json not exists...` | You skipped article generation but polish needs the draft article and citation map. | Rerun with `--do-generate-article`, then polish. |
| Output appears under an unexpected folder | STORM replaces spaces and `/` with `_`, then truncates topic directory names to 125 characters. | Use the same exact `--topic` and `--output-dir` for resume. Check the dry-run `article_output_dir`. |
| Topic is empty or resolves poorly | Blank topic or topic consists only of path-like separators/spaces. | Provide a natural-language topic. Avoid `/`; the runner will replace it with `_`. |
| `run_config.json` or `llm_call_history.jsonl` missing after successful stages | `post_run()` was not called. | Call `runner.post_run()` after `runner.run(...)`. The bundled helper does this by default. |
| `llm_call_history.jsonl` contains little or no data | No LLM calls were made, calls failed before history was recorded, or cache/history was reset. | Confirm enabled stages and inspect `runner.summary()` output. Rerun a small stage if needed. |
| `raw_search_results.json` is empty | Retriever key invalid, endpoint unreachable, public search blocked, or query/topic too narrow. | Validate the retriever with a one-query provider call, switch retriever, reduce threads, or broaden the topic. |
| Article has weak citations or repeated facts | Retriever returned thin snippets, `retrieve_top_k` too low, outline sections overlap, or duplicate removal was off. | Inspect `raw_search_results.json` and `url_to_info.json`; increase `search_top_k`/`retrieve_top_k`; try `--remove-duplicate` during polish. |
| Deprecated wrapper examples fail or behave differently | Older examples used `OpenAIModel`/`AzureOpenAIModel`, which are legacy compatibility wrappers. | Use `LitellmModel` with explicit provider model strings and kwargs. |
| `TypeError` or ignored key when constructing `BingSearch` | Wrong constructor keyword. | Use `bing_search_api_key=...` or set `BING_SEARCH_API_KEY`. |
| `AzureAISearch` returns missing-field errors | Azure index documents do not have the fields expected by the retriever. | Ensure results expose `metadata_storage_path`, `title`, and `chunk`, or adapt a custom retriever. |
| `SearXNG` returns HTML or parsing errors | Endpoint is not returning JSON. | Use a SearXNG search endpoint that supports `format=json`; verify the URL in a browser or curl before STORM. |
| Callback output is silent | No callback handler was passed, or subclass method names do not match hook names. | Pass `callback_handler=YourHandler()` to `runner.run(...)`; confirm methods such as `on_dialogue_turn_end`. |
| `disable_perspective=True` seems ignored | The current high-level runner path exposes the dataclass field but calls the research module with perspective discovery enabled. | Use `max_perspective=1` for a lighter run, or write a custom module call if you must disable perspective-guided research completely. |

## Credential names by retriever

```text
bing             BING_SEARCH_API_KEY
you              YDC_API_KEY
brave            BRAVE_API_KEY
serper           SERPER_API_KEY
duckduckgo       no API key, optional package required
tavily           TAVILY_API_KEY
searxng          SEARXNG_API_URL, optional SEARXNG_API_KEY
azure_ai_search  AZURE_AI_SEARCH_API_KEY, AZURE_AI_SEARCH_URL, AZURE_AI_SEARCH_INDEX_NAME
```

## Stage resume prerequisites

| Desired stage | You may skip | Required files already present |
| --- | --- | --- |
| Outline only | research | `conversation_log.json` |
| Article only | research + outline | `conversation_log.json`, `storm_gen_outline.txt` |
| Polish only | research + outline + article | `storm_gen_article.txt`, `url_to_info.json` |

The runner does not use `raw_search_results.json` for resume, but keep it for audit/debugging.

## Safe retry recipe after a failed run

1. Keep the same topic and output directory.
2. Run `--dry-run` and confirm the article output directory.
3. If research files are complete but article files are missing, resume with `--skip-research --skip-generate-outline`.
4. If outline is missing or corrupt, rerun `--do-generate-outline` from existing research.
5. If `conversation_log.json` is missing or corrupt, rerun research.
6. If rate limits caused the failure, reduce `--max-thread-num` before retrying.
