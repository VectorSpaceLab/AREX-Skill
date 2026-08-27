# Browse Tree and Targeted Sync

## When to read this

Read this before changing source browse-tree support, lazy child loading, browse-node ID encoding, node-selection persistence, or targeted sync behavior. Pair with sibling [backend-api](../../backend-api/SKILL.md) for endpoint request/response lifecycle and auth/org headers.

## Connector-facing contract

A source that sets `supports_browse_tree=True` must implement two source-owned methods:

| Method | Responsibility | Failure mode if wrong |
| --- | --- | --- |
| `get_browse_children(parent_node_id=None)` | Return a list of `BrowseNode` objects for the root or one parent node. | Browse endpoint returns empty/wrong tree or raises source API errors. |
| `parse_browse_node_id(node_id)` | Decode a `source_node_id` into `(node_type, node_metadata)` for persistence and targeted sync. | Node selection saves unusable metadata; targeted sync silently skips or syncs the wrong scope. |

`generate_entities(..., node_selections=...)` must detect non-empty selections and run a targeted path instead of the normal full/incremental path.

## Data types

| Type | Fields that matter | Notes |
| --- | --- | --- |
| `BrowseNode` | `source_node_id`, `node_type`, `title`, optional `description`, `item_count`, `has_children`, `node_metadata`. | Returned by connector `get_browse_children()`. `source_node_id` is source-owned and must be stable enough for selection. |
| `BrowseTreeResponse` | `nodes`, `parent_node_id`, `total`. | API wrapper around source children. |
| `NodeSelectionRequest` | `source_node_ids`. | Caller submits IDs, not full metadata. |
| `NodeSelectionCreate` / `NodeSelectionData` | `source_node_id`, `node_type`, `node_title`, `node_metadata`. | Persisted selection snapshot loaded by sync pipeline. |
| `NodeSelectionResponse` | `source_connection_id`, `selections_count`, `sync_job_id`, message. | Selection triggers a sync job. |

Important implication: because the selection request carries only IDs, the parser must reconstruct all metadata required by targeted sync. Do not rely only on `BrowseNode.node_metadata` unless the selection API is changed to submit it.

## API and service flow

Browse tree endpoints are source-connection scoped:

- `GET /{source_connection_id}/browse-tree/selections` returns persisted selections.
- `GET /{source_connection_id}/browse-tree?parent_node_id=...` instantiates the source and calls `get_browse_children(parent_node_id)`.
- `POST /{source_connection_id}/browse-tree/select` stores selections and dispatches a sync job.

`BrowseTreeService.get_tree()` creates the source via source lifecycle, checks `supports_browse_tree`, calls the source, and wraps results.

`BrowseTreeService.select_nodes()`:

1. Loads the source connection.
2. Instantiates the source.
3. Checks `supports_browse_tree`.
4. For each submitted node ID, calls `source.parse_browse_node_id(node_id)`.
5. Atomically replaces all existing node selections for the source connection.
6. Dispatches a normal sync job; the sync pipeline later passes persisted node selections into `generate_entities()`.

## SharePoint Online browse tree encoding

SharePoint Online is the main implemented browse-tree connector in the inspected evidence.

| Browse level | Emitted `source_node_id` | `node_type` | Required parser metadata | Targeted sync use |
| --- | --- | --- | --- | --- |
| Site | `site:{site_id}` | `site` | `site_id` | Syncs site entity and all drives if no more specific drive selection exists for that site. |
| Drive | `drive:{site_id}|{drive_id}` | `drive` | `site_id`, `drive_id` | Syncs the selected drive. |
| Folder | `folder:{drive_id}|{folder_id}` | `folder` | `drive_id`, `folder_id` | Recursively syncs files under the folder. |
| File | `file:{drive_id}|{item_id}` | `file` | `drive_id`, `item_id` | Fetches and syncs exactly that file. |

The source currently documents parser conventions for site, drive, and folder IDs. It also emits file nodes and targeted sync expects file metadata. If a file selection stores only raw metadata, targeted file sync can skip the item because `drive_id` and `item_id` are absent. When diagnosing a file-selection bug, compare `get_browse_children()` file IDs with `parse_browse_node_id()` coverage before blaming Microsoft Graph or the UI.

## SharePoint Online browse flow

Root browse (`parent_node_id is None`):

- Delegated source discovers explicit `site_url` values or searches accessible sites.
- App-only source resolves configured `site_url` or enumerates all sites via app permissions.
- Each site node includes site ID and web URL metadata and has children.

Site node browse:

- Parses `site:{site_id}`.
- Lists document library drives for the site.
- Emits `drive:{site_id}|{drive_id}` nodes with `drive_type` metadata.

Drive/folder browse:

- `drive:{site_id}|{drive_id}` lists root drive children.
- `folder:{drive_id}|{folder_id}` lists immediate children only.
- Folders become child nodes with `childCount`; files become leaf nodes with `mime_type`, size, drive ID, and item ID metadata.
- The source caps browse children at `BROWSE_TREE_MAX_ITEMS = 500` per folder load.

## SharePoint Online targeted sync behavior

`generate_entities(..., node_selections=...)` runs `_targeted_sync()` before cursor full/incremental decisions when selections are present.

Targeted sync behavior:

- Site selections add the site entity and, when no specific drive selection exists for that site, walk all drives under the site.
- Drive selections call `_sync_drive(...)` for the selected drive.
- Folder selections call `_sync_folder_recursive(...)` for recursive file sync under a folder.
- File selections fetch the single drive item, get item permissions, optionally translate sharing links through the SharePoint unique ID, resolve viewers, optionally download content, and yield one file entity.
- Targeted sync logs `TARGETED` and still emits ACL/group tracking for yielded entities.

Cursor implications:

- Targeted sync bypasses the normal full-vs-incremental decision.
- Do not update broad full-sync cursor state from a small targeted selection unless the source deliberately records selection-specific cursor data.
- For SharePoint Online, normal full sync records drive delta tokens and tracked groups; incremental sync uses those tokens when no node selections exist.

## Browse tree troubleshooting checklist

1. Confirm the source metadata exposes `supports_browse_tree=True` through `/sources/{short_name}`.
2. Confirm the source connection can be instantiated; browse tree goes through source lifecycle and calls `validate()`.
3. Reproduce the failing browse level with exact `parent_node_id`. Malformed `drive:` and `folder:` IDs should raise clear `ValueError` messages.
4. Compare emitted IDs with parser output. The parser must return the same `node_type` and metadata names consumed by targeted sync.
5. Check selection persistence: `GET /browse-tree/selections` should show the decoded metadata that `generate_entities()` expects.
6. Check targeted sync job creation and status. Selection dispatches a normal sync job; failures may appear as sync failures, not browse endpoint failures.
7. For SharePoint Online, separate Graph permissions from SharePoint REST token issues. Browse tree needs Graph site/drive/item access; SP site-group expansion needs SharePoint-scoped tokens later during ACL membership extraction.

## Reference-only manual artifact

The source inventory identified the SharePoint browse-tree manual test as valuable evidence but not safe to bundle. It requires real Microsoft tenant credentials, real source connections, and external SharePoint/AD state, so keep it as a reference-only troubleshooting pattern rather than a default helper script.
