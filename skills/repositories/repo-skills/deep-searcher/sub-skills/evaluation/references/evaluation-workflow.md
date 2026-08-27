# DeepSearcher evaluation workflow

This reference distills the DeepSearcher retrieval-evaluation workflow into a self-contained operating procedure. The implemented benchmark path evaluates 2WikiMultiHopQA-style multi-hop questions by retrieving document titles and scoring whether supporting article titles appear in the top results.

## What the benchmark compares

For each question sample:

1. DeepSearcher retrieval calls `retrieve(question, max_iter=<max_iter>)` and reads `metadata["title"]` from each returned result.
2. The naive baseline calls `naive_retrieve(question)` and also reads `metadata["title"]`.
3. The ground truth title set is built from the first element of each pair in `supporting_facts`.
4. Recall@2 and Recall@5 are calculated as the fraction of gold titles found in the first 2 or 5 retrieved titles.

The benchmark measures retrieval title coverage, not final-answer exact match. `query()` answer generation is not part of the standard recall loop.

## Required parameters

| Parameter | Required? | Meaning | Safe default / caution |
| --- | --- | --- | --- |
| `dataset` | Yes | Dataset name. The supported built-in branch is `2wikimultihopqa`. | Use exactly `2wikimultihopqa` unless you have adapted both data files and scorer logic. |
| `config_yaml` | Yes | YAML configuration loaded by `Configuration(config_path=...)` before providers are initialized. | Use a benchmark-specific file. Keep secrets in environment variables where possible. |
| `pre_num` | Yes | Number of question samples to evaluate from the start of the question list. A falsey value in the runner means all samples. | Start with 1-5. Larger values consume more time and tokens. |
| `max_iter` | Yes | Retrieval/reflection iteration cap passed to DeepSearcher retrieval; overrides `query_settings.max_iter` for the benchmark call. | Start at 1-3 for smoke tests. Higher values generally cost more tokens and may improve multi-hop recall. |
| `output_dir` | Yes | Root directory for benchmark output. | Use a dedicated directory outside source-controlled runtime skill content. |
| `skip_load` | Optional flag | Skip corpus indexing and use an existing compatible vector collection. | Only use after a successful corpus load with the same embedding/vector DB/corpus. |
| `flag` | Optional | Subdirectory name under `output_dir` for this run's report files. | Use descriptive labels such as `openai_o1mini_iter3_sample5`. |

## Configuration expectations

The benchmark configuration has the same top-level shape as DeepSearcher configuration:

```yaml
provide_settings:
  llm:
    provider: "OpenAI"
    config:
      model: "o1-mini"
  embedding:
    provider: "OpenAIEmbedding"
    config:
      model: "text-embedding-ada-002"
  file_loader:
    provider: "JsonFileLoader"
    config:
      text_key: "text"
  web_crawler:
    provider: "FireCrawlCrawler"
    config: {}
  vector_db:
    provider: "Milvus"
    config:
      default_collection: "deepsearcher"
      uri: "./milvus.db"
      token: "root:Milvus"
      db: "default"
query_settings:
  max_iter: 3
load_settings:
  chunk_size: 1500
  chunk_overlap: 100
```

For the standard corpus JSON, `file_loader.provider` should be `JsonFileLoader` and `file_loader.config.text_key` should be `text`; otherwise the loader may fail or embed the wrong field. Provider names, optional SDKs, credentials, and vector DB selection are handled by the provider-configuration sub-skill.

## Safe preflight sequence

1. Place or generate the two dataset files:
   - `2wikimultihopqa_corpus.json`
   - `2wikimultihopqa.json`
2. Run `scripts/check_evaluation_inputs.py` against those files and `config_yaml`. This only parses local JSON/YAML and previews output behavior.
3. Confirm credential and service readiness separately:
   - LLM provider credentials for DeepSearcher retrieval.
   - Embedding provider credentials or local embedding dependencies.
   - Vector DB availability and correct collection target.
4. Choose a unique working directory or explicit vector DB URI for local Milvus Lite. The default `./milvus.db` is relative to the process current directory and can lock if reused concurrently.
5. Run a tiny sample (`pre_num` 1-5). Inspect `details.csv`, `statistics.json`, errors, and token usage before scaling.

## First run versus resumed run

### First run

Do not set `skip_load` when the vector collection is empty or uncertain. The benchmark loads the corpus file with:

- `force_new_collection=True`
- `chunk_size=999999`
- `chunk_overlap=0`

The large chunk size is intentional because the corpus is already passage-sized. `force_new_collection=True` can drop/replace the target collection. Use a dedicated collection or vector DB path for evaluations.

### Resume after interruption

The runner writes one row at a time to `details.csv`. If `details.csv` already exists, it resumes at `start_index = len(existing_df)`. If `statistics.json` exists, it loads prior DeepSearcher token usage, error count, and sample count, then recalculates aggregate recall as new rows are appended.

To resume safely:

1. Keep `output_dir/<flag>/details.csv` and `output_dir/<flag>/statistics.json` together.
2. Reuse the same `dataset`, `config_yaml`, embedding model/dimension, vector DB URI, collection name, corpus file, `max_iter`, and `flag` unless you intentionally want a mixed report.
3. Use `--skip_load` only if the corpus collection is already loaded and compatible.
4. Set `pre_num` to the desired final sample count, not the additional count. For example, if 12 rows already exist and you want 30 total rows, run with `--pre_num 30`; the loop resumes from index 12.
5. If the previous run stopped during corpus loading before any report row was produced, do not use `--skip_load` unless you independently verified that the collection is complete.

## Output files

Files are written under `output_dir/<flag>/`.

### `details.csv`

Each appended row contains:

- `idx`: zero-based question index.
- `question`: input question text.
- `recall`: DeepSearcher recall dictionary for `2` and `5`.
- `recall_naive`: naive-RAG recall dictionary for `2` and `5`.
- `gold_titles`: title list from supporting facts.
- `retrieved_titles`: DeepSearcher title list from result metadata.
- `retrieved_titles_naive`: naive-RAG title list.

Recall dictionaries may appear as stringified dicts when reloaded from CSV. Parse carefully if post-processing.

### `statistics.json`

The aggregate JSON contains:

- `deepsearcher.average_recall`: Recall@2 and Recall@5 means over processed rows.
- `deepsearcher.token_usage`: cumulative token count reported by DeepSearcher retrieval.
- `deepsearcher.error_num`: count of retrieval calls that produced no results after retries.
- `deepsearcher.sample_num`: number of DeepSearcher samples counted in statistics.
- `deepsearcher.token_usage_per_sample`: cumulative token usage divided by sample count.
- `naive_rag.average_recall`: naive baseline Recall@2 and Recall@5 means.

## Cost and reproducibility notes

- Full evaluation is optional, credentialed, network/provider-bound, and potentially expensive.
- `pre_num` controls sample count. `max_iter` controls DeepSearcher retrieval-loop depth and is a major token/time lever.
- Provider behavior and LLM instruction following affect parse failures and recall. Record provider, model, embedding model, vector DB, corpus version, `max_iter`, and sample count with every result.
- Do not compare runs if one used a different corpus, collection, embedding model/dimension, or resume state.
- Naive RAG retrieval in the public API accepts `collection` and `top_k` parameters, but the current implementation delegates to the configured naive agent and may not honor those function arguments directly. Treat the benchmark's naive baseline as the package's default configured naive retrieval.
