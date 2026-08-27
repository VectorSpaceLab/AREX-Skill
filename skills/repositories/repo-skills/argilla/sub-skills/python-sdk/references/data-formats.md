# Argilla data formats and mappings

Use this reference when incoming data needs to be transformed before logging to Argilla or exported out of Argilla.

## Settings schema rules

- A publishable dataset requires at least one field and one question.
- Names must be unique across fields, questions, metadata properties, and vector fields. A field named `text` and a vector named `text` collide.
- Prefer stable ASCII names such as `review`, `sentiment`, `split`, and `embedding`. Vector names must be URL-safe: letters, numbers, underscore, and hyphen are safe.
- `allow_extra_metadata=True` stores metadata keys that are not defined in settings, but those extra keys are not available for UI filtering/sorting.
- `TaskDistribution(min_submitted=N)` sets how many submitted responses complete a record. Keep `N` no larger than the number of expected annotators.

## Field value formats

| Field class | Record value format |
| --- | --- |
| `TextField` | A string. Set `use_markdown=True` to render Markdown/HTML. |
| `ImageField` | A remote URL string, local image path string available to the logging process, or a PIL image object. |
| `ChatField` | A list of dictionaries with `role` and `content` keys. Roles commonly include `user`, `assistant`, `system`, or `model`; extra keys are ignored with a warning. |
| `CustomField` | A dictionary whose keys match the template references, for example `{{record.fields.profile.name}}`. Prefer inline templates for reproducible scripts; URL/path templates create external runtime dependencies. |

## Question, suggestion, and response value formats

The same value format applies to `rg.Suggestion(question_name=..., value=...)`, `rg.Response(question_name=..., value=..., user_id=...)`, and source columns mapped to that question.

| Question class | Value format |
| --- | --- |
| `LabelQuestion` | One label value, e.g. `"positive"`. Labels can be declared as a list or as `{value: display_text}`. |
| `MultiLabelQuestion` | A list of label values, e.g. `["toxicity", "pii"]`. |
| `RankingQuestion` | A list of option values in ranked order, e.g. `["reply-2", "reply-1", "reply-3"]`. |
| `RatingQuestion` | One integer from the configured `values`, e.g. `4`. |
| `SpanQuestion` | A list of span dictionaries, e.g. `[{"start": 0, "end": 9, "label": "ORG"}]`; `field=` must point to the text field being annotated. |
| `TextQuestion` | A string. Set `use_markdown=True` if responses should render Markdown/HTML. |

`rg.Suggestion` also accepts `score` as a float or list of floats, `agent` as a model/user identifier string, and `type` as `"model"` or `"human"`. `rg.Response` requires `user_id` and may use status `"draft"`, `"submitted"`, or `"discarded"`.

## Record object format

```python
record = rg.Record(
    id="external-id-001",
    fields={"review": "Works well."},
    metadata={"split": "train", "length": 11},
    vectors={"embedding": [0.1, 0.2, 0.3]},
    suggestions=[rg.Suggestion(question_name="sentiment", value="positive", score=0.98, agent="model-v1")],
    responses=[rg.Response(question_name="sentiment", value="positive", user_id=user.id, status="submitted")],
)
```

Rules:

- `id` is the public external id. It is the same logical value exported as `id` and serialized internally as `external_id`.
- If `fields` are not provided, `id` is required.
- At least one of `fields`, `metadata`, `vectors`, `responses`, or `suggestions` must be provided.
- Vector value length must equal the corresponding `VectorField(dimensions=...)`.

## Dictionary/Hugging Face dataset mapping syntax

`dataset.records.log(records, mapping=...)` maps source keys or dataset columns to Argilla destinations. Mapping values use:

```text
attribute[.type[.parameter]]
```

- `attribute` must be a configured field/question/metadata/vector name, or `id`.
- `type` can be `field`, `suggestion`, `response`, `metadata`, `vector`, or `id`.
- `parameter` can be `value`, `score`, or `agent` for suggestions.
- If `type` is omitted, Argilla infers it from the settings schema. For questions, omitted type defaults to a suggestion value.

Common targets:

| Source purpose | Mapping target |
| --- | --- |
| Record external id | `"id"` |
| Field value | `"<field_name>"` or `"<field_name>.field"` |
| Suggestion value | `"<question_name>"` or `"<question_name>.suggestion.value"` |
| Suggestion score | `"<question_name>.suggestion.score"` |
| Suggestion agent/model | `"<question_name>.suggestion.agent"` |
| Human/existing response | `"<question_name>.response"` and pass `user_id=...` |
| Metadata value | `"<metadata_name>"` or `"<metadata_name>.metadata"` |
| Vector value | `"<vector_name>"` or `"<vector_name>.vector"` |
| One source to multiple destinations | `{"source_col": ("field_a", "question_b")}` |

Example:

```python
mapping = {
    "uuid": "id",
    "prompt": "review",
    "label": "sentiment.suggestion.value",
    "probability": "sentiment.suggestion.score",
    "model": "sentiment.suggestion.agent",
    "gold_label": "sentiment.response",
    "split_name": "split",
    "dense_vector": "embedding",
}
dataset.records.log(rows, mapping=mapping, user_id=client.me.id)
```

If source keys are unknown and not in the mapping, Argilla ignores them with a warning. If a row has no recognizable attribute after mapping, ingestion fails.

## Flattened export columns

`dataset.records.to_list(flatten=True)` and `to_dict(flatten=True)` flatten fields, metadata, vectors, suggestions, and responses:

- Fields become their bare field names, e.g. `review`.
- Metadata becomes its bare metadata property name, e.g. `split`.
- Vectors become their bare vector field names, e.g. `embedding`.
- Suggestions become `<question>.suggestion`, `<question>.suggestion.score`, and `<question>.suggestion.agent`.
- Responses become `<question>.responses`, `<question>.responses.users`, and `<question>.responses.status` because multiple users can respond.
- Similarity search exports can include a top-level `score` for the search score.

Nested exports keep keys `id`, `fields`, `metadata`, `suggestions`, `responses`, `vectors`, `status`, and `_server_id`.

## Markdown and media helpers

For Markdown-enabled `TextField` or `TextQuestion`, Argilla provides helpers:

```python
from argilla.markdown import image_to_html, audio_to_html, video_to_html, pdf_to_html, chat_to_html

html_image = image_to_html("image.png", width="300px", height="300px")
html_audio = audio_to_html("audio.mp3", autoplay=False, loop=False)
html_video = video_to_html("video.mp4", width="50%")
html_pdf = pdf_to_html("file.pdf", width="1000px", height="1000px")
html_chat = chat_to_html([{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}])
```

Helper constraints:

- Local media helpers embed Data URLs and warn or fail for unsupported formats or large files. Keep files small; the helper enforces a 5 MB recommendation limit.
- Width/height must be pixel or percentage strings such as `"300px"` or `"50%"`.
- Hosted media in raw HTML must be reachable by annotators' browsers. Private media needs its own access control plan.
- `chat_to_html` accepts messages with roles `user`, `assistant`, `system`, or `model` and raises on unknown roles.

## Custom field templates

`CustomField(template=..., advanced_mode=False)` uses Handlebars-style placeholders against the browser-side `record` object:

```python
template = """
<style>.row { display: flex; gap: 1rem; }</style>
<div class="row">
  <div>{{record.fields.comparison.left}}</div>
  <div>{{record.fields.comparison.right}}</div>
</div>
"""
settings = rg.Settings(
    fields=[rg.CustomField(name="comparison", template=template)],
    questions=[rg.LabelQuestion(name="winner", labels=["left", "right", "tie"])],
)
record = rg.Record(fields={"comparison": {"left": "A", "right": "B"}})
```

With `advanced_mode=True`, the template can include custom JavaScript and the global `record` object. Treat advanced templates as UI code: avoid external scripts unless the user explicitly accepts that runtime dependency.
