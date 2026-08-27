# Ingestion pipeline troubleshooting

Use this guide when M-flow ingestion, memorization, procedural learning, or custom `Stage` workflows behave unexpectedly.

## Loader and input failures

| Signal | Likely cause | Fix |
| --- | --- | --- |
| `No registered loader can handle: ...` | File extension/MIME pair does not match any registered loader, or optional loader dependency is not installed. | Run `scripts/pipeline_stage_inspector.py --json`; install the missing optional dependency or pass a registered loader in `preferred_loaders`. |
| Preferred loader is silently skipped | Loader name is not in the runtime registry. | Use exact `loader_name` values such as `advanced_pdf_loader`, not informal names such as `pdf`. Put a fallback loader after the preferred one. |
| HTML URL ingests but loses main content | URL was stored as HTML but default priority may not select `beautiful_soup_loader`. | Prefer `beautiful_soup_loader` with extraction rules, then fallback to `unstructured_loader`. |
| Layout-sensitive PDF loses tables | Default priority tries `pypdf_loader` before `advanced_pdf_loader`. | Use `preferred_loaders=[{"advanced_pdf_loader": {"strategy": "hi_res"}}, "pypdf_loader"]`. |
| `Unsupported path scheme` | The stored path reaching loader conversion is not `s3://`, `file://`, or an absolute local path. | For text, pass it as text to `add()`. For files, pass an existing relative path, an absolute path, or a `file://` URI. |
| `Local file access not permitted` | Local-file ingestion is disabled. | Enable local file access in the process environment only if the source is trusted, or copy data into an accepted storage/backend path. |
| Bare binary stream rejected | Public hints include `BinaryIO`, but implementation reliably handles upload-like objects with `.file` and `.filename`. | Save the stream to a named temp file, pass a path, or wrap it like a FastAPI upload object. |
| S3 directory expansion fails | S3 credentials/filesystem are unavailable. | Configure S3 credentials before passing an S3 prefix, or pass individual files from a storage adapter that can be opened. |
| Image/audio file fails during load | Loader needs a configured vision/transcription-capable LLM backend. | Verify LLM provider/model credentials and test a tiny image/audio file before batch ingestion. |

## Content routing and chunking failures

| Signal | Likely cause | Fix |
| --- | --- | --- |
| Transcript split into unnatural fragments | `content_type` defaulted to text or auto-detection did not trigger. | Pass `content_type=ContentType.DIALOG` for chat logs, interviews, meetings, scripts, and support calls. |
| Article/code misdetected as dialog | `MFLOW_AUTO_DETECT_DIALOG` is enabled and colon-heavy lines look like speakers. | Set `MFLOW_AUTO_DETECT_DIALOG=false` and pass `ContentType.TEXT`. |
| Mixed article + transcript produces poor episodes | One `content_type` was applied to heterogeneous content. | Split into separate `add()`/`memorize()` calls or separate datasets per content type. |
| Very large or vague episodes | Chunks are too large or content routing is disabled. | Lower `chunk_size`, enable content routing, and use `ContentType.DIALOG` for transcript-like inputs. |
| Excessive LLM cost or rate limits | `precise_mode`, procedural extraction, content routing, high `chunks_per_batch`, or image/audio loaders increase LLM calls. | Disable optional layers, lower `chunks_per_batch`, reduce `items_per_batch`, or stage data with `add()` first. |
| `precise_mode` still loses structure | Loader flattened tables/layout before memorization. | Fix extraction first: prefer `advanced_pdf_loader` or `beautiful_soup_loader` with rules before tuning memorization. |

## Memorize and concurrency failures

| Signal | Meaning | Fix |
| --- | --- | --- |
| `ConcurrentMemorizeError` | Another in-process `memorize()` run is active for the same dataset and `conflict_mode="error"`. | Wait for the active run or use a different dataset. Do not switch to `ignore` unless duplicate graph writes are acceptable. |
| Warning about concurrent processing | Same dataset is already being memorized and `conflict_mode="warn"`. | Treat as a data-consistency warning. Prefer `conflict_mode="error"` for production jobs. |
| `ingest()` returns `MEMORIZE_FAILED` | `add()` succeeded, but graph/vector/LLM extraction failed. | Do not re-add data blindly. Retry `memorize(datasets=[result.dataset_name], ...)` after fixing backend/config. |
| `ingest(skip_memorize=True)` data is not queryable | Data was staged only in relational/file storage. | Run `memorize()` for the dataset. |
| Background run returns before data is searchable | `run_in_background=True` schedules work and returns early. | Poll run status/logs through the service surfaces owned by service integrations; avoid immediate search assertions. |
| Re-running memorize duplicates or reprocesses too much | `incremental_loading=False`, disabled cache, or concurrent runs. | Keep `incremental_loading=True` for normal incremental ingestion; use `enable_cache=False` only for intentional rebuilds. |

## Procedural memory and `learn()` failures

| Signal | Likely cause | Fix |
| --- | --- | --- |
| `learn()` reports no episodes found | Episodic memory has not been built, dataset selection did not match, or all Episodes already have derived procedures. | Run `memorize(enable_episodic=True)` first; omit `episode_ids` for duplicate-preventing dataset-wide learning. |
| `learn(run_in_background=True)` still blocks | Current implementation warns and runs synchronously to create derived edges after persistence. | Treat `learn()` as synchronous. If background behavior is mandatory, use a service-level worker/job wrapper outside the core API. |
| Procedures are duplicated for explicit IDs | Passing `episode_ids` bypasses the dataset-wide query that skips already-derived Episodes. | Before calling with explicit IDs, query/check for existing `derived_procedure` edges or omit `episode_ids`. |
| No procedures generated | Source episodes may be factual rather than procedural, or classifier confidence is too low. | Use procedural-rich inputs: workflows, runbooks, preferences, decision policies, playbooks, troubleshooting steps. |
| Procedures lack source traceability | Derived edges failed or source refs were not produced. | Inspect `learn()` summary for `edges_created`; rerun after graph backend errors are fixed. |

## Custom `Stage` / `run_custom_pipeline()` failures

| Signal | Likely cause | Fix |
| --- | --- | --- |
| `TypeError: Expected a callable` | `Stage()` received a non-callable. | Wrap an actual function/coroutine/generator. Prefer `Stage` instances over string task identifiers unless a task registry is known. |
| Stage argument mismatch | `Stage` appends default positional args after runtime pipeline inputs. | Match callable signatures to the previous stage output. For `ingest_data`, use `Stage(ingest_data, dataset_name, user, ...)` so runtime data is first. |
| Next stage receives nested lists or wrong shape | A custom stage returned a shape incompatible with the next stage. | Add a tiny local unit test around the custom stage. Normalize single item vs list explicitly. |
| Generator stage emits tiny batches | Default `batch_size` is 1. | Use `Stage(fn, task_config={"batch_size": N})`. |
| Custom pipeline unexpectedly reuses old results | Cache/incremental flags differ from intent. | For ad-hoc custom pipelines, default `run_custom_pipeline(enable_cache=False, incremental_loading=False)` is usually safest; enable each only intentionally. |
| Pipeline writes to wrong dataset | `dataset` passed to `run_custom_pipeline()` and dataset name passed as `Stage` default diverge. | Keep dataset names/UUIDs consistent across `run_custom_pipeline(dataset=...)` and stages like `ingest_data`. |

## Safe debugging sequence

1. Run the inspector script to confirm installed signatures and loader registry:

   ```bash
   python sub-skills/ingestion-pipelines/scripts/pipeline_stage_inspector.py --json
   ```

2. Add one tiny plain-text item to a disposable dataset.
3. Memorize it with explicit `content_type` and `conflict_mode="error"`.
4. Add one representative file/URL with explicit `preferred_loaders`.
5. Scale `items_per_batch`, `chunks_per_batch`, procedural extraction, and background execution only after the small run succeeds.
