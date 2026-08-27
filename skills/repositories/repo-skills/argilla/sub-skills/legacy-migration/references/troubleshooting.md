# Legacy migration troubleshooting

Use this reference when a v1/Rubrix-to-v2 migration fails during import, identity recreation, schema mapping, record logging, or post-upgrade search behavior.

## Import and dependency failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `import argilla.v1 as rg_v1` raises that `argilla-v1` is not installed. | The current SDK shim delegates to the separate legacy package. | Install or inspect `argilla-v1` only in a separate legacy environment, or use a same-server upgrade path. Do not add broad legacy extras to the current Argilla 2.x server env. |
| Current `argilla_server` CLI/API breaks after installing legacy dependencies. | `argilla-v1` pins old dependencies such as `httpx<=0.26` and old Typer ranges, while current server dependencies require the newer stack. | Separate environments: one read-only/export-focused legacy env, one current target env. Restore current dependencies before operating the v2 server. |
| Legacy code still imports `rubrix`. | Rubrix is the historical package name. | Replace new work with `argilla`. Use `argilla.v1` only for compatibility extraction, not as a permanent application API. |
| Old training, monitoring, or listener code is requested. | Those surfaces pull broad optional integrations and are outside the selected migration scope. | State the scope boundary. Migrate datasets/users/workspaces only, then route any new training or monitoring workflow to modern tools or a separate legacy-only analysis. |

## Identity, credentials, and permissions

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| The user wants to keep legacy passwords. | Passwords cannot be recovered from the legacy server. | Generate new passwords for fresh v2 recreation. If exact credentials must survive, use the safer same-server upgrade or temporary v2 copy strategy instead of recreating users on a new server. |
| User or workspace IDs changed. | A fresh target server generated new IDs, or supplied legacy IDs were rejected. | Decide before migration whether IDs matter. If they do, test ID preservation with a small subset or choose the same-server upgrade path. If not, keep an ID mapping table for audit records. |
| `rg_v1.User.list()` is empty, incomplete, or forbidden. | The legacy key lacks owner-level permissions. | Retry inventory with an owner/admin key. Do not infer user ownership from partial lists. |
| Workspace membership does not match after migration. | Workspaces were not created before users, names differ, or owner users are handled differently. | Recreate workspaces first. Use exact workspace names as join keys. Skip owner workspace assignment when appropriate and call `user_v2.add_to_workspace(workspace_v2)` only after both resources exist. |
| Responses are assigned to the wrong current user. | Legacy annotation agents were not recreated or usernames changed. | Build `users_by_name = {user.username: user for user in client.users}` after target user creation. Use `client.me` as a fallback only when acceptable; otherwise stop and ask for an explicit user mapping. |

## Dataset creation and schema failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Dataset.create()` fails because the dataset already exists. | The target workspace already has a dataset with the same name. | Stop for approval, rename the target, or intentionally delete the existing dataset with `client.datasets(name=..., workspace=...).delete()` before creating the migrated one. |
| Records fail to log with missing fields. | Legacy `record.inputs` has keys not declared as v2 fields, or token/text-generation records use `text` while the field name differs. | Define one v2 field per retained input key. Ensure every `record.fields` key exactly matches the settings field names. |
| Suggestions or responses do not appear. | `question_name` does not match the v2 question name, or values have the wrong shape. | Match names exactly: `label`, `labels`, `spans`, or `text_generation` only if those are the actual v2 question names. Check value and score shapes per task. |
| Multi-label suggestions are rejected. | Labels and scores are not parallel sequences. | Convert legacy prediction entries to `labels, scores = zip(*[(p["label"], p["score"]) for p in prediction])`, then create `rg.Suggestion(question_name="labels", value=labels, score=scores, agent=...)`. |
| Span suggestions/responses are rejected. | Span objects are malformed or the target question is not a `SpanQuestion`. | Use `rg.SpanQuestion(name="spans", labels=...)`; ensure each span contains the expected label/start/end-style payload and use `score=[span["score"] ...]` for suggestions when scores exist. |
| Text-generation suggestions are rejected or incomplete. | The migration tries to copy a whole legacy candidate list into one text response. | Choose the intended candidate, commonly `prediction[0]["text"]`, and store its score/agent in one `rg.Suggestion(question_name="text_generation", ...)`. |
| Metadata logging fails. | Metadata keys/types are not declared or `allow_extra_metadata=False`. | Add `TermsMetadataProperty`, `FloatMetadataProperty`, or `IntegerMetadataProperty` for retained keys, or intentionally allow extra metadata if the target policy permits it. |
| Vector logging fails. | Vector key missing in settings or dimension mismatch. | Add `rg.VectorField(name=..., dimensions=N)` for each migrated vector and verify every record vector length equals `N`. |

## FeedbackDataset and search-index confusion

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| A `FeedbackDataset` is selected for legacy migration. | `FeedbackDataset` already follows the v2-style extensible dataset format. | Do not rebuild it through the legacy task-dataset mapping. Export/backup as needed, then focus on server upgrade and search-index health. |
| Records exist but search/filter results are stale after a 2.x change. | The server search index structure changed or search data needs refresh. | Hand off to `server-ops`. For Docker/server operation, the relevant current setting is `REINDEX_DATASETS=1` or the equivalent search-engine reindex command. |
| Rubrix-era server data is not visible after upgrade. | The migration is a server/index operation, not a record mapping issue. | Hand off to `server-ops` for the Rubrix/Argilla operational migration path and search alias/reindex handling. |

## When to stop instead of guessing

Stop and ask for a decision when:

- The user requires exact password preservation.
- The target already contains a dataset with the same name and deletion/overwrite was not approved.
- The legacy user list is incomplete but responses must retain user ownership.
- Metadata or vector dimensions cannot be inferred from the export.
- The issue is actually server reachability, proxy base URL, database/search/Redis health, or deployment state.

Provenance: distilled from the current Argilla 2.x SDK/server facts, the legacy migration guide, Rubrix migration notes, `argilla.v1` shim behavior, `argilla-v1` dependency metadata, and current server reindex configuration.
