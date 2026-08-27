# Extraction Troubleshooting

Use this guide for failures that arise from `lx.extract()` arguments, prompt
examples, schema envelopes, resolver parsing/alignment, tokenization, chunking,
or result interpretation. Provider credentials, endpoint routing, and live
service limits belong in [providers](../../providers/SKILL.md); JSONL/HTML
output belongs in [visualization](../../visualization/SKILL.md).

## Quick triage

1. Decide whether the failure happened before inference, during provider
   inference, while parsing model output, during alignment, or after result
   handling.
2. Reproduce on a short literal text string before scaling to URLs, iterables,
   or long documents.
3. Turn off avoidable variables: one document, one extraction pass,
   `show_progress=False`, and strict prompt validation while authoring.
4. Inspect `extraction_text`, `attributes`, `char_interval`, and
   `alignment_status` before saving or visualizing results.

## Symptom matrix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError` says examples are required | `examples` is empty and no explicit `output_schema` or preconfigured output-schema model is active. | Add at least one `lx.data.ExampleData` with verbatim `Extraction` objects, or supply `output_schema`. Examples remain recommended even with a schema when prompt behavior is nuanced. |
| `PromptAlignmentError` before inference | An example `extraction_text` is not an exact substring of its own example text, or strict mode treats fuzzy/lesser matches as errors. | Copy exact source substrings into examples; preserve punctuation and spacing. During development use `PromptValidationLevel.ERROR` with `prompt_validation_strict=True`. Relax strictness only after the examples are intentionally validated. |
| Warning-only validation logs alignment issues but extraction continues | Default validation is `WARNING`, so bad examples can still incur provider cost. | Treat warnings as action items. Switch to `PromptValidationLevel.ERROR` in local/staging checks to fail fast. |
| Many `char_interval=None` results | The model paraphrased, returned a normalized value, selected text outside the chunk, or alignment was too strict for small transcription differences. | Strengthen the prompt: "Use exact text from the input." Add examples for the failing class. First inspect whether the extraction text is present in source. If near-matches are valid, lower `fuzzy_alignment_threshold` cautiously; if not, filter ungrounded results. |
| Wrong span matched under fuzzy alignment | Fuzzy threshold is too low, match density is too permissive, or examples allow ambiguous classes. | Raise `fuzzy_alignment_threshold`; raise `fuzzy_alignment_min_density` to reject sparse long-span matches; add disambiguating attributes or examples; do not use fuzzy alignment to compensate for non-verbatim prompts. |
| Partial exact span accepted when the model included extra words | `accept_match_lesser=True` allows `MATCH_LESSER`. | Keep it enabled only when edge-token drift is acceptable. Disable or combine with `prompt_validation_strict=True` when every output must exactly match source text. |
| Parse/schema error for one chunk aborts extraction | `suppress_parse_errors` is false or a low-level call raised while parsing malformed model output. | For production resilience, use `resolver_params={"suppress_parse_errors": True}`. For debugging, set it false so the bad raw shape fails loudly. Suppressed chunks return no partial results. |
| Results appear out of the desired logical order | The model output order differs from source order or explicit index attributes were ignored. | State "return extractions in source order" in the prompt. If the model emits attributes such as `entity_index`, set `resolver_params={"extraction_index_suffix": "_index"}` so those attributes drive ordering. |
| Duplicate or confusing multi-document outputs | Iterable inputs lack stable unique `document_id` values or downstream code assumes a single result. | Pass `lx.data.Document(document_id=..., text=...)` for each input. Expect a list of `AnnotatedDocument` outputs for iterables and a single `AnnotatedDocument` for a text string. |

## Output schema and raw JSON conflicts

`output_schema` is strict about output format because it configures the raw
LangExtract JSON envelope.

| Symptom | Why it happens | Fix |
| --- | --- | --- |
| Error says `output_schema` cannot be used with fences | `fence_output=True` was supplied directly or through conflicting lower-level configuration. | Remove forced fences or set `fence_output=False`. Do not ask the model for fenced JSON when `output_schema` is active. |
| Error says output schema requires JSON | `format_type` was set to YAML or resolver params changed the format handler. | Leave `format_type` unset or set JSON only. Keep the default wrapper key `extractions`. |
| Error mentions provider schema kwargs conflict | Provider kwargs such as `response_format`, `response_schema`, or `response_json_schema` would override the explicit `output_schema`. | Remove provider-native schema kwargs and let `output_schema` configure structured output. Route provider-specific schema capability questions to [providers](../../providers/SKILL.md). |
| The resolver cannot parse attribute objects | A raw schema used generic fields like `extraction_text` or changed the `_attributes` suffix. | Each item must use the extraction class key for text, for example `condition`, and the attributes object key `condition_attributes`. Keep the default `_attributes` suffix unless writing lower-level provider code outside `lx.extract()`. |
| OpenAI strict schema rejects an optional attribute | Every object property must usually be listed in `required`, and helper-supplied attributes are required by design. | Represent optional values as nullable (`anyOf` with `null`) while keeping the key required, or hand-author a provider-compatible raw schema. |
| Model/provider says user schemas are unsupported | The selected backend does not implement `output_schema`. | Use Gemini or a supported OpenAI model for this path, or remove `output_schema` and rely on examples. Route model capability checks to [providers](../../providers/SKILL.md). |

Remember: examples are optional only because `output_schema` supplies the output
envelope. Examples still improve prompt behavior and should mirror the schema's
classes and attribute names.

## Fuzzy alignment tuning

Start from defaults and tune by symptom:

```python
resolver_params = {
    "suppress_parse_errors": True,
    "enable_fuzzy_alignment": True,
    "fuzzy_alignment_threshold": 0.75,
    "fuzzy_alignment_algorithm": "lcs",
    "fuzzy_alignment_min_density": 1 / 3,
    "accept_match_lesser": True,
}
```

- Too many false negatives with minor source variations: lower
  `fuzzy_alignment_threshold` slightly, then inspect a sample of accepted
  spans.
- False positives spanning too much text: raise `fuzzy_alignment_threshold` or
  `fuzzy_alignment_min_density`.
- Slow long-document alignment: keep the current `lcs` algorithm and reduce
  chunk sizes before disabling fuzzy alignment entirely.
- Examples fail only under strict validation: fix example substrings. Do not
  hide example drift by relaxing fuzzy settings unless the drift is
  intentional and documented.
- `accept_match_lesser` is for cases where the returned text contains an exact
  source substring plus extra edge tokens. It is not equivalent to fuzzy
  matching and can be too permissive for legal, medical, or evaluation spans.

## Long documents: cost, latency, and quality

Long-document issues often come from multiplying chunks, workers, and passes.

- `max_char_buffer` too small: more chunks, more inference calls, more boundary
  effects. Increase it when the prompt needs wider context and the provider can
  handle the context reliably.
- `max_char_buffer` too large: less local focus and more long-context
  distraction. Decrease it when the model misses local entities or mixes
  distant facts.
- `extraction_passes > 1`: improves recall by rerunning the full task, but
  each pass reprocesses the document. Treat it as a cost multiplier.
- `batch_length < max_workers`: the package warns that only `batch_length`
  workers can be used. Increase `batch_length` or reduce `max_workers`.
- `max_workers` too high: provider quota, rate limits, or memory may dominate.
  Route service-specific limits to [providers](../../providers/SKILL.md).
- `context_window_chars` too high: more tokens and possible prompt confusion.
  Use only for cross-chunk coreference and verify that new context does not
  create duplicate or misgrounded spans.

A safe escalation path is: one short text, one pass, strict example validation,
inspect grounded spans, then scale buffer/batching, then add more passes only
if recall remains inadequate.

## URL input and SSRF risk

`fetch_urls=False` by default. If you pass a URL-looking string without
`fetch_urls=True`, LangExtract treats the URL as literal text. If you enable
`fetch_urls=True`, the package fetches the URL through a normal HTTP request
without URL allowlisting, host filtering, redirect controls, DNS rebinding
protection, or cloud-metadata blocking.

Use `fetch_urls=True` only when all are true:

- The URL came from a trusted source.
- The process runs in a sandbox or restricted network environment.
- Internal hostnames, loopback addresses, metadata IPs, and redirects are
  already blocked by infrastructure or pre-validation.
- The fetched text size and encoding are bounded before model inference.

For untrusted URLs, fetch content yourself with an allowlist and pass the final
literal text to `lx.extract()`.

## Unicode and non-spaced languages

Symptoms that suggest tokenizer mismatch:

- Japanese, Chinese, Korean, Thai, emoji, or combining marks have incorrect
  offsets.
- `char_interval` boundaries split grapheme clusters or adjacent characters.
- Prompt validation reports non-exact matches even though the visible text
  appears correct.

Use:

```python
from langextract.core import tokenizer

result = lx.extract(
    text_or_documents=text,
    prompt_description=prompt,
    examples=examples,
    model_id="<provider-model-id>",
    tokenizer=tokenizer.UnicodeTokenizer(),
)
```

`UnicodeTokenizer` is slower than the default `RegexTokenizer`, so choose it
for languages or data where Unicode segmentation matters. Pass it directly to
`lx.extract()` so prompt validation, chunking, and alignment use the same
segmentation.

## Grounded result handling

Before using results as source-grounded facts, filter on intervals:

```python
def is_grounded(extraction):
    interval = extraction.char_interval
    return (
        interval is not None
        and interval.start_pos is not None
        and interval.end_pos is not None
        and interval.start_pos < interval.end_pos
    )
```

Then inspect `alignment_status`:

- `MATCH_EXACT`: best for strict span tasks.
- `MATCH_GREATER`: the aligned source span is larger than the returned text.
- `MATCH_LESSER`: only part of the returned text was exactly matched.
- `MATCH_FUZZY`: a fuzzy match was accepted.

Downstream highlighting and HTML visualization should normally exclude
ungrounded extractions. Route save/load and visualization mechanics to
[visualization](../../visualization/SKILL.md).
