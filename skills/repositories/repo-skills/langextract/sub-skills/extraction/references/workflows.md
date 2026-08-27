# Extraction Workflows

This reference is the operating detail for `lx.extract()`. The public
`langextract.extract` convenience function forwards to the implementation in
`langextract.extraction`; use the implementation signature below when deciding
which arguments are available.

## 1. Establish the input and output contract

The implementation has this effective signature (defaults shown are part of
the package contract):

```python
langextract.extraction.extract(
    text_or_documents,
    prompt_description=None,
    examples=None,
    model_id="gemini-3.5-flash",
    api_key=None,
    language_model_type=None,      # deprecated; prefer model/config/model_id
    format_type=None,
    max_char_buffer=1000,
    temperature=None,
    fence_output=None,
    use_schema_constraints=True,
    batch_length=10,
    max_workers=10,
    additional_context=None,
    resolver_params=None,
    language_model_params=None,
    debug=False,
    model_url=None,
    extraction_passes=1,
    context_window_chars=None,
    config=None,
    model=None,
    *,
    output_schema=None,
    fetch_urls=False,
    prompt_validation_level=PromptValidationLevel.WARNING,
    prompt_validation_strict=False,
    show_progress=True,
    tokenizer=None,
)
```

`lx.extract()` itself is a thin `*args, **kwargs` wrapper, so examples should
use the public spelling while API reviews can compare behavior with the
implementation signature.

The result shape depends on the input:

- A literal text string produces one `lx.data.AnnotatedDocument`.
- An iterable of `lx.data.Document` objects produces a list of
  `AnnotatedDocument` objects in input order. Preserve unique `document_id`
  values when joining results downstream.
- A string that looks like `http://` or `https://` is still literal text by
  default. Set keyword-only `fetch_urls=True` only when the URL is trusted and
  fetching occurs inside a sandbox or other network boundary. The built-in
  fetch is intentionally not an SSRF defense; see the troubleshooting guide.

Provider selection, credentials, endpoint configuration, and batch APIs are
not extraction concerns. Route those questions to
[providers](../../providers/SKILL.md).

## 2. Build examples that teach the prompt

A reliable extraction request contains a precise prompt and one or more
`lx.data.ExampleData` objects. Each example has source `text` and an ordered
list of `lx.data.Extraction` objects:

```python
import langextract as lx

examples = [
    lx.data.ExampleData(
        text="Aspirin 100mg daily for heart health.",
        extractions=[
            lx.data.Extraction(
                extraction_class="medication",
                extraction_text="Aspirin",
                attributes={"group": "Aspirin"},
            ),
            lx.data.Extraction(
                extraction_class="dosage",
                extraction_text="100mg",
                attributes={"group": "Aspirin"},
            ),
            lx.data.Extraction(
                extraction_class="frequency",
                extraction_text="daily",
                attributes={"group": "Aspirin"},
            ),
        ],
    )
]

result = lx.extract(
    text_or_documents="The patient started Metformin 500mg twice daily.",
    prompt_description=(
        "Extract medication, dosage, and frequency. Use exact source text "
        "and return extractions in order of appearance."
    ),
    examples=examples,
    model_id="<provider-model-id>",
)
```

Prompt rules:

- State exactly what extraction classes are allowed and what each attribute
  means.
- Say explicitly: use exact text from the input for `extraction_text`.
- Require source order when order matters. The default output order is model
  output order; use `extraction_index_suffix` only when the prompt/schema emits
  explicit ordering attributes.
- Say whether overlapping spans are allowed. For most entity pipelines,
  require non-overlapping spans.
- Give attributes stable names and values. An attribute is metadata attached to
  an extraction; it is not a replacement for grounding the extraction text.
- Include a few-shot example for each difficult class, relationship, or
  attribute convention. Keep example classes and attribute names consistent.
- Do not paraphrase in examples. Copy the exact substring, including the
  relevant punctuation or whitespace behavior.

### Basic extraction

Use distinct `extraction_class` values for entity types and put optional
metadata in `attributes`. Inspect `result.extractions`; each item is an
`Extraction` with `extraction_class`, `extraction_text`, optional `attributes`,
and alignment fields.

### Relationship extraction

LangExtract represents relationships as extractions plus shared attributes.
For example, give each medication, dosage, and condition a common
`medication_group` attribute such as `Aspirin`, and state in the prompt that
all members of one group must share the same value. This preserves grounded
spans while making the relationship explicit and easy to group in Python.
Do not assume an attribute value itself has a `char_interval`; only the
extraction's `extraction_text` is aligned to source text.

### Iterable documents

Use `lx.data.Document` when processing multiple independent texts:

```python
documents = [
    lx.data.Document(document_id="note-1", text="Shortness of breath on stairs."),
    lx.data.Document(document_id="note-2", text="Dizziness in the morning."),
]
results = lx.extract(
    documents,
    prompt_description="Extract symptoms in source order.",
    examples=examples,
    model_id="<provider-model-id>",
)
for document in results:
    print(document.document_id, len(document.extractions or []))
```

Each input document should have a unique ID. An iterable is materialized into
an output list, while a single string remains a single annotated result.
`additional_context` can provide shared context; per-document
`Document.additional_context` is preserved unless the call-level value is
used to fill an absent value.

## 3. Long-document controls

LangExtract chunks text before inference and then aligns and merges chunk
results. Start with a short representative text and scale one knob at a time.

| Argument | Operational effect | Trade-off / guidance |
| --- | --- | --- |
| `max_char_buffer` | Approximate maximum characters per inference chunk; sentence and token boundaries are respected where possible. | Smaller buffers can improve local focus but create more requests and more boundary cases. A single oversized token may exceed the buffer. |
| `batch_length` | Number of chunks grouped into a batch. | Larger batches can expose more parallel work and consume more memory. |
| `max_workers` | Maximum concurrent workers used by supported providers. | More workers reduce wall time only when the provider and quota allow it. Keep `batch_length >= max_workers` to avoid an avoidable warning and under-utilization. |
| `extraction_passes` | Reprocesses the full document sequentially and merges non-overlapping results; earlier passes win overlaps. | Improves recall at roughly proportional inference cost. Use `1` first. |
| `context_window_chars` | Adds trailing text from the previous chunk to the current prompt for cross-boundary coreference. | Helps pronouns and continuity but increases prompt size and may add ambiguity. |

A good tuning sequence is: validate one short document, try a moderate
`max_char_buffer`, check grounding and class precision, then increase
`batch_length`/`max_workers` for throughput. Add `extraction_passes` only when
missed entities justify additional cost. Monitor provider quotas and tokens;
parallelism primarily changes latency, while more passes and more chunks change
usage.

## 4. Schema-constrained extraction

`output_schema` is a JSON Schema for LangExtract's raw output envelope. The
supported helper signatures are:

```python
lx.schema.extraction_item_schema(
    extraction_class: str,
    *,
    attributes: Mapping[str, JsonSchema] | None = None,
    additional_properties: bool = False,
) -> dict

lx.schema.extractions_schema(
    item_schema: JsonSchema,
    *additional_item_schemas: JsonSchema,
    additional_properties: bool = False,
) -> dict
```

Build an item schema, then wrap it in the required top-level `extractions`
array. Attribute properties are represented with the reserved
`<extraction_class>_attributes` key:

```python
import langextract as lx

output_schema = lx.schema.extractions_schema(
    lx.schema.extraction_item_schema(
        "condition",
        attributes={
            "status": {
                "type": "string",
                "enum": ["present", "absent"],
            }
        },
    )
)

result = lx.extract(
    text_or_documents="The note mentions hypertension and denies diabetes.",
    prompt_description=(
        "Extract conditions. Use exact text and set status to present or absent."
    ),
    # examples may be omitted because output_schema is present.
    output_schema=output_schema,
    model_id="<gemini-or-openai-model-id>",
    fence_output=False,
)
```

Schema rules:

- Examples are optional when `output_schema` is supplied. If supplied, they
  remain prompt guidance and should use the same classes and attribute names as
  the schema.
- Gemini and supported OpenAI models provide `output_schema` support. Ollama
  does not provide this user-schema path; route model capability checks to
  [providers](../../providers/SKILL.md).
- Keep `format_type` unset or JSON. Do not set `fence_output=True`; schema
  output must be raw JSON, and forced fences fail before inference.
- Do not combine `output_schema` with provider-native schema kwargs such as
  `response_format`, `response_schema`, or `response_json_schema`. Let the
  output schema configure the structured response.
- Keep the default `_attributes` suffix. Custom attribute suffixes are not
  compatible with the schema envelope expected by the resolver.
- The helpers default `additional_properties=False` and make supplied fields
  required. To model an optional value, keep the key required but allow
  `null`, or author a raw schema when omission is truly required.
- Multiple extraction classes are represented by passing additional item
  schemas to `extractions_schema()`; the helper uses `anyOf` for the item
  union.

## 5. Validate prompt examples before paying for inference

`PromptValidationLevel` has exactly these members:

- `OFF`: skip pre-flight example alignment checks.
- `WARNING`: log failed or non-exact alignment and continue. This is the
  default.
- `ERROR`: raise `PromptAlignmentError` for failed alignment; with
  `prompt_validation_strict=True`, fuzzy and lesser matches also fail.

Use strict validation while authoring examples:

```python
from langextract.prompt_validation import PromptValidationLevel

result = lx.extract(
    text_or_documents=text,
    prompt_description=prompt,
    examples=examples,
    model_id="<provider-model-id>",
    prompt_validation_level=PromptValidationLevel.ERROR,
    prompt_validation_strict=True,
)
```

The validator uses the same fuzzy-alignment settings supplied in
`resolver_params` and the same `tokenizer` supplied to extraction. Fix example
text first; use `OFF` only when validation is deliberately handled elsewhere.
For production pipelines, `WARNING` is a useful compatibility setting after
examples have been validated offline.

## 6. Resolver parsing and alignment

Pass resolver controls as a dictionary. The most useful current keys are:

```python
resolver_params={
    "suppress_parse_errors": True,
    "extraction_index_suffix": "_index",
    "enable_fuzzy_alignment": True,
    "fuzzy_alignment_threshold": 0.75,
    "fuzzy_alignment_algorithm": "lcs",
    "fuzzy_alignment_min_density": 1 / 3,
    "accept_match_lesser": True,
}
```

- `suppress_parse_errors=True` skips a malformed chunk with a warning instead
  of aborting the whole document. The chunk's results are lost; use `False`
  while diagnosing provider output.
- `extraction_index_suffix` enables index-based ordering when emitted
  attributes end with that suffix. Without it, resolved items follow model
  output order.
- `enable_fuzzy_alignment` allows fallback matching after exact matching fails.
- `fuzzy_alignment_threshold` is the minimum fraction of extraction tokens that
  must match. Lower it only for small, explainable transcription differences.
- `fuzzy_alignment_algorithm="lcs"` is the current default; `"legacy"` is
  deprecated. `fuzzy_alignment_min_density` rejects sparse matches spread over
  a long span.
- `accept_match_lesser` accepts a partial exact span when the model includes
  extra edge tokens. It is different from fuzzy alignment and should not be
  used as a general recall switch.

Tune one alignment setting at a time and inspect `alignment_status` and
`char_interval` after each change. See
[references/troubleshooting.md](troubleshooting.md) for symptom-driven choices.

## 7. Tokenizers and grounded results

The default is `RegexTokenizer`, a fast choice for spaced English-like text.
For Japanese, Chinese, Korean, Thai, or other non-spaced or grapheme-sensitive
text, pass `UnicodeTokenizer()`:

```python
from langextract.core import tokenizer

result = lx.extract(
    text_or_documents=source_text,
    prompt_description="Extract named entities using exact source text.",
    examples=examples,
    model_id="<provider-model-id>",
    tokenizer=tokenizer.UnicodeTokenizer(),
)
```

`UnicodeTokenizer` preserves indices against the original input and handles
Unicode grapheme clusters, but is slower. Use the same tokenizer during prompt
validation and alignment by passing it to `lx.extract()` rather than manually
mixing tokenizers.

Every `AnnotatedDocument` contains `text` and an `extractions` collection.
Each `Extraction` exposes `extraction_class`, `extraction_text`,
`attributes`, `char_interval`, `token_interval`, and `alignment_status`.
`CharInterval.start_pos` is inclusive and `end_pos` is exclusive. The status
usually identifies exact, greater, lesser, or fuzzy matching.

For downstream highlighting or visualization, keep only extractions with a
valid interval and a status acceptable to the application:

```python
def grounded(extraction):
    interval = extraction.char_interval
    return (
        interval is not None
        and interval.start_pos is not None
        and interval.end_pos is not None
        and interval.start_pos < interval.end_pos
    )

grounded_extractions = [e for e in result.extractions if grounded(e)]
```

`char_interval=None` is not a harmless formatting detail: it means the
returned text could not be located in the source document. Diagnose prompt
verbatimness and resolver settings before treating that extraction as a
source-grounded fact. Route persistence or HTML output to
[visualization](../../visualization/SKILL.md).
