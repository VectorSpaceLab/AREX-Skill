# Evaluation troubleshooting

Use this guide when DeepSearcher retrieval evaluation fails validation, consumes more tokens than expected, cannot resume, or reports suspicious recall values.

## Preflight validation failures

### Unsupported dataset name

Symptom: the validator rejects `dataset` or the runner raises a not-implemented dataset error.

Fix:

- Use `2wikimultihopqa` for the standard scorer.
- For a new dataset, adapt both the ground-truth extraction and Recall@K logic. Do not simply rename files; the standard scorer reads `supporting_facts` title pairs.

### Corpus JSON is not a list of objects

Symptom: validation fails, or loading raises a JSON/list/dictionary error.

Fix:

- Make the corpus a JSON array.
- Each item needs non-empty string `title` and `text` fields.
- For JSONL or another layout, convert to the expected array or use a custom loader and custom benchmark wrapper.

### Questions JSON lacks `question` or `supporting_facts`

Symptom: validation fails, or scoring raises a key/index/type error.

Fix:

- Each sample must have a non-empty `question` string.
- `supporting_facts` must be a non-empty list of two-item pairs such as `["Article title", 0]`.
- The scorer uses only the first element of each pair as the gold title.

### Ground-truth titles are missing from the corpus

Symptom: validation reports missing titles, or recall stays unexpectedly low.

Fix:

- Normalize title spelling, punctuation, Unicode, and whitespace.
- Ensure the corpus file and questions file come from the same dataset build.
- If the mismatch is intentional, document it and expect lower maximum recall.

### YAML sections are missing

Symptom: validator reports absent `provide_settings.llm`, `embedding`, `file_loader`, `web_crawler`, or `vector_db`, or initialization fails with a key error.

Fix:

- Use the full DeepSearcher configuration shape, including `query_settings` and `load_settings`.
- For standard 2Wiki corpus loading, set `file_loader.provider: JsonFileLoader` and `file_loader.config.text_key: text`.
- Route provider names, SDK installation, and credential details to the provider-configuration sub-skill.

## Provider and dependency failures

### Missing provider credentials

Symptom: OpenAI/DeepSeek/other provider errors appear during configuration, embedding, or retrieval.

Fix:

- Confirm the required environment variables or provider config fields outside runtime skill files.
- Run the validator first; then perform a tiny credentialed sample (`pre_num` 1) before larger evaluations.
- Do not put secrets in generated reports or runtime skill files.

### CLI or help fails before argument parsing

Symptom: even a help command or runner import initializes providers and fails on credentials or vector DB readiness.

Fix:

- DeepSearcher initializes providers early in several entry points. Use a benchmark-specific environment and minimal valid provider settings before invoking those entry points.
- For parser-only checks, use dummy credentials only when no API call will be made and isolate the vector DB path. Never use dummy values for real evaluation.

### FireCrawl import error involving `ScrapeOptions`

Symptom: provider initialization fails while importing the web crawler section even though the benchmark does not crawl.

Fix:

- This package version expects a FireCrawl SDK that exports `ScrapeOptions`. In inspection, `firecrawl-py 2.16.5` worked; `firecrawl-py 4.x` may fail for this checkout.
- If the benchmark config initializes `FireCrawlCrawler`, keep the compatible SDK pin or switch to a provider setup known to import in your environment.

### Local Milvus Lite failures

Symptoms:

- Local DB lock or file-access errors.
- Local `./milvus.db` smoke failures after dependency upgrades.
- Collection exists with wrong dimension or stale corpus.

Fix:

- Use a unique working directory or explicit local DB URI per run. The default URI `./milvus.db` is relative to the process current directory.
- Avoid concurrent processes against the same local Milvus Lite file.
- In the verified inspection environment, local Milvus Lite worked with `pymilvus==2.5.8` and `milvus-lite==2.5.1`; newer major versions produced local DB smoke failures.
- If embedding dimension/model changed, reload into a fresh collection rather than using `skip_load`.

## Loading and resume failures

### `skip_load` returns no results

Symptom: all retrievals fail or return no titles after setting `--skip_load`.

Likely causes:

- The collection was never loaded.
- The process current directory changed, so `./milvus.db` points to a different local database.
- Embedding model/dimension or collection name changed.
- The vector DB service was reset or pointed to another database.

Fix:

- Rerun without `skip_load` in a dedicated evaluation collection, accepting that the first-run path replaces that collection.
- If preserving an existing collection matters, configure a separate benchmark collection or vector DB URI first.

### Resume starts at the wrong index

Symptom: the runner prints a start index that does not match the intended sample count.

Fix:

- Resume index is `len(details.csv)`, not a value stored in `statistics.json`.
- Remove or archive a stale `details.csv` if starting a fresh logical run.
- Use a new `flag` for a different model, `max_iter`, corpus, or sample target.
- Set `pre_num` to the final desired total. If `details.csv` already has 10 rows and you run `pre_num=5`, there is nothing new to process.

### Statistics disagree with details

Symptom: `statistics.json` aggregate does not match manually recomputed CSV values.

Fix:

- Preserve `details.csv` and `statistics.json` as a pair.
- If a run was interrupted while writing, recompute statistics from `details.csv` or rerun in a new flag.
- Watch for stringified dictionary keys in CSV (`"2"` vs `2`) when post-processing.
- Avoid manually editing only one output file.

## Recall and result-quality issues

### Recall is zero despite relevant text being present

Likely causes:

- Retrieved result metadata lacks exact `title`.
- Corpus loader did not preserve `title` as metadata because `text_key` or loader provider was wrong.
- Gold titles differ from corpus titles by case, punctuation, whitespace, or Unicode normalization.
- Collection routing selected an empty or unrelated collection.

Fix:

- Validate corpus/questions matching with the helper.
- Confirm the config uses `JsonFileLoader` with `text_key: text` for the standard corpus.
- Inspect a small number of `retrieved_titles` in `details.csv`.
- Route RAG behavior and collection-routing diagnosis to the rag-query sub-skill if retrieval returns unrelated titles.

### DeepSearcher pipeline errors or parse retries

Symptom: repeated messages about parsing LLM output, retries, or no retrieved results.

Fix:

- Reduce `max_iter` and test a tiny sample to isolate whether failures are model-instruction-following or provider errors.
- Try a stronger instruction-following/reasoning model if budget allows.
- Check provider rate limits and transient errors before declaring the result invalid.
- Record `error_num` and inspect affected questions in `details.csv`.

### Token usage too high

Fix:

- Lower `pre_num` for smoke tests.
- Lower `max_iter`; token consumption generally increases with iteration count.
- Use `skip_load` only after a confirmed compatible corpus load to avoid repeated embedding cost.
- Estimate cost from `statistics.json` token usage per sample after a tiny sample before scaling.

## Safety boundaries

- The bundled validator is safe by design: it does not call `load_from_local_files`, `retrieve`, `query`, providers, vector DBs, networks, or credentials.
- Full evaluation is optional and expensive. Treat it as unverified until it actually runs with real credentials and a ready vector DB.
- Keep benchmark outputs and any credentialed logs out of runtime skill files.
