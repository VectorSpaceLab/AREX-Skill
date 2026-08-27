# Query Input Contracts

GraphRAG query methods consume completed index tables. The CLI resolves these through the configured output storage/table provider; Python callers usually pass pandas DataFrames read from the same parquet outputs.

## Required Tables by Method

| Method | Required tables | Optional tables |
| --- | --- | --- |
| `global` | `entities`, `communities`, `community_reports` | none |
| `local` | `entities`, `communities`, `community_reports`, `text_units`, `relationships` | `covariates` |
| `drift` | `entities`, `communities`, `community_reports`, `text_units`, `relationships` | none |
| `basic` | `text_units` | none |
| question generation | same practical shape as `local` | `covariates` |

When using `--data`, provide the directory that directly contains files such as `entities.parquet`, not a parent run directory unless the configured table provider resolves that parent.

## Required Columns

The adapters read these core columns:

- `entities`: `id`, `title`, `human_readable_id`, `description`, `degree`, `text_unit_ids`; `type` and `description_embedding` are commonly present and useful.
- `communities`: `id`, `community`, `level`, `title`, `entity_ids`, `parent`, `children`.
- `community_reports`: `id`, `community`, `level`, `title`, `summary`, `full_content`, `rank`; `full_content_embedding` may be present in BYOG tables but DRIFT normally reads report vectors from the vector store by report `id`.
- `text_units`: `id`, `text`, `entity_ids`, `relationship_ids`, `n_tokens`, `document_id`; `covariate_ids` is optional.
- `relationships`: `id`, `human_readable_id`, `source`, `target`, `description`, `combined_degree`, `weight`, `text_unit_ids`.
- `covariates`: `id`, `human_readable_id`, `subject_id`, `type`, `object_id`, `status`, `start_date`, `end_date`, `description`.

List-like columns may arrive as arrays from parquet; the GraphRAG loaders convert arrays to lists. Strings in optional-list fields are treated as single-item lists. Required list fields such as `communities.children` must be list-like.

## Community Level Behavior

`community_level` filters rows where `level <= community_level`. For non-dynamic global search, GraphRAG rolls entities up to the maximum community each entity belongs to, then keeps reports matching those communities. If a requested level is absent or too low, global/local/DRIFT may run with too few reports or entities.

Dynamic global selection still accepts `community_level`; it caps the maximum level before selection. If dynamic selection returns no relevant reports, inspect `global_search.dynamic_search_threshold`, `dynamic_search_max_level`, and whether report summaries/full content are informative.

## BYOG Table Advice

For bring-your-own graph/index tables, align IDs exactly:

- `communities.entity_ids` must reference `entities.id`.
- `relationships.source` and `relationships.target` should match entity titles used in local context relationships.
- `text_units.entity_ids` and `text_units.relationship_ids` should reference available entity and relationship IDs.
- `community_reports.community` must match `communities.community` values and include the requested levels.
- Report IDs used for DRIFT `community_full_content` vectors must match `community_reports.id`.

Run `scripts/validate_query_prereqs.py` before invoking a model-backed query to catch missing files, missing columns, empty filtered levels, and common schema mismatches.
