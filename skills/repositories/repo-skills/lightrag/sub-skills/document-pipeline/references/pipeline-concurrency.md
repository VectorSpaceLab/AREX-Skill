# Pipeline Concurrency

## Core Principle

LightRAG allows concurrent enqueue plus processing, but prevents enqueue during destructive storage mutation and scan classification. The shared `pipeline_status` dict is workspace-scoped and must be read/written under the workspace `pipeline_status` lock.

`busy=True` alone means a pipeline job is active; it does not mean enqueue must be refused. The exclusive blockers are `destructive_busy` and `scanning_exclusive`.

## Important Fields

| Field | Meaning | Operational consequence |
| --- | --- | --- |
| `busy` | Some pipeline job or destructive job is active. | Processing entry sets it. Enqueue can still be accepted unless an exclusive field is also set. |
| `destructive_busy` | Clear/delete is dropping storages and removing input files. | Enqueue is refused; scan is refused; destructive operation owns the exclusive window. |
| `scanning` | A directory scan task is active for its lifecycle. | A second scan is refused; uploads are not blocked by this flag alone. |
| `scanning_exclusive` | Scan is in classification, reading `doc_status` and deleting stale/retry stubs. | Normal enqueue is refused; scan's own `from_scan=True` enqueue bypasses this guard. |
| `pending_enqueues` | Upload/text requests reserved an enqueue slot but background enqueue has not completed. | Scan reservation refuses while this is greater than zero. |
| `request_pending` | New work arrived while processing was busy. | The processing loop re-queries `doc_status` after the current batch instead of exiting stranded. |
| `cancellation_requested` | Pipeline should stop before/at safe stage boundaries. | Workers raise/short-circuit; final status and messages explain cancellation reason. |
| `cancellation_reason` / `cancellation_detail` | Why cancellation was requested. | `internal_error` indicates a worker-stage failure asked the batch to halt safely. |

## Reservation And Refusal Matrix

| Operation | Refuses if | Writes or side effect |
| --- | --- | --- |
| Enqueue reservation for upload/text | `scanning_exclusive` or `destructive_busy` | `pending_enqueues += 1` while background enqueue is outstanding. |
| `apipeline_enqueue_documents` last-line guard | `scanning_exclusive` when not `from_scan`, or `destructive_busy` | Writes `full_docs` and `doc_status`; nudges `request_pending` if processing is busy. |
| Scan endpoint reservation | `busy`, `scanning`, or `pending_enqueues > 0` | Sets `scanning=True`; later sets `scanning_exclusive=True` during classification. |
| `apipeline_process_enqueue_documents` entry | If already `busy` | Sets `request_pending=True` and returns; otherwise sets `busy=True`. |
| Clear/delete reservation | `busy`, `scanning`, or `pending_enqueues > 0` | Sets `busy=True` and `destructive_busy=True`. |

## Enqueue And Processing Handoff

The enqueue path uses a workspace `enqueue_serialize` lock around dedup/filter/upsert so two concurrent uploads do not both miss the same filename or content-hash duplicate. This lock does not block processing from reading pending docs.

When enqueue writes new pending rows while processing is already busy:

1. Enqueue updates `doc_status` / `full_docs`.
2. Under `pipeline_status` lock, enqueue sets `request_pending=True`.
3. The processing loop finishes the current batch.
4. Before clearing `busy`, the loop checks `request_pending` atomically.
5. If set, it clears `request_pending`, re-queries pending/failed-resumable docs, and continues.

This avoids a stranded state where a document lands just as the current batch is exiting.

## Scan Classification Window

A scan has two phases with different exclusivity:

- During classification, `scanning=True` and `scanning_exclusive=True`; normal upload/text enqueue is refused because scan is reading and mutating classification-related `doc_status` rows.
- After classification, `scanning_exclusive=False` while scan-driven processing continues; concurrent uploads can land and signal `request_pending` for the processing loop.
- Scan's own enqueue calls use `from_scan=True` because the scan already owns `scanning`; this bypass is not a general-purpose upload bypass.

## Destructive Window

Clear and per-document delete set both `busy=True` and `destructive_busy=True`. This is stronger than normal processing because storages and input files may be dropped or removed. Accepting enqueue during this window could write documents into storage being torn down, so both reservation and enqueue last-line guard refuse.

## Interpreting Refusals

When explaining a refused user action, identify the exact field combination:

- Upload refused during scan classification: `scanning_exclusive=True`, regardless of `busy` alone.
- Upload refused during delete/clear: `destructive_busy=True`.
- Scan refused during active upload: `pending_enqueues > 0`.
- Scan refused during processing or destructive work: `busy=True`.
- Delete/clear refused during scan or upload: `scanning=True` or `pending_enqueues > 0`.
- Processing call did not start a new loop: `busy=True`, so it only set `request_pending=True`.

## Cancellation Semantics

Cancellation is cooperative. Workers check `cancellation_requested` at stage boundaries and during long-running parse/analyze/process loops. Internal worker errors can set `cancellation_requested=True` with reason `internal_error` so the batch halts after preserving per-document failure state. A cancelled batch may leave some documents pending or failed for later retry/resume.
