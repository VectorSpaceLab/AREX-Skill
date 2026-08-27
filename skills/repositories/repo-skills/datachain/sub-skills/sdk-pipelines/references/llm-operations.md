# LLM Operations

`datachain.llm` provides row-wise model-call specs that plug into `.map()` and
`.gen()`. They behave like typed, cacheable UDFs: each row may call a provider
model, output becomes a DataChain signal, and saved datasets preserve results for
reuse.

## Functions

```python
from datachain import llm

llm.complete(col, prompt=None, *, schema=None, context=None, type=None,
             llm=None, retries=1, fallback=None, include_usage=False, **params)
llm.classify(col, into, prompt=None, *, context=None, type=None,
             llm=None, retries=1, fallback=None, include_usage=False, **params)
llm.score(col, prompt=None, *, context=None, type=None, llm=None,
          retries=1, fallback=None, include_usage=False, **params)
llm.embed(col, *, llm=None, retries=1, fallback=None,
          include_usage=False, **params)
```

| Function | Output | Use it for |
| --- | --- | --- |
| `complete` | `str`, a Pydantic model, or a list schema | Generate text, summarize, extract fields, or emit structured results. Use `.gen()` with `schema=list[Model]` to fan out rows. |
| `classify` | `str` | Pick exactly one label from `into=[...]`. Passing a single string to `into` is a config error. |
| `score` | `float` | Numeric scoring against a prompt. |
| `embed` | `list[float]` | Text embeddings; use Query Engine distances later for ranking. |

## Model Selection

Set a default model on the chain:

```python
chain = chain.settings(llm="anthropic/claude-haiku-4-5")
```

A per-call `llm=` argument overrides the chain default. Provider routing is via
LiteLLM, so model strings are provider-prefixed. Credentials should come from the
environment, cloud IAM, or a callable passed through `llm_params`; do not hardcode
secrets in pipeline code.

`retries=` covers transient failures. `fallback=` can name a backup model or list
of models. Output-affecting params are part of the cache key; secret-only params
should be supplied through a callable when possible.

## Input Modalities

The input column type determines how content is sent to the model.

| Column type | Sent as | Notes |
| --- | --- | --- |
| `str` or Pydantic model | text | Models serialize as JSON; a string path is just text, not file contents. |
| `TextFile` | text | Read with `read_storage(..., type="text")`. |
| `ImageFile` or video frame | image | Requires a vision-capable model. |
| raw `File` | text by default | Fails if bytes are not valid text; use `type="image"` or `type="document"` when needed. |
| `bytes` | text unless `type=` overrides | Invalid UTF-8 raises. |
| `AudioFile` / `VideoFile` | not directly supported | Decode, transcribe, or extract frames first. |

Use `type="document"` for PDF-style document inputs when using a document-capable
model. Heavy document processing is often better as a decode/chunk stage followed
by LLM operations over chunks.

## Usage Columns

Pass `include_usage=True` to return a pair `(value, dc.llm.Usage)`. Name both
outputs with multi-output `map` syntax:

```python
import datachain as dc
from datachain import llm

(
    dc.read_storage("s3://tickets/", type="text", anon=True)
    .settings(llm="openai/gpt-5-mini")
    .map(
        llm.classify("file", into=["bug", "billing", "feature"], include_usage=True),
        output={"category": str, "usage": dc.llm.Usage},
    )
    .save("ticket_categories")
)
```

`Usage` has `input_tokens` and `output_tokens`. Aggregate costs with native
operations later:

```python
chain = dc.read_dataset("ticket_categories")
input_tokens = chain.sum("usage.input_tokens")
output_tokens = chain.sum("usage.output_tokens")
```

## Caching and Save Boundaries

LLM outputs are expensive. Save broad, reusable outputs first, then apply
problem-specific filters downstream.

```python
all_scores = (
    dc.read_storage("s3://reviews/", type="text", anon=True)
    .settings(llm="anthropic/claude-haiku-4-5", parallel=8)
    .map(risk=llm.score("file", "refund risk 0..1"))
    .save("review_refund_risk")
)

high_risk = (
    dc.read_dataset("review_refund_risk")
    .filter(dc.C("risk") > 0.8)
    .save("high_refund_risk_reviews")
)
```

This preserves all model calls for future thresholds or tasks.

## Structured Outputs

Use Pydantic schemas for model-validated outputs:

```python
from pydantic import BaseModel
from datachain import llm

class Scene(BaseModel):
    objects: list[str]
    risk: float

chain.map(scene=llm.complete("file", prompt="Describe the scene", schema=Scene))
```

If parsing fails, simplify the schema, use a model with structured-output
support, or handle the error as a row-level failure in a wider pipeline.

## Troubleshooting Signals

- Missing provider credentials: model calls fail before a useful output column is
  created. Keep secrets outside code and confirm the provider prefix.
- Wrong input modality: a path string is sent as text; read the file as a
  `TextFile`/`ImageFile` when the content is required.
- `include_usage=True` without multi-output `output={...}`: name both the value
  and usage columns.
- A hard boolean classification makes re-thresholding impossible. Prefer
  continuous `score` when the user may ask for different cutoffs later.
- Embedding search is two-stage: generate and save embeddings with LLM/UDF code,
  then use Query Engine distances for ranking.
