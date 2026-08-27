# Prompt Template Outputs

## Live Output Filenames

The current prompt-tune CLI writes exactly three files:

| File | Config field | Purpose |
| --- | --- | --- |
| `extract_graph.txt` | `extract_graph.prompt` | Entity and relationship extraction instructions, examples, delimiters, and entity-type guidance. |
| `summarize_descriptions.txt` | `summarize_descriptions.prompt` | Summarizes lists of entity or relationship descriptions. |
| `community_report_graph.txt` | `community_reports.prompt` | Generates community report summaries from graph context. |

Use this config mapping after prompt tuning:

```yaml
extract_graph:
  prompt: "prompts/extract_graph.txt"
summarize_descriptions:
  prompt: "prompts/summarize_descriptions.txt"
community_reports:
  prompt: "prompts/community_report_graph.txt"
```

Some documentation examples may mention `community_report.txt`. Treat that as stale for the installed package contract when the live generator writes `community_report_graph.txt`.

## Manual Placeholder Contract

Manual prompt files are plaintext templates. Preserve the placeholders that the indexer injects at runtime.

Entity/relationship extraction prompt placeholders:

- `{input_text}`
- `{entity_types}` when using typed extraction
- `{tuple_delimiter}`
- `{record_delimiter}`
- `{completion_delimiter}`

Entity/relationship description summarization placeholders:

- `{entity_name}`
- `{description_list}`

Community report summarization placeholders:

- `{input_text}`

## Generated Prompt Characteristics

Auto prompt tuning produces indexing prompts, not query prompts. The generated content can include:

- Domain-specific role/persona language.
- Language guidance for extraction and summaries.
- Entity type lists when discovery is enabled.
- Few-shot entity/relationship examples selected from sampled chunks.
- Community report rating and reporter-role guidance.

`max_tokens` applies to the entity extraction prompt construction. The generator includes at least `min_examples_required` examples, then stops adding examples when the token budget is exhausted.

## Brace Handling

The input loader escapes braces in source chunks by replacing `{` with `{{` and `}` with `}}` before those chunks are inserted into generated examples. This protects Markdown, JSON, and LaTeX from `str.format` errors during generation.

When manually editing final prompt templates:

- Keep GraphRAG runtime placeholders as single braces, such as `{input_text}`.
- Escape literal braces that are not GraphRAG placeholders as `{{` and `}}`.
- Be especially careful with JSON examples, Markdown tables containing braces, and LaTeX notation.

## Output Validation

The bundled script validates the output contract without importing GraphRAG:

```bash
python sub-skills/prompt-tuning/scripts/validate_prompt_tune_contract.py prompts --check-placeholders
```

Use it after CLI runs or after writing API-returned prompts to disk.
