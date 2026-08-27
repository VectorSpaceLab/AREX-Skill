# Prompt Tune API and CLI

## When to Use

Use `graphrag prompt-tune` or `generate_indexing_prompts` to generate domain-adapted indexing prompts from a GraphRAG input corpus. This improves the prompts used by graph extraction, description summarization, and community report summarization before an index run.

Prompt tuning is optional, but recommended when a corpus has domain-specific vocabulary, multilingual content, unusual entity types, or a desired analyst persona.

## CLI Contract

The CLI subcommand loads config from `--root`, optionally overrides prompt-tune chunk settings, calls the API, and writes generated prompts to `--output`.

Common options:

| Option | Purpose |
| --- | --- |
| `--root` | Project directory containing GraphRAG config. Defaults to the current directory. |
| `--output` | Directory for generated prompt files. Defaults to `prompts`. |
| `--domain` | Domain hint. If omitted, GraphRAG asks the LLM to infer it from sampled chunks. |
| `--language` | Prompt/output language guidance. If omitted, GraphRAG asks the LLM to detect it. |
| `--selection-method` | One of `random`, `top`, `all`, `auto`. Default is `random`. |
| `--limit` | Number of chunks for `random` or `top`. Default is `15`. |
| `--chunk-size` | Token chunk size used while generating prompt-tune examples. Default is `200`. |
| `--overlap` | Chunk overlap override when exposed by the installed CLI. |
| `--max-tokens` | Token budget for the generated entity extraction prompt. Default is `2000`. |
| `--discover-entity-types` / `--no-discover-entity-types` | Enable or disable LLM-discovered entity types. |
| `--min-examples-required` | Minimum examples included in the extraction prompt before token-budget truncation. Default is `2`. |
| `--n-subset-max` | Number of chunks embedded for `auto` selection. Default is `300`. |
| `--k` | Number of representative chunks selected by `auto`. Default is `15`. |
| `--verbose` | Enables more detailed logging. |

Typical command:

```bash
graphrag prompt-tune --root <project> --output prompts --domain "legal filings" --language English --selection-method random --limit 15
```

## API Contract

`generate_indexing_prompts` is an async API:

```python
async def generate_indexing_prompts(
    config,
    limit=15,
    selection_method="random",
    domain=None,
    language=None,
    max_tokens=2000,
    discover_entity_types=True,
    min_examples_required=2,
    n_subset_max=300,
    k=15,
    verbose=False,
) -> tuple[str, str, str]: ...
```

Return order:

1. Entity/relationship extraction prompt for `extract_graph`.
2. Entity/relationship description summarization prompt for `summarize_descriptions`.
3. Community report summarization prompt for `community_reports`.

The API uses the GraphRAG config to load input documents, chunk them, create embedding/completion models, and generate examples. It does not write files; callers must persist the tuple explicitly if bypassing the CLI.

## Selection Methods

- `random`: samples `limit` chunks with pandas random sampling. Use for normal corpora.
- `top`: uses the first `limit` chunks. Use for deterministic debugging or curated head documents.
- `all`: keeps all chunks. Use only when the corpus is small enough for repeated LLM calls.
- `auto`: embeds up to `n_subset_max` sampled chunks and selects the `k` closest chunks to the embedding centroid. Use for large, imbalanced corpora when representative coverage matters.

If `limit <= 0` or exceeds the chunk count for `top`/`random`, GraphRAG logs a warning and falls back to the default limit. For `auto`, `k` must be greater than zero; invalid `k` raises `ValueError`.

## Generation Sequence

The API performs these steps:

1. Load and chunk input documents using the configured input reader, storage, chunking, and embedding tokenizer.
2. Escape `{` and `}` in chunk text so Markdown, JSON, and LaTeX content does not break Python template formatting.
3. Create the prompt-tuning completion model from the default completion model config.
4. Infer `domain` if not provided.
5. Detect `language` if not provided.
6. Generate persona, community report rating guidance, optional entity types, entity/relationship examples, and community reporter role.
7. Build final prompt templates with token-aware truncation of extraction examples.

## Routing Notes

- For full indexing runs after prompts are generated, use the indexing sub-skill.
- For missing config, invalid input storage, or workspace initialization, use the configuration/data sub-skill first.
- For query prompt customization, do not use this sub-skill except to state that prompt tuning here covers indexing templates only.
