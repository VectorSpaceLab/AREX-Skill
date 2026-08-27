# Knowledge and RAG Workflows

## Ingestion pipeline

A file upload ultimately follows this shape:

```text
API/domain service -> KnowledgeFile status -> MinIO object -> knowledge_celery task -> loader -> transformers -> Milvus dense vectors + Elasticsearch sparse index -> preview/cache/status update
```

Important paths:

- API/domain: `src/backend/bisheng/knowledge/api/` and `knowledge/domain/services/`.
- Models: `knowledge/domain/models/knowledge.py`, `knowledge_file.py`, and related DAO/repository files.
- Pipeline: `knowledge/rag/base_file_pipeline.py`, `knowledge_file_pipeline.py`, `pipeline/base.py`, `pipeline/loader/`, `pipeline/transformer/`.
- Vector/search factories: `knowledge/rag/milvus_factory.py`, `elasticsearch_factory.py`, `knowledge/domain/knowledge_rag.py`.
- Workers: `worker/knowledge/file_worker.py`, `qa.py`, `rebuild_knowledge_worker.py`.

## Parser provider workflow

PDF and image parsing is selected from knowledge config:

- `etl4lm`: external service, default-style provider, longer timeout.
- `mineru`: external parser service with headers/request kwargs.
- `paddle_ocr`: OCR-oriented service with token support.
- local fallback: local PDF parsing; image OCR without a configured parser is not equivalent.

Use the bundled checker for key presence in YAML-like configs:

```bash
python scripts/check_knowledge_config.py --config <bisheng-checkout>/docker/bisheng/config/config.yaml
```

The checker does not validate credentials or connect to services.

## Transform workflow

The normal document transform chain includes:

1. summary extraction, optionally skipped by config/parameters;
2. embedded image or extra-file handling to MinIO;
3. thumbnail generation when requested;
4. text splitting with chunk size, overlap, separators, pages, bbox, and metadata;
5. preview cache writes.

Excel/CSV-style files have a specialized path that can skip image/thumbnail/splitter assumptions because row/table logic happens in the loader.

## Retrieval workflow

BiSheng uses dual recall:

- Milvus stores dense embedding vectors by knowledge collection.
- Elasticsearch stores sparse/BM25 text and metadata by index.
- `bisheng_langchain/rag/` supplies retrievers such as keyword, baseline vector, mixed, smaller-chunks, and ensemble retrievers.
- Knowledge and space permissions can filter what reaches retrieval or list APIs; route authorization correctness to `identity-permissions-tenancy`.

## Worker workflow

Knowledge workers use the `knowledge_celery` queue. Common tasks include parsing, retrying, deleting, copying, and rebuilding knowledge files.

Safe command template from `src/backend/`:

```bash
uv run celery -A bisheng.worker.main worker -l info -c 20 -P threads -Q knowledge_celery -n knowledge@%h
```

Do not run a full worker as a simple validation if the task only changes a parser utility or schema. Prefer focused tests.

## Test selection

From `src/backend/`:

```bash
uv run pytest test/knowledge/test_file_encoding_transformer.py -q
uv run pytest test/knowledge/test_knowledge_file_metadata.py -q
uv run pytest test/knowledge/rag/test_pptx_parser.py -q
uv run pytest test/knowledge/test_knowledge_space_service.py -q
uv run pytest test/knowledge/test_v2_filelib_unified.py -q
```

Select tests by changed layer: parser tests for loader/transformer changes, DAO/service tests for metadata and space behavior, worker tests for Celery dispatch/status behavior.
