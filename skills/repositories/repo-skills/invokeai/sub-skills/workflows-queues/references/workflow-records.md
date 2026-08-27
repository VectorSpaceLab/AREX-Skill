# Workflow Records

InvokeAI stores workflow library entries as JSON workflow documents plus record metadata. The JSON itself is deliberately loose for frontend workflow editor compatibility; storage and API code enforce ownership, category, timestamps, search fields, and thumbnail behavior around it.

## Workflow JSON Contract

A workflow document should contain:

- `id`: present for stored/default workflows; omitted when creating user workflows through the API body model.
- `name`, `author`, `description`, `version`, `contact`, `tags`, `notes`: string metadata; `tags` is a comma-separated string, not a list.
- `exposedFields`: list of `{nodeId, fieldName}` records used by the UI to expose editable node fields.
- `meta`: object with `version` as a semver string and `category` as `user` or `default`.
- `nodes`, `edges`: loose frontend workflow graph arrays; nodes usually carry ReactFlow-style `id`, `type`, `data`, and `position` fields, while invocation node details live under `data`.
- `form`: optional object; older workflows may omit it and the frontend fills a default.

`WorkflowWithoutID` ignores extra keys. This matters when reading browser-exported workflow JSON: additional UI fields may survive on disk but are not part of the server-side DTO.

## Record DTOs

The workflow library record wraps the workflow JSON with database metadata:

- `workflow_id`: primary ID; equals workflow JSON `id` after storage.
- `created_at`, `updated_at`, `opened_at`: record timestamps. `opened_at` can be null on newer migrations and is updated by the dedicated open endpoint, not by plain `GET`.
- `user_id`: owner. Single-user and migrated records commonly use `system`.
- `is_public`: whether other users may view the workflow in multiuser mode.
- List views also expose `description`, `category`, `tags`, and optional `thumbnail_url`.

Generated SQL columns extract `category`, `name`, `description`, and `tags` from the JSON for filtering and ordering. If those JSON fields are malformed or missing, storage/search failures tend to surface as database or pydantic validation errors.

## Storage Semantics

User workflows and default workflows have different mutation paths:

- `create(workflow, user_id, is_public)` only accepts `meta.category == user`; it assigns a fresh UUID workflow ID and stores the workflow JSON.
- `update(workflow, user_id=None)` only updates `category == user`. Passing `user_id` scopes the write to the owner as defense in depth.
- `delete(workflow_id, user_id=None)` refuses default workflows and scopes by owner when `user_id` is provided.
- `update_is_public(workflow_id, is_public, user_id=None)` updates sharing and manages the comma-separated `shared` tag automatically.
- `get_many(...)` filters by categories, tags, query text, opened state, `user_id`, and `is_public`; if a `user_id` filter is present, default workflows are still included.
- `counts_by_category`, `counts_by_tag`, and `get_all_tags` follow the same category/user/public filtering model.

Default workflow sync bypasses the public create/update/delete guards so startup can replace bundled defaults directly.

## API Behavior

Workflow endpoints live under `/api/v1/workflows` in the running app:

- `GET /` lists paginated workflow records; supports `page`, `per_page`, `order_by`, `direction`, `categories`, `tags`, `query`, `has_been_opened`, and `is_public`.
- `POST /` creates a user workflow from body `{workflow: ...}`. Single-user mode creates `system`-owned public records; multiuser mode creates private records owned by the current user.
- `GET /i/{workflow_id}` returns one workflow plus `thumbnail_url`; multiuser mode allows default workflows, owners, public workflows, and admins.
- `PATCH /i/{workflow_id}` updates a user workflow; non-admins may update only their own records.
- `DELETE /i/{workflow_id}` deletes a user workflow and best-effort deletes its thumbnail; non-admins may delete only their own records.
- `PATCH /i/{workflow_id}/is_public` toggles public sharing; owner/admin only.
- `PUT /i/{workflow_id}/opened_at` marks the record opened; owner/admin only in multiuser mode.
- `GET /tags`, `GET /counts_by_tag`, and `GET /counts_by_category` expose library aggregate helpers.
- `PUT`, `DELETE`, and `GET /i/{workflow_id}/thumbnail` manage thumbnail images. Thumbnail reads are intentionally unauthenticated because browsers load them with plain image tags; workflow UUID unguessability is the protection.

## Multiuser Rules

- Private user workflows are visible only to the owner and admins.
- Public user workflows appear to other users when they request shared/public listings, but still appear in the owner’s normal list.
- System-owned public legacy workflows appear in shared listings and admin listings, not in a regular user’s personal user-workflow listing.
- Regular users cannot update or delete system-owned workflows even if public; admins can.
- Default workflows are visible regardless of owner scoping because `category == default` is included with user filters.

## Thumbnail Rules

Thumbnail upload accepts only content types beginning with `image`. The handler reads the upload, attempts to parse it with Pillow, and returns:

- `404` if the workflow record does not exist.
- `403` if a non-owner non-admin attempts mutation in multiuser mode.
- `415` for non-image content type or unreadable image bytes.
- `500` for lower-level thumbnail save/delete service errors.

Deleting a workflow tolerates a missing thumbnail file, but explicit thumbnail delete surfaces service `ValueError` as `500`.

## Practical Editing Guidance

When editing workflow records or diagnosing API failures:

1. Validate `meta.version` as semver and `meta.category` as `user` or `default`.
2. Keep `tags` as a comma-separated string; do not convert to an array.
3. For multiuser bugs, inspect both the API-level authorization check and the storage call’s `user_id` scoping.
4. For list/count surprises, check the interaction between `categories`, `is_public`, `user_id`, and default-workflow inclusion.
5. For public sharing bugs, verify the automatic `shared` tag add/remove behavior as well as the `is_public` flag.
6. For thumbnails, distinguish unauthenticated `GET` from owner/admin mutation endpoints.