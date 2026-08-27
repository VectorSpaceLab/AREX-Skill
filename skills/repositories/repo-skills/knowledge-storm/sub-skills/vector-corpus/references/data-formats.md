# VectorRM data formats

`VectorRM` expects a single CSV where each row is one source document. The vector-store builder embeds chunks derived from each row's `content` field and stores `title`, `url`, and `description` as metadata.

## Required columns

| Column | Required | Meaning | Validation rule |
| --- | --- | --- | --- |
| `content` | yes | Main text to embed and retrieve. | Header must exist; each indexed row should contain non-empty text. |
| `url` | yes | Stable source identifier used by STORM citations and source tracking. | Header must exist; each indexed row should contain a non-empty value; values should be unique per original row. |

## Optional columns

| Column | Required | Meaning | Recommended value |
| --- | --- | --- | --- |
| `title` | no | Human-readable document title shown in retrieved source metadata. | Short title or empty string. |
| `description` | no | Supplemental metadata returned with retrieval results. | Abstract, summary, provenance note, or empty string. |

The package can tolerate missing `title` and `description` columns by using empty/default metadata, but including both columns makes retrieval outputs easier to inspect. If optional cells are missing, normalize them to empty strings before indexing when possible.

## Minimal CSV

```csv
content,url
"I am a document about retrieval-augmented generation.",doc-001
"I am another document about vector search.",doc-002
```

## Full CSV

```csv
content,title,url,description
"I am a document.","Document 1",doc-001,"A self-explanatory document."
"I am another document.","Document 2",doc-002,"Another self-explanatory document."
```

## URL uniqueness

`url` is a source identifier, not necessarily a web URL. It can be a synthetic id such as `doc-0001`, `paper_42`, or `uid_7`. It must be stable enough for STORM to cite retrieved chunks and for the user to trace each chunk back to the original row.

A long row may be split into multiple vector chunks; those chunks intentionally share the row's `url`. The uniqueness requirement applies to original CSV rows. Duplicate row URLs cause ambiguous citations and should be treated as fatal before indexing.

Run:

```bash
python scripts/validate_vector_corpus_csv.py --input-path corpus.csv --strict-unique-url
```

## Chunking and batching fields

`QdrantVectorStoreManager.create_or_update_vector_store` treats each CSV row as a document and then chunks its `content` using a recursive character splitter.

| Parameter | Default | Applies to | Effect |
| --- | --- | --- | --- |
| `chunk_size` / `--chunk-size` | `500` | vector-store creation | Maximum approximate character length per chunk before embedding. Increase for larger context passages; decrease for short, targeted retrieval. |
| `chunk_overlap` / `--chunk-overlap` | `100` | vector-store creation | Overlap between adjacent chunks. Higher overlap preserves context but creates more vectors. |
| `batch_size` / `--embed-batch-size` | `64` | vector-store creation | Number of chunks passed to Qdrant embedding/add operations per batch. Lower it for memory or timeout issues. |

For short rows such as abstracts, defaults are usually sufficient. For long PDFs or reports converted to CSV rows, consider `--chunk-size 800 --chunk-overlap 150`, then validate retrieval quality with a few `VectorRM.forward(...)` queries.

## Accepted vector store locations

| Mode | Required setting | Credential | Typical use |
| --- | --- | --- | --- |
| offline | `--offline-vector-db-dir ./vector_store` | none | Local development, private corpus, reproducible local runs. |
| online | `--online-vector-db-url https://...` | `QDRANT_API_KEY` or `--qdrant-api-key` | Shared Qdrant Cloud/server collection. |

If `--csv-file-path` is present, the helper can create/update the selected collection. If `--csv-file-path` is omitted, the collection must already exist at the selected offline path or online URL.

## Validation symptoms

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ERROR: input path must end with .csv` | File suffix is not `.csv`. | Export the corpus as CSV or rename only after confirming it is actually comma-separated. |
| `ERROR: input path does not exist` | Wrong file path or working directory. | Pass an absolute or correct relative path. |
| `ERROR: missing required column(s): content` | Header does not include exact lowercase `content`. | Rename the text column or pass a converted CSV with the exact schema. |
| `ERROR: missing required column(s): url` | Header does not include exact lowercase `url`. | Add stable document identifiers. |
| `ERROR: row N has empty content` | A row would produce no useful embedding. | Fill or remove the row. |
| `ERROR: row N has empty url` | A row cannot be cited or deduplicated. | Fill with a stable unique id. |
| `WARNING: duplicate url value ...` | Non-strict validation detected repeated row identifiers. | Rerun with `--strict-unique-url` and fix duplicates before indexing. |
| `Not valid file format. Please provide a csv file.` | Package-level vector-store builder rejected a non-CSV path. | Use a `.csv` file and re-run validation. |
| `Content column content not found in the csv file.` | Package-level builder could not find the content column. | Validate the file and use exact column names. |
| `URL column url not found in the csv file.` | Package-level builder could not find the URL column. | Validate the file and use exact column names. |
