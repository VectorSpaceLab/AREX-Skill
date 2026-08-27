# Argilla Python SDK workflows

Use these recipes as starting points. They are intentionally explicit about live-server actions so you can avoid accidental mutations.

## Connect and authenticate

```python
import os
import argilla as rg

client = rg.Argilla(
    api_url=os.environ["ARGILLA_API_URL"],
    api_key=os.environ["ARGILLA_API_KEY"],
    timeout=60,
    retries=5,
)
print(client.me.username, client.me.role)
```

For a private Hugging Face Space, the Hugging Face token is an HTTP header, not the Argilla API key:

```python
client = rg.Argilla(
    api_url="https://<owner>-<space>.hf.space",
    api_key="<argilla-api-key>",
    headers={"Authorization": f"Bearer {os.environ['HF_TOKEN']}"},
)
```

Create the client before fields/questions/datasets if you are not relying on `ARGILLA_API_URL` and `ARGILLA_API_KEY`, because SDK resources can use the current default client.

## Create a dataset with settings

```python
import argilla as rg

client = rg.Argilla(api_url="<api_url>", api_key="<api_key>")

settings = rg.Settings(
    guidelines="Classify each review and explain difficult cases.",
    fields=[
        rg.TextField(name="review", title="Review", use_markdown=False),
    ],
    questions=[
        rg.LabelQuestion(name="sentiment", labels=["positive", "negative"], title="Sentiment"),
        rg.TextQuestion(name="rationale", title="Why?", required=False, use_markdown=True),
    ],
    metadata=[
        rg.TermsMetadataProperty(name="split", options=["train", "validation", "test"]),
        rg.FloatMetadataProperty(name="source_score", min=0.0, max=1.0, visible_for_annotators=False),
    ],
    vectors=[rg.VectorField(name="embedding", dimensions=3)],
    distribution=rg.TaskDistribution(min_submitted=1),
    allow_extra_metadata=False,
)

existing = client.datasets(name="review_triage", workspace="argilla")
if existing is not None:
    raise RuntimeError("Choose a new dataset name or intentionally update the existing dataset")

dataset = rg.Dataset(
    name="review_triage",
    workspace="argilla",
    settings=settings,
    client=client,
).create()
```

Notes:

- Keep names unique across fields/questions/metadata/vectors.
- `TextField(use_markdown=True)` and `TextQuestion(use_markdown=True)` permit Markdown/HTML rendering.
- `TaskDistribution(min_submitted=N)` controls how many submitted responses are required before a record is completed.

## Log records as SDK objects

```python
records = [
    rg.Record(
        id="review-001",  # external id
        fields={"review": "The app is fast and pleasant."},
        metadata={"split": "train", "source_score": 0.94},
        vectors={"embedding": [0.1, 0.2, 0.3]},
        suggestions=[rg.Suggestion(question_name="sentiment", value="positive", score=0.94, agent="baseline-v1")],
    ),
    rg.Record(
        id="review-002",
        fields={"review": "Crashes during checkout."},
        metadata={"split": "validation", "source_score": 0.88},
        vectors={"embedding": [0.0, 0.4, 0.1]},
        suggestions=[rg.Suggestion(question_name="sentiment", value="negative", score=0.88, agent="baseline-v1")],
    ),
]

dataset.records.log(records, batch_size=256)
```

To log existing human labels as responses, retrieve or define the user and use `rg.Response`:

```python
user = client.users(username="alice")
records = [
    rg.Record(
        id="review-003",
        fields={"review": "Great support."},
        responses=[rg.Response(question_name="sentiment", value="positive", user_id=user.id, status="submitted")],
    )
]
dataset.records.log(records)
```

## Log dictionary or Hub dataset rows with mappings

When source column names do not match Argilla schema names, use `mapping`. Question columns map to suggestions by default; use dot notation for response, suggestion score, and suggestion agent.

```python
source_rows = [
    {
        "row_id": "r-1",
        "text_col": "The docs are clear.",
        "pred_label": "positive",
        "pred_confidence": 0.91,
        "model_name": "sentiment-baseline",
        "human_label": "positive",
        "split_col": "train",
        "score_col": 0.91,
        "embedding_col": [0.3, 0.2, 0.5],
    }
]

mapping = {
    "row_id": "id",
    "text_col": "review",
    "pred_label": "sentiment.suggestion.value",
    "pred_confidence": "sentiment.suggestion.score",
    "model_name": "sentiment.suggestion.agent",
    "human_label": "sentiment.response",
    "split_col": "split",
    "score_col": "source_score",
    "embedding_col": "embedding",
}

dataset.records.log(source_rows, mapping=mapping, user_id=client.me.id)
```

Map one source column to multiple Argilla destinations with a tuple/list:

```python
dataset.records.log(
    [{"message": "Summarize this", "quality": 4}],
    mapping={"message": ("prompt_field", "prompt_answer")},
)
```

## List, update, and delete records

```python
# Fetch records with optional payloads.
for record in dataset.records(with_suggestions=True, with_responses=True, with_vectors=True, limit=100):
    print(record.id, record.status, record.fields, record.suggestions, record.responses)

# Update suggestions or metadata, then upsert by id.
updated = []
for record in dataset.records(with_suggestions=True, limit=100):
    record.metadata["split"] = "reviewed"
    if record.suggestions["sentiment"]:
        record.suggestions["sentiment"].agent = "baseline-v2"
    updated.append(record)

dataset.records.log(updated)

# Delete retrieved records intentionally.
records_to_delete = list(dataset.records(rg.Query(filter=rg.Filter(("status", "==", "pending"))), limit=5))
dataset.records.delete(records_to_delete)
```

## Search, filter, and similar search

```python
# Text search.
records = dataset.records(rg.Query(query="checkout crash"), limit=25).to_list(flatten=True)

# Filter by suggestions, response status, and metadata.
filters = rg.Filter([
    ("sentiment.suggestion", "==", "negative"),
    ("response.status", "in", ["draft", "submitted"]),
    ("metadata.split", "==", "validation"),
    ("metadata.source_score", ">=", 0.5),
])
records = dataset.records(rg.Query(filter=filters), with_suggestions=True, with_responses=True).to_list(flatten=True)

# Combine text query and filters.
query = rg.Query(
    query='"payment error" | checkout',
    filter=rg.Filter([("sentiment.score", ">=", 0.8), ("metadata.split", "==", "train")]),
)
records = dataset.records(query=query, with_suggestions=True).to_list(flatten=True)

# Similarity search. The dataset must define VectorField(name="embedding", dimensions=...).
query = rg.Query(similar=rg.Similar(name="embedding", value=[0.1, 0.2, 0.3], most_similar=True))
for item in dataset.records(query=query, with_vectors=True, limit=10):
    # Similar searches may yield (record, score) when iterated.
    record, score = item if isinstance(item, tuple) else (item, None)
    print(record.id, score)
```

Text search uses simple query string syntax: whitespace/`+` for AND, `|` for OR, `-` for negation, `*` for prefix, quotes for phrases, parentheses for precedence, and `~N` for edit distance. Escape literal operator characters with a backslash.

## Export records and datasets

```python
# Python objects.
nested_list = dataset.records.to_list(flatten=False)
flat_list = dataset.records.to_list(flatten=True)
by_name = dataset.records.to_dict(flatten=True, orient="names")
by_id = dataset.records.to_dict(flatten=False, orient="index")
hf_dataset = dataset.records.to_datasets()
dataset.records.to_json("records.json")

# Local directory containing .argilla/settings.json, .argilla/dataset.json, and optional records.json.
dataset.to_disk("argilla_backup", with_records=True)
restored = rg.Dataset.from_disk("argilla_backup", name="restored_review_triage", workspace="argilla", client=client)

# Hugging Face Hub. Pass token for private repos.
dataset.to_hub("<org-or-user>/<dataset-repo>", token="<hf-token>", with_records=True, generate_card=True)
loaded = rg.Dataset.from_hub(
    "<org-or-user>/<dataset-repo>",
    name="loaded_review_triage",
    workspace="argilla",
    client=client,
    settings="auto",
    token="<hf-token>",
)
```

`Dataset.from_hub(..., settings="ui")` returns a configuration URL string by default. Use `settings="auto"` for inferred settings or pass an explicit `rg.Settings` object for deterministic imports.

Settings can be serialized independently:

```python
settings.to_json("settings.json")
settings = rg.Settings.from_json("settings.json")
settings = rg.Settings.from_hub("<org-or-user>/<dataset-repo>", feature_mapping={"label_col": "question"})
```

## Users and workspaces

```python
# Workspace lifecycle.
workspace = client.workspaces("annotation")
if workspace is None:
    workspace = rg.Workspace(name="annotation", client=client).create()

# User lifecycle. Only owners can manage users globally.
user = client.users("alice")
if user is None:
    user = rg.User(username="alice", password="temporary-password", role="annotator", client=client).create()

workspace.add_user(user)           # or workspace.add_user("alice")
workspace_users = list(workspace.users)
workspace_datasets = workspace.datasets

# Update allowed user fields.
user.role = "admin"
user.update()

# Remove access intentionally.
workspace.remove_user(user)
```

Owners manage users/workspaces; admins manage datasets within assigned workspaces; annotators provide feedback in assigned datasets. Do not delete a workspace until its datasets have been deleted or moved.

## Webhooks

The convenient decorator registers a webhook when it is executed:

```python
import argilla as rg
from datetime import datetime

client = rg.Argilla(api_url="<api_url>", api_key="<api_key>")
server = rg.get_webhook_server()

@rg.webhook_listener(events=["record.completed", "response.created"], client=client, server=server)
async def handle_feedback(type: str, timestamp: datetime, record=None, response=None, dataset=None):
    print(type, timestamp, record or response or dataset)
```

Because decorator execution can mutate server webhook resources, prefer the bundled safe template for production answers:

```bash
python scripts/webhook_listener_template.py --help
python scripts/webhook_listener_template.py --register --serve --event record.completed --event response.created
```

Webhook deployment checklist:

1. Set `WEBHOOK_SERVER_URL` to the public URL the Argilla server can reach, not necessarily the URL your browser uses.
2. Use an IP address or a URL with a top-level domain; webhook validation rejects problematic local hostnames.
3. Install and run FastAPI/uvicorn only when you intentionally serve the listener.
4. Do not delete existing webhooks unless the user explicitly asks.

## Markdown, media, chat, and custom field workflows

```python
from argilla.markdown import chat_to_html, image_to_html

messages = [
    {"role": "user", "content": "What is Argilla?"},
    {"role": "assistant", "content": "A dataset annotation platform."},
]
html_chat = chat_to_html(messages)

settings = rg.Settings(
    fields=[
        rg.TextField(name="conversation_html", use_markdown=True),
        rg.ChatField(name="chat", use_markdown=True),
        rg.CustomField(
            name="side_by_side",
            template="<div>{{record.fields.side_by_side.left}}</div><div>{{record.fields.side_by_side.right}}</div>",
        ),
    ],
    questions=[rg.TextQuestion(name="notes", use_markdown=True)],
)

records = [
    rg.Record(fields={
        "conversation_html": html_chat,
        "chat": messages,
        "side_by_side": {"left": "A", "right": "B"},
    })
]
```

Use `image_to_html`, `audio_to_html`, `video_to_html`, `pdf_to_html`, and `chat_to_html` for Markdown-enabled text fields/questions. Use `ImageField` for image values and `CustomField` when the field value is a dictionary rendered by a template.
