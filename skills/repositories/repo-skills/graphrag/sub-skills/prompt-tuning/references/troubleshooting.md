# Prompt Tuning Troubleshooting

## Config and Model Creation Failures

Symptoms:

- `load_config` fails before generation.
- The prompt-tuning completion model cannot be created.
- Embedding model creation fails while loading chunks.

Checks:

- Confirm the project has a valid GraphRAG config and initialized prompts/config structure.
- Verify the default completion model config exists; prompt tuning currently uses the default completion model for its LLM calls.
- Verify the embedding model config used by `embed_text` exists because chunk selection uses the embedding tokenizer and `auto` selection performs embeddings.
- Use explicit `--domain` and `--language` to reduce extra LLM calls when debugging model access.

## Input Reader and Storage Failures

Symptoms:

- Prompt tuning starts but fails while reading files.
- No chunks are generated.
- Storage or input-reader plugin errors appear before LLM calls.

Checks:

- Route workspace setup and input path diagnosis to the configuration/data sub-skill.
- Confirm the configured input storage and input reader can read the corpus.
- Check chunking settings. Very small or malformed inputs can produce too few chunks for requested `limit` or `k`.

## Empty or Too-Small Chunks

Symptoms:

- `random` sampling errors because the requested `limit` exceeds actual chunks.
- Generated prompts have weak or generic examples.
- Logs warn that `limit` is out of range and the default is being used.

Checks:

- Lower `--limit`, increase input corpus size, or switch to `--selection-method all` only for tiny corpora.
- Increase `--chunk-size` if chunks are too fragmented.
- Prefer explicit `--domain` and `--language` when the sample is too small for reliable inference.

## Invalid `k`, `limit`, or Selection Behavior

- `limit <= 0` or `limit > chunk_count` is replaced with the default limit for relevant selection methods.
- `--selection-method auto` requires `k > 0`; invalid `k` raises `ValueError`.
- `auto` embeds up to `n_subset_max` sampled chunks and picks the `k` nearest to the embedding centroid. Use smaller `k` for concise examples and larger `n_subset_max` for broader representative sampling.

## LLM and JSON Parsing Failures

Symptoms:

- Domain, language, entity-type, or example generation fails.
- Entity type discovery returns malformed JSON or unusable output.

Checks:

- Retry with `--no-discover-entity-types` to use untyped extraction templates.
- Provide `--domain` and `--language` explicitly to bypass inference calls.
- Use a smaller `--limit` or more focused corpus sample if the LLM is overwhelmed by mixed topics.
- Inspect `prompt-tuning.log` for the generation step that failed.

## Token-Budget Truncation

Symptoms:

- Fewer few-shot examples appear than expected.
- The extraction prompt looks shorter than the sampled corpus would imply.

Checks:

- Increase `--max-tokens` if the target model supports longer prompts.
- Lower `--min-examples-required` only if fewer required examples is acceptable.
- Reduce example verbosity by using smaller chunks or a more focused sample.

## Brace Escaping

GraphRAG escapes braces in source chunks before formatting generated examples. If manually editing prompts, keep GraphRAG placeholders as single braces and escape literal braces as double braces.

Examples:

- Keep `{input_text}` as-is.
- Write literal JSON examples like `{{"field": "value"}}` inside a template.
- Check brace-heavy Markdown, JSON, or LaTeX with the bundled validator.

## Multilingual Guidance

- Use `--language <target>` when the desired prompt/output language is known.
- If corpus language and output language differ, expect the LLM guidance to include translation-oriented instructions.
- For mixed-language corpora, provide a domain and language explicitly; auto language detection may overfit to the sampled chunks.

## Community Report Filename Drift

The live CLI writes `community_report_graph.txt`. If older docs or snippets say `community_report.txt`, update config to point at `community_report_graph.txt` for the current output contract.
