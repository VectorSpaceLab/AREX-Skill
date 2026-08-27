# Runtime data formats reference

## Raw context input model

Capture components create `RawContextProperties` objects before processing. The
fields future agents most often need are:

| Field | Type / values | Meaning |
| --- | --- | --- |
| `source` | `screenshot`, `vault`, `local_file`, `web_link`, `input` | Origin of the raw material. |
| `content_format` | `text`, `image`, `file` | How processors should interpret the payload. |
| `create_time` | datetime | Capture time. |
| `object_id` | UUID string by default | Stable raw-context id. |
| `content_path` | string or null | File path for image/file contexts. |
| `content_text` | string or null | Inline text for input/text contexts. |
| `filter_path` | string or null | Dedup/filter key; web links use URL, folder monitor uses file path. |
| `additional_info` | object | Capture-specific metadata such as file event, screenshot monitor, source URL. |
| `enable_merge` | bool | Whether later context-merger stages may merge the context. |

Create manual local-file context in Python:

```python
from datetime import datetime
from opencontext.models.context import RawContextProperties
from opencontext.models.enums import ContentFormat, ContextSource

raw = RawContextProperties(
    source=ContextSource.LOCAL_FILE,
    content_format=ContentFormat.FILE,
    content_path="/absolute/path/to/note.txt",
    content_text="",
    create_time=datetime.now(),
    filter_path="/absolute/path/to/note.txt",
    additional_info={"event_type": "file_created"},
    enable_merge=False,
)
```

## Processed context model

Processors create `ProcessedContext` objects. The key nested fields are:

| Field | Contents | Operational use |
| --- | --- | --- |
| `id` | UUID string | Used by context detail/delete and storage lookups. |
| `properties.raw_properties` | Source raw contexts | Trace back to file path, URL, screenshot metadata, or vault id. |
| `properties.create_time`, `update_time`, `event_time` | datetimes | Display, filtering, timeline, monitoring. |
| `properties.file_path`, `raw_type`, `raw_id` | optional tracking | Used by document/vault cleanup and status checks. |
| `extracted_data.title` | string | UI title when available. |
| `extracted_data.summary` | string | Main extracted text or summary. |
| `extracted_data.keywords`, `entities` | lists | Search/display metadata. |
| `extracted_data.context_type` | context type enum | Determines vector collection and route filters. |
| `extracted_data.confidence`, `importance` | integer scores | Used by generated content and prioritization. |
| `vectorize.content_format`, `text`, `image_path`, `vector` | embedding source and optional vector | Storage vectorization input. |
| `metadata` | object | Structured metadata such as `knowledge_file_path`, entity profile details, or source-specific annotations. |

API detail responses use a flattened `ProcessedContextModel` with fields such as
`id`, `title`, `summary`, `keywords`, `entities`, `context_type`, `confidence`,
`importance`, `raw_contexts`, `metadata`, and formatted times.

## Context types

These values are valid in vector-search filters, storage collections, and
processed contexts:

| Type | Meaning |
| --- | --- |
| `entity_context` | Entity profiles for people, teams, projects, organizations, aliases, and relationships. |
| `activity_context` | Completed actions, meetings, learning, communication, and historical activity records. |
| `intent_context` | Future plans, goals, priorities, intentions, and action strategies. |
| `semantic_context` | Concepts, principles, architecture, definitions, and reusable knowledge. |
| `procedural_context` | Step-by-step operation flows and learned task procedures. |
| `state_context` | Current status, progress, metrics, risks, and monitoring information. |
| `knowledge_context` | Document/file knowledge chunks; folder/file/document processors primarily create this type. |

## Supported document formats

`DocumentProcessor.get_supported_formats()` was verified to return 17 suffixes:

```text
.pdf .png .jpg .jpeg .gif .bmp .webp .docx .doc .pptx .ppt .xlsx .xls .csv .jsonl .md .txt
```

Processing behavior:

| Format group | Raw source/format | Processor path | Model dependency |
| --- | --- | --- | --- |
| Plain text input | `source=input`, `content_format=text`, `content_text` set | Text chunking into `knowledge_context` | The current chunker attempts semantic LLM chunking for short text and falls back on errors; use the smoke script for deterministic local checks. |
| `.txt` file | `source=local_file`, `content_format=file` | Reads UTF-8 text, chunks, creates `knowledge_context` | Same chunking caveat. |
| Structured files | `.xlsx`, `.xls`, `.csv`, `.jsonl`, `faq*.xlsx` | Structured/FAQ chunkers, then `knowledge_context` | Usually CPU for extraction, but embedding/storage later needs embedding model. |
| Visual documents | `.pdf`, `.docx`, `.doc`, `.pptx`, `.ppt`, images, visual markdown | Page/image conversion plus VLM extraction where needed | Requires VLM credentials for visual/scanned pages. |
| Web links | URL converted to markdown or PDF, then local-file processing | `WebLinkCapture` + `DocumentProcessor` | Requires browser/crawl dependency and network; visual/PDF paths can require VLM. |
| Screenshots | `source=screenshot`, `content_format=image` | `ScreenshotProcessor` dedup, resize, VLM extraction | Requires screenshot file path plus VLM and embedding model for full processing/storage. |

## Folder monitor events

Folder monitoring emits local-file raw contexts for create/update events and
uses deletion events for cleanup only.

| Event | Raw context emitted? | Metadata |
| --- | --- | --- |
| `file_created` | Yes | `additional_info.event_type`, `file_path`, `file_name`, `file_type`, `file_info` with mtime/size/hash. |
| `file_updated` | Yes | Same as create, with updated file hash and timestamps. |
| `file_deleted` | No | Cleans matching `knowledge_context` records whose metadata contains `knowledge_file_path`. |

Only supported suffixes are scanned. Files larger than `max_file_size` are
ignored. `initial_scan: true` caches existing files so the first monitor pass
reports later modifications instead of treating all existing files as new.

## Screenshot metadata

`ScreenshotCapture` saves screenshots when `storage_path` is configured and
emits raw image contexts with metadata including:

- `format`, `timestamp`, `last_seen_timestamp`;
- screenshot library (`mss`), monitor id, and coordinates;
- `screenshot_path` and tag list;
- optional region/format/quality values.

`ScreenshotProcessor` computes perceptual hashes, deduplicates against recent
screenshots, optionally deletes duplicate files, batches VLM extraction, and
creates processed contexts with extracted title/summary/type/importance.

## Web-link capture output

`WebLinkCapture` accepts `http://` or `https://` URLs. In `markdown` mode it
uses `crawl4ai` to write an `.md` file; in `pdf` mode it uses Playwright
Chromium to write a `.pdf` file. A successful conversion returns raw contexts:

```json
{
  "source": "web_link",
  "content_format": "file",
  "content_path": "...generated markdown or PDF...",
  "filter_path": "https://example.com",
  "additional_info": {"url": "https://example.com", "markdown_path": "..."}
}
```

The capture component must be initialized and started before direct
`capture(urls=[...])` calls because the base capture lifecycle refuses captures
when the component is not running.

## Storage layouts

### ChromaDB/Qdrant vector collections

Vector storage creates one collection per context type plus a `todo` collection
for todo deduplication. Documents are stored with flattened extracted data,
properties, metadata, document text, and embedding. ChromaDB local mode persists
under the configured path. Qdrant local/server mode uses Qdrant collections and
converts context UUIDs to deterministic UUID point ids.

### SQLite document database

SQLite creates and migrates these table families:

| Table/family | Purpose |
| --- | --- |
| `vaults` | Notes, reports, default quick-start document, folders. |
| `todo` | Generated and user todo records. |
| `activity` | Activity records. |
| `tips` | Generated tips. |
| `monitoring_token_usage`, `monitoring_stage_timing`, `monitoring_data_stats` | Token, processing, and data metrics. |
| `conversations`, `messages`, `message_thinking` | Agent chat conversation and streaming message persistence. |

Use a fresh `CONTEXT_PATH` for destructive debugging. Do not delete or migrate a
user database without explicit approval and backup guidance.
