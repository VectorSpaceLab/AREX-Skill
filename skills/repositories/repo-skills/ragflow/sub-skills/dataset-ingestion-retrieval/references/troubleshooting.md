# Troubleshooting Dataset Ingestion and Retrieval

## Parser Config and Chunk Method Mismatch

Symptoms:

- Dataset or document update rejects `chunk_method`.
- Parsing starts but fails before chunks are generated.
- UI shows one parser but task rows use another parser id.
- New chunk method works in one endpoint but not another.

Checks:

1. Confirm public `chunk_method` is accepted by both dataset and document validation if the change touches both.
2. Confirm internal `parser_id` maps to a parser module in the task executor parser factory.
3. Confirm `parser_config` defaults exist for the method or that the method tolerates only base defaults.
4. Confirm `parent_child` is flattened into `children_delimiter` and `enable_children` when needed.
5. Confirm file-type guards are satisfied: visual files usually require `picture`; presentations require `presentation`.
6. Run `scripts/inspect_parser_config.py --chunk-method METHOD --config parser_config.json` on the intended config.

Fix patterns:

- Add missing validation and parser factory entries together.
- Keep default `raptor`/`graphrag` flags explicit for methods that should not use auxiliary indexes.
- Do not silently ignore unknown config keys unless the endpoint intentionally allows extension.

## Missing Embedding Model or Vector Size

Symptoms:

- Task fails with embedding model binding errors.
- Retrieval returns no chunks after reembedding or model change.
- Search errors mention vector dimensions or a missing `q_*_vec` field.

Checks:

1. Confirm the dataset has a valid embedding model id.
2. Confirm all selected datasets in a retrieval request use the same embedding model family/name where required.
3. Confirm the document engine index was created with the current vector size.
4. Confirm chunks contain `q_{dimension}_vec` fields matching the active embedding model.
5. Confirm manually added chunks re-embed content and update document counters.

Fix patterns:

- Use embedding check/reembedding routes when changing dataset embedding configuration.
- Delete/reparse or reembed stale chunks when switching embedding model dimensions.
- Avoid mixing datasets with incompatible embedding spaces in one retrieval call.

## Document Engine Index Missing or Stale

Symptoms:

- Documents show `DONE`, but retrieval returns no chunks.
- Listing chunks returns zero despite nonzero document counters.
- Error says no chunk found or doc engine index not found.

Checks:

1. Confirm document engine index exists for the tenant and dataset.
2. Confirm rows exist for the expected `doc_id` and `kb_id`.
3. Confirm parse/reparse did not delete rows and fail before reinsertion.
4. Confirm cancellation cleanup did not remove rows while the document row stayed stale.
5. Confirm public response fields are not hiding internal rows because of remapping/filtering.

Fix patterns:

- Reparse the document after clearing old task rows and stale document-engine rows.
- Keep document counters synchronized with insert/delete operations.
- In retrieval, prune chunks whose DB document rows no longer exist, but fix delete paths separately.

## Task Stuck, Cancelled, or Failing

Symptoms:

- Document remains `RUNNING` or `CANCEL`.
- Progress logs stop after chunking, embedding, or indexing.
- Cancellation request succeeds but worker continues.

Checks:

1. Inspect task status, document `run`, `progress`, and `progress_msg`.
2. Confirm workers can read queue messages and storage files.
3. Check whether a task is standard, dataflow, RAPTOR, GraphRAG, memory, or placeholder route.
4. Confirm cancellation is checked in the route being executed.
5. Confirm document engine cleanup did not leave inconsistent counters.

Fix patterns:

- Cancel through the document/chunk stop route for document parsing.
- For GraphRAG/RAPTOR, use index delete/cancel route with the desired `wipe` setting.
- Reset document state and requeue only after understanding whether old chunks should be deleted.

## Redis or NATS Queue Issues

Symptoms:

- Tasks never start.
- GraphRAG locks or phase markers behave inconsistently.
- Progress callbacks fail or logs disappear.
- RAPTOR/GraphRAG jobs pile up behind other indexing jobs.

Checks:

1. Confirm task queue backend is reachable and workers are subscribed.
2. Confirm Redis is reachable for progress logs, GraphRAG locks, checkpoints, phase markers, and LLM cache.
3. Confirm queue payloads include `id`, `tenant_id`, `kb_id`, `doc_id`, `parser_id`, `parser_config`, and `kb_parser_config`.
4. Confirm locks use bounded timeouts and do not mask an active task.

Fix patterns:

- Treat Redis checkpoint/phase marker failures as optimization failures unless code explicitly depends on them.
- Do not clear GraphRAG locks or checkpoints blindly; first verify no active task owns them.
- Keep task retry/cancel behavior separate from artifact wipe behavior.

## Metadata Filter Shape Problems

Symptoms:

- Retrieval works without metadata filters but returns zero with filters.
- Document listing rejects `metadata_condition` as invalid JSON or non-object.
- Filtered retrieval returns chunks from unexpected documents.

Checks:

1. Confirm the request uses the right field for the endpoint: `metadata_condition` vs `meta_data_filter`.
2. Confirm `metadata_condition` is an object with `logic` and `conditions`, not a JSON string unless the endpoint explicitly expects a query-string JSON value.
3. Confirm metadata exists at document level, not only inside chunk content.
4. Confirm condition operators match supported forms and values have compatible types.
5. Confirm empty filtered document ids should produce zero results.

Fix patterns:

- Convert wrapper filter formats to canonical metadata conditions once at the service boundary.
- Keep document metadata update APIs and retrieval filter conversion in sync.
- Test both inclusion and exclusion cases.

## Retrieval with Empty Dataset IDs or Wrong Weights

Symptoms:

- `/retrieval` returns argument errors.
- Search returns too many irrelevant chunks or none at all.
- Hybrid ranking behaves differently from chat retrieval.

Checks:

1. Public compatibility retrieval requires non-empty `dataset_ids`.
2. `question` is required; empty strings return an empty chunk result in compatibility retrieval.
3. `top_k` must be greater than zero.
4. `highlight` must be boolean or a true/false string in compatibility retrieval.
5. `vector_similarity_weight` may be validated differently across endpoints; dataset search models constrain it to 0..1, while some compatibility paths cast directly to float.
6. Similarity thresholds differ by caller; chat defaults can differ from dataset search defaults.

Fix patterns:

- Validate endpoint-specific inputs at the boundary.
- Log vector and full-text weights together when diagnosing rank changes.
- For behavior bugs, compare `/retrieval` with `/datasets/search` using equivalent request fields.

## GraphRAG Locks, Checkpoints, and Resume

Symptoms:

- GraphRAG task says lock acquisition failed or appears stuck in merge/resolution/community phase.
- Re-running GraphRAG skips phases unexpectedly.
- Community or resolution output looks stale after adding documents.

Checks:

1. Confirm `parser_config.graphrag.use_graphrag` is true and the task type is `graphrag`.
2. Confirm GraphRAG method is `light`, `general`, or `ner`.
3. Confirm `entity_types` are not empty for the desired extractor behavior.
4. Confirm Redis checkpoint keys and phase markers are scoped to the dataset and have expected TTL.
5. Confirm phase markers are cleared when new graph content invalidates previous resolution/community results.
6. Confirm the dataset lock is not held by another active task.

Fix patterns:

- Use `wipe=false` when the goal is to resume rather than delete prior graph artifacts.
- Clear phase markers only when graph content changed or the user explicitly wipes graph state.
- Keep checkpoint parsing tolerant; bad checkpoint entries should be logged and skipped rather than crashing a whole run.

## RAPTOR Duplicate or Missing Summary Chunks

Symptoms:

- Retrieval returns repeated RAPTOR summaries.
- RAPTOR task completes with no inserted chunks.
- Switching RAPTOR method leaves old summaries visible.

Checks:

1. Confirm source chunks exist before RAPTOR runs.
2. Confirm `parser_config.raptor.use_raptor` and route defaults are aligned.
3. Confirm scope: file-level vs dataset-level.
4. Confirm `tree_builder` and `clustering_method` match cleanup `keep_method` behavior.
5. Confirm summary ids are deterministic enough to avoid duplicates for identical content/doc ids.
6. Confirm cleanup deletes stale `raptor_kwd` chunks for affected doc ids/fake doc ids.

Fix patterns:

- Cleanup stale RAPTOR chunks when method changes.
- Do not run RAPTOR on empty source chunks.
- Record cleanup counts in progress/log output when possible.

## Dataflow Pipeline Output Problems

Symptoms:

- Pipeline debug works, but real document indexing inserts no chunks.
- Pipeline output is `markdown`, `text`, or `html` but indexing expects `chunks`.
- Pipeline logs show an upstream component error hidden by downstream empty output.

Checks:

1. Inspect pipeline output type: `chunks`, `json`, `markdown`, `text`, `html`, or empty.
2. Confirm the final component output has text-bearing fields.
3. Confirm output chunks are normalized before embedding.
4. Confirm chunks without `q_*_vec` are embedded by the dataflow service.
5. Confirm pipeline operation logs are recorded for real document runs.

Fix patterns:

- Preserve `output_format` values through components.
- Return an explicit empty chunks list for valid empty output rather than malformed data.
- Keep pipeline debug mode from mutating persistent document state.

## Installation Troubleshooting Note

Source-level inspection may work even if a full editable install fails. In RAGFlow 0.26.1, project metadata can reference a top-level `graphrag` package while the actual GraphRAG code is packaged under RAGFlow's internal RAG module namespace. Treat that as an install/package-layout troubleshooting issue, not as evidence that GraphRAG runtime code is absent.
