# Session Queue And Batches

InvokeAI queues executable graph sessions, not workflow-library records. A queue enqueue request starts with a `Batch` containing a graph and optional workflow metadata; the service expands batch data into one or more serialized `GraphExecutionState` rows in `session_queue`.

## Batch Payload Contract

The enqueue API accepts a `Batch` body at `/api/v1/queue/{queue_id}/enqueue_batch`:

- `batch_id`: generated when omitted.
- `origin`, `destination`: optional frontend routing hints stored on every queue item.
- `graph`: required invocation `Graph`; validated before enqueue.
- `workflow`: optional `WorkflowWithoutID`; stored with queue items for UI context.
- `runs`: integer `>= 1`; repeats the generated session permutations.
- `data`: optional list of zipped groups. Its shape is `list[list[BatchDatum]]`.

A `BatchDatum` is `{node_path, field_name, items}`. Each item may be a string, number, or image field object like `{image_name: "..."}`. A concrete queue item records the selected values as `field_values`, where each value is a `NodeFieldValue` `{node_path, field_name, value}`.

## Batch Expansion Semantics

Batch expansion has two levels:

1. Inside each inner `data` group, `BatchDatum.items` are zipped together. All item lists in the same group must have equal length.
2. Across inner groups, zipped outputs are combined with a cartesian product.
3. The whole product is repeated `runs` times.
4. Every generated session mutates the same target node fields in a dumped graph dict, assigns a fresh session ID, then serializes a `GraphExecutionState` plus JSON `field_values`.

Examples:

- `data: null` or `data: []` requests `runs` sessions with the original graph.
- One group with two datums of lengths `[3, 3]` requests `3 * runs` sessions.
- Two groups with lengths `[2, 2]` and `[4]` request `8 * runs` sessions.

The service reports both `requested` and `enqueued`; `enqueued` can be lower when the configured max queue size leaves fewer free slots.

## Validation Rules

`Batch` validation catches these before enqueue:

- Zipped length mismatch: every datum in one inner group must have the same `items` length.
- Mixed item types: non-empty `items` in one datum must all share the same type, except `int` and `float` may mix.
- Duplicate node/field mapping: a `(node_path, field_name)` pair may appear only once across the whole `data` collection.
- Unknown node: `graph.get_node(node_path)` must succeed.
- Unknown field: `field_name` must exist in the pydantic model fields for the target invocation node.
- Invalid graph: `graph.validate_self()` must pass.
- Invalid `workflow`: optional workflow metadata must validate as a workflow-without-ID record.

The bundled `scripts/validate_batch_payload.py` performs structural checks for the first four categories and lightweight graph-node/field checks without importing InvokeAI. Use InvokeAI’s own pydantic models or native tests for authoritative node-schema validation.

## Queue Item Model

A `SessionQueueItem` includes:

- Identity and ordering: `item_id`, `queue_id`, `batch_id`, `session_id`, `priority`, `retried_from_item_id`.
- Status: one of `pending`, `in_progress`, `completed`, `failed`, or `canceled`.
- `status_sequence`: monotonically increments for visible status lifecycle changes; older rows may deserialize with a fallback.
- Timing: `created_at`, `updated_at`, `started_at`, `completed_at`.
- Error details: `error_type`, `error_message`, `error_traceback` with backward-compatible alias `error`.
- Ownership: `user_id`, optional `user_display_name`, optional `user_email`.
- Payload: `field_values`, full `session` as `GraphExecutionState`, and optional `workflow`.

Queue rows store `session`, `field_values`, and `workflow` as JSON text. Deserialization manually parses those JSON columns into `GraphExecutionState`, `NodeFieldValue`, and workflow DTOs.

## Status Lifecycle

- On app startup, any `in_progress` row is marked `canceled` and `status_sequence` increments.
- If `clear_queue_on_startup` is enabled, the default queue is cleared.
- If `max_queue_history` is set, terminal rows (`completed`, `failed`, `canceled`) are pruned to keep the most recent N.
- `dequeue()` picks the highest priority pending item, then lowest item ID, marks it `in_progress`, increments `status_sequence`, and emits a status event.
- `complete_queue_item`, `fail_queue_item`, and `cancel_queue_item` update status unless the row is already terminal.
- Bulk cancel paths skip already terminal items and increment `status_sequence` for changed rows.

## Queue API Behavior

Queue endpoints live under `/api/v1/queue/{queue_id}`:

- `POST /enqueue_batch` enqueues generated sessions for the current user; `prepend=true` assigns priority one higher than the current highest pending priority.
- `GET /status` returns queue counts plus processor status. Non-admin callers get user-filtered counts and cannot see another user’s current item identifiers.
- `GET /current`, `GET /next`, `GET /list_all`, `POST /items_by_ids`, and `GET /i/{item_id}` return queue items with per-user sanitization.
- `GET /item_ids` returns ordered item IDs; non-admin callers see only their own item IDs.
- `GET /b/{batch_id}/status` and `GET /counts_by_destination` return counts filtered to the caller’s ownership unless admin.
- `PUT /cancel_all_except_current`, `PUT /delete_all_except_current`, `PUT /cancel_by_batch_ids`, `PUT /cancel_by_destination`, `DELETE /d/{destination}`, `PUT /clear`, `PUT /prune`, `PUT /i/{item_id}/cancel`, and `DELETE /i/{item_id}` scope non-admin effects to owned items.
- `PUT /retry_items_by_id` lets non-admins retry only their own failed/canceled items; retries clone the graph into a new `GraphExecutionState` and preserve `retried_from_item_id` lineage.
- Processor `resume` and `pause` are admin-only.

## Multiuser Redaction

There are two redaction layers:

- Queue-item sanitization: admins and owners see full `SessionQueueItem`. A non-admin viewing another user’s item keeps only non-sensitive identity/status/timestamps; `user_id`, `batch_id`, and `session_id` become `redacted`, user display/email are removed, origin/destination/priority/field values/retry/workflow/errors are removed, and `session` becomes an empty `GraphExecutionState(id="redacted", graph=Graph())`.
- Queue-status current-item redaction: `get_queue_status` uses one `get_current()` snapshot to decide whether to embed `item_id`, `session_id`, and `batch_id`. If the acting user does not own the current item, those identifiers are `None`, while aggregate counts may still be global for service-emitted events.

The event path intentionally separates `user_id` count filtering from `acting_user_id` redaction. This prevents a race where another user’s current item disappears between reads but stale identifiers remain in a status event.

## Clear, Prune, Delete, And Retry Notes

- `clear(queue_id, user_id)` deletes all matching rows; with `user_id=None` it is admin/global.
- Router-level clear first tries to cancel the current item and enforces ownership for non-admins.
- `prune(queue_id, user_id)` deletes terminal rows only.
- `delete_by_destination` cancels a matching current item if authorized, then deletes matching rows.
- `cancel_by_batch_ids` and `cancel_by_destination` separately handle current in-progress items because bulk SQL excludes them.
- Retrying ignores non-terminal rows and inserts new pending rows for failed/canceled rows.

## GraphExecutionState Serialization

Queue code serializes a `GraphExecutionState`, not the frontend workflow JSON. A minimal session has an `id` and a `graph`; runtime execution state can also contain prepared execution graph state, results, executed nodes, errors, source/prepared mappings, and other scheduler fields. When validating queue payloads, do not confuse:

- frontend workflow `nodes`/`edges` arrays under a workflow record, with
- invocation graph `nodes` mapping and graph edges used by `GraphExecutionState`.

For graph construction and authoritative node schemas, route to `workflow-nodes`.