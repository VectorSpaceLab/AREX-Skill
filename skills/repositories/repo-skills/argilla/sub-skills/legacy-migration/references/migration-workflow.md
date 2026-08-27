# Legacy migration workflow

This workflow covers legacy Argilla v1/Rubrix users, workspaces, and task-specific datasets that must be recreated in the current Argilla 2.x SDK/server model. It does not cover new v2-only dataset design, deployment operations, or old training/monitoring integrations.

## Safety gate

Before writing to any current server:

- Back up the legacy server and any current target server.
- Export first. Keep a local, inspectable export or at least a reproducible `rg_v1.load(...).to_datasets()` snapshot before creating target resources.
- Keep legacy and current API URLs/API keys separate; do not point v1 extraction code at the v2 target by accident.
- Passwords cannot be recovered from the legacy server. If recreating users on a new v2 server, generate and securely distribute new passwords.
- If the user must keep old user IDs and passwords, prefer a same-server upgrade path or a temporary v2 copy path. A fresh target-server recreation will normally create new credentials and may create new IDs unless IDs are intentionally supplied.
- Do not install `argilla-v1` and its old optional integrations into the current Argilla 2.x server environment. Use a separate legacy inspection/runtime environment if the old package must be imported.

## Decision tree

1. **Is the source a `FeedbackDataset`?** It already uses the v2-style format. Do not run the legacy task-dataset mapping below. If search is stale after a 2.x server/index change, hand off to `server-ops` for reindexing.
2. **Is the source a task-specific legacy dataset?** Migrate `DatasetForTextClassification`, `DatasetForTokenClassification`, or `DatasetForText2Text` by rebuilding v2 settings and logging converted records.
3. **Does the user need exact IDs/passwords?** Prefer the safer same-server/temporary-copy upgrade path instead of a clean re-create on a new target.
4. **Is the blocker deployment, proxying, database/search, or Redis?** Hand off to `server-ops`; this sub-skill owns the data/API mapping only.

## Recommended migration order

### 1. Connect to the legacy server and extract source state

Use the compatibility module only as a migration bridge:

```python
import argilla.v1 as rg_v1

rg_v1.init(api_url=LEGACY_API_URL, api_key=LEGACY_API_KEY)

users_v1 = list(rg_v1.User.list())
workspaces_v1 = list(rg_v1.Workspace.list())
settings_v1 = rg_v1.load_dataset_settings(DATASET_NAME, workspace=WORKSPACE_NAME)
records_v1 = rg_v1.load(DATASET_NAME, workspace=WORKSPACE_NAME)
hf_dataset = records_v1.to_datasets()
```

Use owner/admin-level credentials for inventory steps. `User.list()` can be permission-sensitive; a non-owner key may not see enough users to preserve response ownership.

### 2. Connect to the current Argilla 2.x target

```python
import argilla as rg

client = rg.Argilla(api_url=CURRENT_API_URL, api_key=CURRENT_API_KEY, timeout=60, retries=5)
```

The current target resources are recreated with `rg.Workspace`, `rg.User`, `rg.Settings`, `rg.Dataset`, `rg.Record`, `rg.Suggestion`, and `rg.Response`.

### 3. Recreate workspaces before users

```python
for workspace in workspaces_v1:
    rg.Workspace(id=workspace.id, name=workspace.name, client=client).create()
```

If preserving IDs is not required or the target rejects supplied IDs, let the server create new IDs and keep a mapping table from legacy workspace name/ID to current workspace name/ID.

### 4. Recreate users and workspace memberships

```python
for user in users_v1:
    user_v2 = rg.User(
        id=user.id,                 # omit if the target should generate IDs
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        password=NEW_PASSWORD_FOR_USER,
        client=client,
    ).create()

    if user.role == "owner":
        continue

    for legacy_workspace in user.workspaces:
        workspace_v2 = client.workspaces(name=legacy_workspace.name)
        if workspace_v2 is not None:
            user_v2.add_to_workspace(workspace_v2)
```

Passwords are write-only. Keep a secure password handoff outside the migration script output.

### 5. Define v2 settings

Use `settings_v1.label_schema` as the label source when available, but explicitly choose the v2 question class based on the legacy dataset kind.

| Legacy source | V2 fields/questions | Main record mapping |
| --- | --- | --- |
| Single-label `DatasetForTextClassification` | `rg.TextField(name="text")` plus `rg.LabelQuestion(name="label", labels=settings_v1.label_schema)` | Legacy `prediction[0]` -> one `rg.Suggestion(question_name="label", value=label, score=score, agent=prediction_agent)`. Legacy `annotation` -> one `rg.Response(question_name="label", value=annotation, user_id=...)`. |
| Multi-label `DatasetForTextClassification` | `rg.TextField(name="text")` plus `rg.MultiLabelQuestion(name="labels", labels=settings_v1.label_schema)` | Prediction list -> `value` as labels sequence and `score` as parallel scores sequence. Annotation -> multi-label `rg.Response(question_name="labels", value=annotation, user_id=...)`. |
| `DatasetForTokenClassification` | `rg.TextField(name="text")` plus `rg.SpanQuestion(name="spans", labels=settings_v1.label_schema)` | Prediction spans list -> `rg.Suggestion(question_name="spans", value=spans, score=[span["score"] ...], agent=...)`. Annotation spans -> `rg.Response(question_name="spans", value=annotation, user_id=...)`. |
| `DatasetForText2Text` / text generation | `rg.TextField(name="text")` plus `rg.TextQuestion(name="text_generation")` | First generation candidate -> `rg.Suggestion(question_name="text_generation", value=prediction[0]["text"], score=prediction[0].get("score"), agent=...)`. Annotation text -> `rg.Response(question_name="text_generation", value=annotation, user_id=...)`. |

Include every legacy input key that must remain visible as a v2 field. If legacy records use `record.inputs` with multiple keys, create one compatible v2 field per retained input key instead of assuming only `text` exists.

### 6. Preserve metadata and vectors deliberately

- Create metadata settings for every metadata key you intend to keep. Use `rg.TermsMetadataProperty` for categorical/string values, `rg.FloatMetadataProperty` for numeric floats, and `rg.IntegerMetadataProperty` for integer values.
- Create vector settings with `rg.VectorField(name=VECTOR_NAME, dimensions=N)` for each vector key. The record-level `vectors` dict must use the same key names and vector dimensions.
- If some records lack metadata or vectors, normalize to `{}` for missing entries rather than passing `None`.
- If the source has metadata keys that are not declared in v2 settings and `allow_extra_metadata=False`, logging will fail.

### 7. Map suggestions and responses

Build the target-side user lookup after recreating users:

```python
users_by_name = {user.username: user for user in client.users}
current_user = client.me
```

Then create each `rg.Record` explicitly:

```python
record = rg.Record(
    id=data["id"],
    fields=data.get("inputs", {"text": data.get("text")}),
    metadata=data.get("metadata") or {},
    vectors=data.get("vectors") or {},
    suggestions=suggestions,
    responses=responses,
)
```

Use `users_by_name.get(legacy_annotation_agent, current_user).id` for response ownership only when the legacy annotator cannot be recreated on the target. Prefer explicit user mapping when auditability matters.

### 8. Create the dataset and log records

```python
existing = client.datasets(name=DATASET_NAME, workspace=WORKSPACE_NAME)
if existing is not None:
    # Either delete intentionally, rename the target, or stop for user approval.
    existing.delete()

dataset = rg.Dataset(name=DATASET_NAME, workspace=WORKSPACE_NAME, settings=settings, client=client)
dataset.create()
dataset.records.log(records, batch_size=256)
```

For simple flat tabular inputs, `dataset.records.log(records, mapping=...)` can map source columns to target field/question/metadata/vector targets. For legacy task datasets with nested predictions and annotations, explicit `rg.Record` objects are usually safer because they make suggestions, responses, user ownership, metadata, and vectors visible.

### 9. Validate after upload

- Compare source and target record counts.
- Spot-check at least one record per task shape.
- Confirm suggestions and responses appear under the expected question names.
- Confirm metadata and vector keys match v2 settings.
- If the data was already a `FeedbackDataset` or only search/index behavior changed, hand off to `server-ops` for `REINDEX_DATASETS=1` or equivalent server reindex operations instead of rebuilding the dataset.

Provenance: distilled from Argilla 2.8.0dev0 SDK/server inspection, the legacy task-dataset migration guide, Rubrix migration notes, the v1 compatibility shim, and `argilla-v1` source/metadata.
