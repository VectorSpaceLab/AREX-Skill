# STORM Wiki Workflows

These workflows assume the public `knowledge-storm` package is installed in the active Python environment. They do not require the source checkout.

## 1. Preflight a run without network or LLM calls

From the sub-skill directory, or by resolving this bundled script from the loaded skill:

```bash
python scripts/run_storm_wiki.py --help

python scripts/run_storm_wiki.py \
  --dry-run \
  --topic "The history of retrieval-augmented generation" \
  --output-dir ./storm-results \
  --retriever bing \
  --cheap-model openai/gpt-4o-mini \
  --strong-model openai/gpt-4o \
  --max-thread-num 2
```

`--dry-run` prints a JSON plan with:

- the sanitized topic directory that STORM will use;
- selected stage flags;
- model component mapping;
- retriever credential requirements;
- prerequisite files needed when resuming later stages;
- expected output files.

It does not instantiate the runner, call a language model, query a retriever, or create article outputs.

## 2. Full internet-search article run

Set model and retriever credentials first. Example with OpenAI-compatible LiteLLM model strings and Bing:

```bash
export OPENAI_API_KEY="..."
export BING_SEARCH_API_KEY="..."

python scripts/run_storm_wiki.py \
  --topic "The history of retrieval-augmented generation" \
  --output-dir ./storm-results \
  --retriever bing \
  --cheap-model openai/gpt-4o-mini \
  --strong-model openai/gpt-4o \
  --max-conv-turn 3 \
  --max-perspective 3 \
  --max-search-queries-per-turn 3 \
  --search-top-k 3 \
  --retrieve-top-k 3 \
  --max-thread-num 2 \
  --verbose-callbacks
```

The helper enables all four stages by default:

- `do_research=True`
- `do_generate_outline=True`
- `do_generate_article=True`
- `do_polish_article=True`

It calls `runner.post_run()` and `runner.summary()` after `runner.run(...)` unless the run fails.

## 3. Stage-only and resume workflows

STORM stores files under:

```text
<output-dir>/<topic-with-spaces-and-slashes-replaced-by-underscores>/
```

The topic directory is truncated to 125 characters by the package. Reuse the same `--topic` and `--output-dir` when resuming.

### Research and outline only

Use this when you want to inspect the research log and outline before spending article-generation tokens:

```bash
python scripts/run_storm_wiki.py \
  --topic "Your topic" \
  --output-dir ./storm-results \
  --retriever you \
  --skip-generate-article \
  --skip-polish-article
```

Expected files:

- `conversation_log.json`
- `raw_search_results.json`
- `direct_gen_outline.txt`
- `storm_gen_outline.txt`
- `run_config.json`
- `llm_call_history.jsonl`

### Generate article from existing research and outline

Use this when `conversation_log.json` and `storm_gen_outline.txt` already exist:

```bash
python scripts/run_storm_wiki.py \
  --topic "Your topic" \
  --output-dir ./storm-results \
  --retriever you \
  --skip-research \
  --skip-generate-outline \
  --do-generate-article \
  --do-polish-article
```

The runner loads `conversation_log.json` when research is skipped and loads `storm_gen_outline.txt` when outline generation is skipped.

### Polish only

Use this when `storm_gen_article.txt` and `url_to_info.json` already exist:

```bash
python scripts/run_storm_wiki.py \
  --topic "Your topic" \
  --output-dir ./storm-results \
  --retriever duckduckgo \
  --skip-research \
  --skip-generate-outline \
  --skip-generate-article \
  --do-polish-article \
  --remove-duplicate
```

`--remove-duplicate` adds an extra polishing pass over the whole page. It can improve repeated content but costs more tokens and can alter section wording.

## 4. Ground-truth exclusion for evaluation

When evaluating against a known article URL, exclude it from retrieval to avoid leakage:

```bash
python scripts/run_storm_wiki.py \
  --topic "Your topic" \
  --output-dir ./storm-results \
  --retriever bing \
  --ground-truth-url "https://example.org/reference-article"
```

The URL is passed to `STORMWikiRunner.run(..., ground_truth_url=...)` and is excluded from search results during research.

## 5. Output validation checklist

After a successful full run, check the topic output directory for these files:

| File | Produced by | Validation use |
| --- | --- | --- |
| `conversation_log.json` | research | Persona perspectives, dialogue turns, generated search queries, and retrieved result snapshots. Required for outline/article resume. |
| `raw_search_results.json` | research | URL-keyed retrieved information before article citation pruning. Use it to verify the retriever returned useful sources. |
| `direct_gen_outline.txt` | outline | Draft outline from parametric LM knowledge only. Useful for comparing the refined outline. |
| `storm_gen_outline.txt` | outline | Refined outline grounded in the conversation log. Required for article resume. |
| `url_to_info.json` | article | Citation index mapping and source metadata used by the article. Required for polish-only resume. |
| `storm_gen_article.txt` | article | Draft article with markdown headings and inline citation indices. |
| `storm_gen_article_polished.txt` | polish | Polished article with a generated summary/lead section and optional duplicate removal. |
| `run_config.json` | `post_run()` | Model kwargs for each STORM component, with call kwargs centralized here. |
| `llm_call_history.jsonl` | `post_run()` | One JSON record per recorded LLM call after kwargs are stripped from each call record. |

If `run_config.json` or `llm_call_history.jsonl` is missing after successful generation, `post_run()` was not called.

## 6. Callback progress reporting

The bundled helper supports `--verbose-callbacks`, which prints high-level progress for perspective identification, information gathering, outline generation, and dialogue turns.

For custom Python applications, subclass `BaseCallbackHandler` and pass an instance to `runner.run(..., callback_handler=handler)`. Use callbacks for UI status, logs, or progress bars; do not mutate runner state inside callbacks unless you own the application lifecycle.

## 7. Cost and rate-limit controls

Start conservatively for new credentials:

```bash
--max-thread-num 1 --max-perspective 2 --max-conv-turn 2 --search-top-k 2
```

Increase only after successful runs. Research load scales roughly with:

```text
max_perspective × max_conv_turn × max_search_queries_per_turn
```

Article generation also uses threads across first-level outline sections. If you see 429/rate-limit errors, lower `--max-thread-num` first, then reduce perspectives, turns, or top-k values.
