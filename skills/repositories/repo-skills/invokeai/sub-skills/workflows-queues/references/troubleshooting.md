# Troubleshooting Workflows And Queues

Use this guide to map common workflow-library and session-queue symptoms to the right data model, endpoint, and validation layer.

## Batch Validation Failures

### Zipped batch length mismatch

Signal: enqueue fails with `Zipped batch items must all have the same length`.

Check `Batch.data`: every `BatchDatum.items` list inside the same inner group must have the same length. Split independent dimensions into separate inner groups if you need a cartesian product instead of zip semantics.

### Mixed item types

Signal: enqueue fails with `All items in a batch must have the same type`.

Check each `BatchDatum.items` list. Strings, image-field objects, and other object shapes cannot mix. `int` and `float` are the exception and may be mixed as numeric values.

### Duplicate node/field mapping

Signal: enqueue fails with `Each batch data must have unique node_id and field_name`.

Search all groups for repeated `(node_path, field_name)` pairs. The uniqueness rule applies across the entire `data` collection, not just one zipped group.

### Unknown node or field

Signal: enqueue fails with `Node ... not found in graph` or `Field ... not found in node ...`.

Check that `node_path` matches an invocation graph node ID, not a frontend workflow editor node wrapper ID unless those are the same in the converted graph. Check the target field against the invocation model fields. For full node schema questions, route to `workflow-nodes`.

### Too many requested sessions

Signal: `requested` in `EnqueueBatchResult` exceeds `enqueued`, or users report missing queued permutations.

Calculate zipped/cartesian expansion and compare with configured max queue size. `enqueue_batch` caps new items to available queue capacity but still reports the requested count.

## Workflow Access And Listing Bugs

### Private workflow returns 403

In multiuser mode, `GET /workflows/i/{workflow_id}` allows only default workflows, owner workflows, public workflows, or admin users. For update/delete/public-toggle/opened-at/thumbnail mutation, non-admin users must own the record.

### Public workflow missing from another user’s list

Check the listing query. Other users see shared user workflows when `is_public=true` is requested. Without that filter, user-category lists are scoped to the current user. Also check that `update_is_public` succeeded and that the `shared` tag was added.

### System-owned legacy workflow appears in the wrong list

System-owned public user workflows should appear in shared listings and admin listings, but not in a regular user’s personal workflow listing. If this regresses, inspect `list_workflows` user filter selection and storage `get_many` conditions.

### Default workflow cannot be edited or deleted

This is expected. Default workflows are protected by service methods and are updated only by startup sync. Save a user copy for edits.

### `opened_at` filtering seems wrong

`opened_at` can be null on newer databases and is updated by `PUT /workflows/i/{workflow_id}/opened_at`, not automatically by every read. Use `has_been_opened=true/false` filters with that behavior in mind.

## Queue Privacy And Redaction

### Non-owner sees redacted queue item

Expected in multiuser mode. Non-admin non-owners only retain item ID, queue ID, status, and timestamps. User identity, batch/session IDs, origin/destination, field values, workflow, errors, and graph data are stripped.

### Status event leaks another user’s current item identifiers

It should not. Queue status redaction must derive from the same current-item snapshot used to embed `item_id`, `session_id`, and `batch_id`. If a regression appears, inspect `get_queue_status(queue_id, user_id, acting_user_id)` and event emission from status changes.

### Non-admin clear/cancel/delete misses other users’ rows

Expected. Router methods pass the current user ID into service methods for non-admins. Admin calls pass `None` and operate globally.

## Queue History And Lifecycle

### In-progress items become canceled after restart

Expected. Startup marks all `in_progress` queue rows `canceled` because the processor may have been killed mid-item.

### Old terminal history disappears

Check `max_queue_history`. Startup can prune completed/failed/canceled rows to keep only the most recent configured count.

### `status_sequence` does not match expectations

It starts at `0` for pending rows and increments when visible status changes. Dequeue increments to `1`; complete/fail/cancel increments again unless the row is already terminal. Bulk cancel paths also increment changed rows.

### Retry does not create a new item

Only `failed` and `canceled` items are retried. Retrying clones the stored graph into a new `GraphExecutionState`, keeps batch/origin/destination/priority/workflow/field values, and sets `retried_from_item_id` to the original lineage.

## Thumbnail Failures

### Upload returns 415

Either the upload content type does not start with `image`, or Pillow cannot read the bytes. Check both the request headers and the actual file bytes.

### Thumbnail read is unauthenticated

Expected. Browser image tags cannot attach bearer tokens. Thumbnail IDs are workflow UUIDs, so the design relies on unguessability for read access.

### Deleting a workflow with no thumbnail succeeds

Expected. Workflow deletion ignores missing thumbnail files. Explicit thumbnail deletion can still surface thumbnail-service errors.

## Malformed Default Workflow JSON

Use `scripts/inspect_default_workflow.py` first. Common issues:

- Missing `id`, `meta`, `nodes`, `edges`, or `exposedFields`.
- Default ID not starting with `default_`.
- `meta.category` not equal to `default`.
- Non-semver `meta.version`.
- Duplicate node IDs.
- Edge `source` or `target` references unknown nodes.
- Exposed field references an unknown node or a field absent from `node.data.inputs`.
- Tags accidentally written as a list instead of a comma-separated string.
- Model/image/board fields pin local resources that other installations will not have.

## Diagnostic Helpers

- Use `scripts/inspect_default_workflow.py --strict --json workflow.json` for default workflow shape checks.
- Use `scripts/validate_batch_payload.py --json payload.json` for common batch enqueue payload mistakes.
- For authoritative graph and node validation, run InvokeAI’s own pydantic models or native queue/router tests after the runtime skill has been integrated.

## Native Test Candidates

Safe candidates for later verification planning:

- Default workflow JSON validation over the bundled default workflow assets.
- Multiuser workflow router tests covering owner isolation, public sharing, system-owned workflows, and single-user public ownership.
- Queue sanitization tests covering owner/admin/full access versus non-owner redaction.
- Session queue clear/status tests covering user scoping, status sequence increments, and event current-item redaction.