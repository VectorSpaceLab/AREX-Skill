# Legacy API reference

This reference is intentionally narrow. It lists only the legacy compatibility calls and current Argilla 2.x objects needed for migration from v1/Rubrix datasets/users/workspaces. Do not use it to revive old training, monitoring, weak-supervision, or listener integrations.

## Legacy compatibility surface

The current SDK exposes a deprecated migration shim:

```python
import argilla.v1 as rg_v1
```

That shim re-exports the `argilla-v1` package if it is installed. It is for migration only and may be removed in the future.

| Call | Purpose | Migration notes |
| --- | --- | --- |
| `rg_v1.init(api_url=None, api_key=None, workspace=None, timeout=60, extra_headers=None, httpx_extra_kwargs=None)` | Connect the legacy client singleton to an Argilla v1/Rubrix server. | Pass explicit `api_url` and `api_key` so the script cannot fall back to unrelated local credentials. |
| `rg_v1.User.list()` | List legacy users. | Use owner-level credentials when possible; this can be permission-sensitive. |
| `rg_v1.User.me()` | Return the legacy current user. | Useful only for diagnostics; target response ownership should normally use v2 users. |
| `rg_v1.Workspace.list()` | List legacy workspaces visible to the current user. | Preserve names as the stable join key unless IDs must be kept. |
| `rg_v1.load_dataset_settings(name, workspace=None)` | Load legacy dataset settings, including label schemas for task datasets. | Use `settings_v1.label_schema` for classification/span labels when present. |
| `rg_v1.load(name, workspace=None, query=None, vector=None, ids=None, limit=None, sort=None, id_from=None, batch_size=250, include_vectors=True, include_metrics=True, as_pandas=None)` | Load legacy dataset records. | Use `limit`/`id_from` for large datasets; keep `include_vectors=True` if vectors must be migrated. |
| `legacy_dataset.to_datasets()` | Convert the loaded legacy dataset to a Hugging Face `datasets.Dataset`-like object. | This is the export/snapshot object used by the mapping pass. |

Legacy task dataset classes of interest are `DatasetForTextClassification`, `DatasetForTokenClassification`, and `DatasetForText2Text`. `FeedbackDataset` does not require the same schema migration because it already follows the v2-style extensible dataset model.

## Current Argilla 2.x recreation surface

Use the current `argilla` package for all target writes:

```python
import argilla as rg

client = rg.Argilla(api_url=CURRENT_API_URL, api_key=CURRENT_API_KEY, timeout=60, retries=5)
```

Verified current objects for the migration path:

| Current object | Use in migration |
| --- | --- |
| `rg.Argilla(api_url="http://localhost:6900", api_key=None, timeout=60, retries=5, **http_client_args)` | Target server client. Supply the target URL/key explicitly. |
| `rg.Workspace(name=None, id=None, client=None)` | Recreate workspaces with `.create()`. Supply `id=` only if preserving IDs is required and supported by the target. |
| `rg.User(username=None, first_name=None, last_name=None, role=None, password=None, id=None, client=None, _model=None)` | Recreate users with `.create()`, then use `add_to_workspace(...)` for memberships. Passwords must be newly chosen. |
| `rg.Settings(fields=None, questions=None, vectors=None, metadata=None, guidelines=None, allow_extra_metadata=False, distribution=None, mapping=None)` | Define the target schema: fields, questions, metadata properties, vectors, and optional distribution. |
| `rg.Dataset(name=None, workspace=None, settings=None, client=None)` | Create the target dataset with `.create()`. |
| `dataset.records.log(records, mapping=None, user_id=None, batch_size=256, on_error=...)` | Upload converted records. Prefer explicit `rg.Record` objects for nested legacy predictions/annotations. |
| `rg.Record(id=None, fields=None, metadata=None, vectors=None, responses=None, suggestions=None, ...)` | Current generic record shape for all migrated task datasets. |
| `rg.Suggestion(question_name, value, score=None, agent=None, type=None, ...)` | Machine/model prediction attached to a current question. |
| `rg.Response(question_name, value, user_id, status=None, ...)` | Human annotation/response attached to a current question and v2 user. |

## Field, question, metadata, and vector classes

Use these current classes for the selected migration scope:

- Fields: `rg.TextField` for text inputs. Add additional fields if legacy `inputs` carries more than one key.
- Questions: `rg.LabelQuestion`, `rg.MultiLabelQuestion`, `rg.SpanQuestion`, and `rg.TextQuestion`.
- Metadata: `rg.TermsMetadataProperty`, `rg.FloatMetadataProperty`, and `rg.IntegerMetadataProperty`.
- Vectors: `rg.VectorField(name=..., dimensions=...)`.

Keep names stable. `question_name` in every `rg.Suggestion` and `rg.Response` must exactly match a v2 question name; `record.fields`, `record.metadata`, and `record.vectors` keys must match the target settings.

## Package and dependency constraints

- `argilla.v1` is a shim; if `argilla-v1` is absent it raises an install error instead of silently providing legacy APIs.
- `argilla-v1` has old dependency constraints, including `httpx >=0.15,<=0.26`, `typer >=0.6,<0.10`, `numpy <1.27`, and many optional integration extras for legacy training, monitoring, Hugging Face, spaCy, transformers, OpenAI, and related frameworks.
- Current `argilla-server` 2.x expects the newer current stack; the inspected current environment used `httpx 0.27.x`. Co-installing `argilla-v1` into the same current server environment can break server CLI/API dependencies.
- If legacy import execution is unavoidable, create a separate legacy environment and keep it read-only/export-focused. Do not install broad `argilla-v1` extras into the current target server or SDK environment.
- The old `rubrix` module/CLI name is historical. Route new code to `argilla` and use `argilla.v1` only as a short-lived bridge for migration.

## Explicitly out of scope

- Legacy `training`, `monitoring`, listener, metrics, and heavy integration APIs.
- Notebook/tutorial execution that requires tokens, external network, or a live server with side effects.
- Server deployment and reindex mechanics; use `server-ops` when the issue is operational rather than a data mapping problem.

Provenance: distilled from the current SDK/server inspection, the v1 shim, `argilla-v1` project metadata, and selected legacy client/CLI source names.
