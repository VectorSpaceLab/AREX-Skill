# Argilla 2.x Python SDK API reference

This reference summarizes the public Argilla 2.8.0dev0 Python SDK surface verified for this skill. Calls that create clients, create/update/delete resources, log records, import/export through the Hub, or register webhooks can contact a live Argilla server or the network.

## Client and authentication

```python
rg.Argilla(api_url: Optional[str] = "http://localhost:6900", api_key: Optional[str] = None, timeout: int = 60, retries: int = 5, **http_client_args) -> None
rg.Argilla.deploy_on_spaces(api_key: str, repo_name: Optional[str] = "argilla", org_name: Optional[str] = None, hf_token: Optional[str] = None, space_storage: Optional[Union["small", "medium", "large"]] = None, space_hardware: Optional[Union["cpu-basic", "cpu-upgrade"]] = "cpu-basic", private: Optional[bool] = False) -> rg.Argilla
```

- `api_url` defaults to the local server URL or `ARGILLA_API_URL`; `api_key` defaults to `ARGILLA_API_KEY`. Empty or missing values raise an SDK error.
- `**http_client_args` are forwarded to the underlying HTTP client. Use this for private Hugging Face Spaces, for example `headers={"Authorization": f"Bearer {HF_TOKEN}"}`.
- Instantiating `rg.Argilla` validates the connection and current user; `client.me` returns the authenticated user.
- The latest instantiated client becomes the SDK default client. Many resource constructors use that default when an explicit `client=` is not supplied.

Client collections:

```python
client.datasets                  # collection of Dataset resources
client.datasets(name, workspace=None, id=None) -> Optional[rg.Dataset]
client.users                     # collection of User resources
client.users(username=None, id=None) -> Optional[rg.User]
client.workspaces                # collection of Workspace resources
client.workspaces(name=None, id=None) -> Optional[rg.Workspace]
client.webhooks                  # collection of Webhook resources
client.webhooks(id) -> Optional[rg.Webhook]
```

Collections are iterable and support `len(...)`, indexing, `.list()`, and `.add(resource)` patterns where appropriate.

## Datasets and settings

```python
rg.Dataset(name: Optional[str] = None, workspace: Union[rg.Workspace, str, UUID, None] = None, settings: Optional[rg.Settings] = None, client: Optional[rg.Argilla] = None) -> None
```

Important dataset methods and properties:

```python
dataset.create() -> rg.Dataset
dataset.get() -> rg.Dataset
dataset.update() -> rg.Dataset
dataset.delete() -> None
dataset.progress(with_users_distribution: bool = False) -> dict
rg.Dataset.from_disk(path: str, *, name: Optional[str] = None, workspace: Union[rg.Workspace, str, None] = None, client: Optional[rg.Argilla] = None, with_records: bool = True) -> rg.Dataset
rg.Dataset.from_hub(repo_id: str, *, name: Optional[str] = None, workspace: Union[rg.Workspace, str, None] = None, client: Optional[rg.Argilla] = None, with_records: bool = True, settings: Union[rg.Settings, Literal["auto", "ui"]] = "ui", split: Optional[str] = None, subset: Optional[str] = None, **kwargs) -> Union[rg.Dataset, str]
dataset.to_disk(path: str, *, with_records: bool = True) -> str
dataset.to_hub(repo_id: str, *, with_records: bool = True, generate_card: Optional[bool] = True, **kwargs) -> None
```

Dataset properties include `name`, `id`, `workspace`, `settings`, `fields`, `questions`, `guidelines`, `allow_extra_metadata`, `vectors`, `metadata`, `distribution`, `records`, and `schema`.

```python
rg.Settings(fields: Optional[List[Field]] = None, questions: Optional[List[Question]] = None, vectors: Optional[List[rg.VectorField]] = None, metadata: Optional[List[MetadataProperty]] = None, guidelines: Optional[str] = None, allow_extra_metadata: bool = False, distribution: Optional[rg.TaskDistribution] = None, mapping: Optional[Dict[str, Union[str, Sequence[str]]]] = None, _dataset: Optional[rg.Dataset] = None) -> None
settings.add(property, override: bool = True)
settings.validate() -> None
settings.to_json(path: Union[pathlib.Path, str]) -> None
rg.Settings.from_json(path: Union[pathlib.Path, str]) -> rg.Settings
rg.Settings.from_hub(repo_id: str, subset: Optional[str] = None, feature_mapping: Optional[Dict[str, Literal["question", "field", "metadata"]]] = None, **kwargs) -> rg.Settings
```

Settings validation requires at least one field and one question and enforces unique names across fields, questions, metadata properties, and vectors. `Settings.add(..., override=True)` replaces an existing property with the same name; use `override=False` to fail fast on accidental collisions.

## Fields, questions, metadata, vectors, and distribution

Field signatures:

```python
rg.TextField(name: str, title: Optional[str] = None, use_markdown: Optional[bool] = False, required: bool = True, description: Optional[str] = None, client: Optional[rg.Argilla] = None) -> None
rg.ImageField(name: str, title: Optional[str] = None, required: Optional[bool] = True, description: Optional[str] = None, _client: Optional[rg.Argilla] = None) -> None
rg.ChatField(name: str, title: Optional[str] = None, use_markdown: Optional[bool] = True, required: bool = True, description: Optional[str] = None, _client: Optional[rg.Argilla] = None) -> None
rg.CustomField(name: str, title: Optional[str] = None, template: Optional[str] = "", advanced_mode: Optional[bool] = False, required: bool = True, description: Optional[str] = None, _client: Optional[rg.Argilla] = None) -> None
```

Question signatures:

```python
rg.LabelQuestion(name: str, labels: Union[List[str], Dict[str, str]], title: Optional[str] = None, description: Optional[str] = None, required: bool = True, visible_labels: Optional[int] = None, client: Optional[rg.Argilla] = None) -> None
rg.MultiLabelQuestion(name: str, labels: Union[List[str], Dict[str, str]], visible_labels: Optional[int] = None, labels_order: Literal["natural", "suggestion"] = "natural", title: Optional[str] = None, description: Optional[str] = None, required: bool = True, client: Optional[rg.Argilla] = None) -> None
rg.RankingQuestion(name: str, values: Union[List[str], Dict[str, str]], title: Optional[str] = None, description: Optional[str] = None, required: bool = True, client: Optional[rg.Argilla] = None) -> None
rg.TextQuestion(name: str, title: Optional[str] = None, description: Optional[str] = None, required: bool = True, use_markdown: bool = False, client: Optional[rg.Argilla] = None) -> None
rg.RatingQuestion(name: str, values: List[int], title: Optional[str] = None, description: Optional[str] = None, required: bool = True, client: Optional[rg.Argilla] = None) -> None
rg.SpanQuestion(name: str, field: str, labels: Union[List[str], Dict[str, str]], allow_overlapping: bool = False, visible_labels: Optional[int] = None, title: Optional[str] = None, description: Optional[str] = None, required: bool = True, client: Optional[rg.Argilla] = None) -> None
```

Metadata, vector, and distribution signatures:

```python
rg.TermsMetadataProperty(name: str, options: Optional[List[Any]] = None, title: Optional[str] = None, visible_for_annotators: Optional[bool] = True, client: Optional[rg.Argilla] = None) -> None
rg.FloatMetadataProperty(name: str, min: Optional[float] = None, max: Optional[float] = None, title: Optional[str] = None, visible_for_annotators: Optional[bool] = True, client: Optional[rg.Argilla] = None) -> None
rg.IntegerMetadataProperty(name: str, min: Optional[int] = None, max: Optional[int] = None, title: Optional[str] = None, visible_for_annotators: Optional[bool] = True, client: Optional[rg.Argilla] = None) -> None
rg.VectorField(name: str, dimensions: int, title: Optional[str] = None, _client: Optional[rg.Argilla] = None) -> None
rg.TaskDistribution(min_submitted: int)
```

## Records, suggestions, responses, and record IO

```python
rg.Record(id: Union[UUID, str, None] = None, fields: Optional[Dict[str, FieldValue]] = None, metadata: Optional[Dict[str, Any]] = None, vectors: Optional[Dict[str, List[float]]] = None, responses: Optional[List[rg.Response]] = None, suggestions: Optional[List[rg.Suggestion]] = None, _server_id: Optional[UUID] = None, _dataset: Optional[rg.Dataset] = None)
rg.Suggestion(question_name: str, value: Any, score: Union[float, List[float], None] = None, agent: Optional[str] = None, type: Optional[Literal["model", "human"]] = None, _record: Optional[rg.Record] = None) -> None
rg.Response(question_name: str, value: Any, user_id: UUID, status: Union[rg.ResponseStatus, str, None] = None, _record: Optional[rg.Record] = None) -> None
rg.Vector(name: str, values: list[float]) -> None
```

`Record(id=...)` is the external id. Server-internal ids appear as `_server_id` after fetching/exporting.

`dataset.records` is a `DatasetRecords` interface:

```python
dataset.records(query: Optional[Union[str, rg.Query]] = None, batch_size: Optional[int] = 256, start_offset: int = 0, with_suggestions: bool = True, with_responses: bool = True, with_vectors: Optional[Union[List[str], bool, str]] = None, limit: Optional[int] = None)
dataset.records.log(records: Union[List[dict], List[rg.Record], datasets.Dataset], mapping: Optional[Dict[str, Union[str, Sequence[str]]]] = None, user_id: Optional[UUID] = None, batch_size: int = 256, on_error=RecordErrorHandling.RAISE) -> DatasetRecords
dataset.records.delete(records: List[rg.Record], batch_size: int = 64) -> List[rg.Record]
dataset.records.to_list(flatten: bool = False) -> List[Dict[str, Any]]
dataset.records.to_dict(flatten: bool = False, orient: str = "names") -> Dict[str, Any]
dataset.records.to_json(path: Union[pathlib.Path, str]) -> pathlib.Path
dataset.records.from_json(path: Union[pathlib.Path, str]) -> List[rg.Record]
dataset.records.to_datasets() -> datasets.Dataset
```

`on_error` values are `raise`, `warn`, and `ignore` through the SDK enum.

## Query, filter, and similar search

```python
rg.Query(*, query: Optional[str] = None, similar: Optional[rg.Similar] = None, filter: Union[rg.Filter, List[Tuple[str, str, Any]], Tuple[str, str, Any], None] = None)
rg.Filter(conditions: Union[List[Tuple[str, str, Any]], Tuple[str, str, Any], None] = None)
rg.Similar(name: str, value: Union[Iterable[float], rg.Record], most_similar: bool = True)
```

Filter operators: `==`, `in`, `>=`, `<=`.

Common filter scopes:

| Scope | Meaning |
| --- | --- |
| `id` | Record external id |
| `_server_id` | Argilla server record UUID |
| `inserted_at`, `updated_at` | Timestamp filters |
| `status` | Record status, usually `pending` or `completed` |
| `response.status` | Response status: `draft`, `submitted`, or `discarded` |
| `metadata.<name>` | A configured metadata property |
| `<question>.suggestion` | Suggestion value for a question |
| `<question>.score` | Suggestion score |
| `<question>.agent` | Suggestion agent/model name |
| `<question>.type` | Suggestion type, `model` or `human` |
| `<question>.response` | Response value for a question |
| `<question>` | Defaults to suggestion value for that question |

`rg.Similar(name="embedding", value=[...])` needs a matching `VectorField` and a search backend configured by the server.

## Users and workspaces

```python
rg.User(username: Optional[str] = None, first_name: Optional[str] = None, last_name: Optional[str] = None, role: Optional[str] = None, password: Optional[str] = None, id: Optional[UUID] = None, client: Optional[rg.Argilla] = None, _model: Optional[UserModel] = None) -> None
rg.Workspace(name: Optional[str] = None, id: Optional[UUID] = None, client: Optional[rg.Argilla] = None) -> None
```

User methods: `create`, `get`, `update`, `delete`, `add_to_workspace(workspace)`, `remove_from_workspace(workspace)`, `serialize`, `serialize_json`.

Workspace methods: `create`, `get`, `update`, `delete`, `list_datasets`, `add_user(user_or_username)`, `remove_user(user_or_username)`, `serialize`, `serialize_json`. A workspace cannot be deleted while it contains datasets.

Roles are `owner`, `admin`, and `annotator`. Owners manage users/workspaces globally; admins manage datasets in assigned workspaces; annotators provide feedback in assigned datasets.

## Webhooks

```python
rg.Webhook(url: str, events: List[EventType], description: Optional[str] = None, _client: rg.Argilla = None)
rg.webhook_listener(events: Union[str, List[str]], description: Optional[str] = None, client: Optional[rg.Argilla] = None, server: Optional[FastAPI] = None, raw_event: bool = False) -> Callable
rg.get_webhook_server() -> FastAPI
```

Webhook resource methods: `create`, `get`, `update`, `delete`, `serialize`, `serialize_json`. Webhook properties include `url`, `events`, `enabled`, `description`, and read-only `secret`.

Supported events:

- Dataset: `dataset.created`, `dataset.updated`, `dataset.deleted`, `dataset.published`
- Record: `record.created`, `record.updated`, `record.deleted`, `record.completed`
- Response: `response.created`, `response.updated`, `response.deleted`

The `webhook_listener` decorator creates or updates a webhook and adds a POST endpoint when the decorator is executed. Keep decorators inside explicit setup functions unless automatic registration is intended.
