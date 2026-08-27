---
name: extraction
description: "Build robust LangExtract extraction pipelines with examples,
  schemas, prompt validation, resolver tuning, chunking, and tokenizers."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# LangExtract Extraction

Use this sub-skill when the task is to design, write, review, or debug calls to
`lx.extract()` and the core data objects that make extraction reliable and
source-grounded.

## Load first

- Read [references/workflows.md](references/workflows.md) for extraction input
  shapes, prompt/example contracts, output schemas, validation, resolver
  parameters, tokenizers, and result handling.
- Read [references/troubleshooting.md](references/troubleshooting.md) when an
  extraction call fails, returns ungrounded spans, has schema/fence conflicts,
  or behaves poorly on long or non-spaced-language documents.
- Use [scripts/basic_extraction.py](scripts/basic_extraction.py) as a safe
  starter script for example-based extraction.
- Use [scripts/output_schema_extraction.py](scripts/output_schema_extraction.py)
  as a safe starter script for schema-constrained extraction.

## Best-fit tasks

- Create basic or relationship extraction prompts with `lx.data.ExampleData`
  and `lx.data.Extraction`.
- Choose between plain text input, trusted URL string input with `fetch_urls`,
  and iterable `lx.data.Document` inputs.
- Tune long-document parameters such as `max_char_buffer`, `batch_length`,
  `max_workers`, `extraction_passes`, and `context_window_chars`.
- Use `lx.schema.extraction_item_schema()` and
  `lx.schema.extractions_schema()` with `output_schema`.
- Enforce prompt/example quality with `PromptValidationLevel` and
  `prompt_validation_strict`.
- Tune resolver alignment and parsing through `resolver_params`.
- Select `RegexTokenizer` versus `UnicodeTokenizer` and filter grounded
  `AnnotatedDocument` results by `char_interval` and `AlignmentStatus`.

## Route elsewhere

- Provider credentials, model routing, Gemini/OpenAI/Ollama/Vertex settings,
  provider kwargs, and batch APIs belong in [providers](../providers/SKILL.md).
- JSONL save/load and HTML visualization belong in
  [visualization](../visualization/SKILL.md).
- Custom provider package authoring belongs in
  [provider-plugins](../provider-plugins/SKILL.md).

## Operating checklist

1. Define the extraction classes and attributes before writing examples.
2. Make every example `extraction_text` a verbatim substring of the example
   text and keep extractions in source order.
3. Add examples unless an explicit `output_schema` is present; examples are
   still useful with schemas because they teach the prompt.
4. Validate examples in development with `PromptValidationLevel.ERROR` and
   `prompt_validation_strict=True`.
5. For long documents, start with small samples and scale `max_char_buffer`,
   `batch_length`, `max_workers`, and `extraction_passes` deliberately.
6. Treat `char_interval is None` as ungrounded output until diagnosed or
   intentionally filtered out.
