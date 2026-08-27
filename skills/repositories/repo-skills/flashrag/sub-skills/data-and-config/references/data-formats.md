# Data Formats

FlashRAG commonly uses JSONL files for both evaluation datasets and retrieval corpora. Validate the intended role of each file before routing to indexing or pipeline execution because the schemas overlap but are not interchangeable.

## Evaluation dataset JSONL

Each line is one evaluation item. The core fields are:

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `id` | Recommended | string or number | Used for traceability. FlashRAG `Item.id` defaults to `None` if absent, but missing ids make debugging harder. |
| `question` | Yes | string | Main input query. Empty strings should be treated as invalid for evaluation. |
| `golden_answers` | Yes | list of strings | Ground-truth answers for metrics and checks. Empty lists are usually invalid for supervised evaluation. |
| `choices` | Optional | list | Multiple-choice style data. Defaults to an empty list in `Item`. |
| `metadata` | Optional | object | Extra source/task fields. Defaults to an empty object in `Item`. |
| `output` | Optional | object | Runtime outputs. Defaults to an empty object in `Item`; do not prefill unless resuming or testing output handling. |

Tiny fixture:

```jsonl
{"id":"test_0","question":"who got the first nobel prize in physics","golden_answers":["Wilhelm Conrad Röntgen"]}
{"id":"test_1","question":"which mode is used for short wave broadcast service","golden_answers":["Olivia","MFSK"]}
```

## Retrieval corpus JSONL

Each line is one document for indexing or retrieval. The common fields are:

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `id` | Yes | string or number | Unique document identifier. Some downstream retrieval outputs may expose this as `doc_id`. |
| `contents` | Yes | string | Text body used for retrieval. It can include title plus body separated by a newline. |
| `title` | Optional | string | Human-readable title; often duplicated at the start of `contents` in examples. |
| Other metadata | Optional | any JSON value | Keep serializable and stable. |

Tiny fixture:

```jsonl
{"id":0,"title":"What is Artificial Intelligence?","contents":"What is Artificial Intelligence?\nArtificial Intelligence refers to computer systems that perform tasks requiring human intelligence."}
{"id":1,"title":"What is Machine Learning?","contents":"What is Machine Learning?\nMachine Learning is a subset of Artificial Intelligence focused on learning from data."}
```

## Do not mix roles

A file is suspicious if rows contain both evaluation-only fields and corpus-only fields. Examples:

- `question` plus `contents` in the same row.
- `golden_answers` present in a corpus file.
- `contents` present in an evaluation dataset row without a clear custom pipeline reason.
- Empty `golden_answers` in an evaluation file.
- Missing `id` or `contents` in a corpus file.

When in doubt, validate twice with explicit roles: once as `--eval-jsonl` and once as `--corpus-jsonl`. The validator reports role-specific failures.

## `Item` and `Dataset` concepts

`Item` wraps one row and exposes common fields as attributes: `id`, `question`, `golden_answers`, `choices`, `metadata`, and `output`. Unknown attributes are read from `output` first and then the original data dict. Setting an unknown attribute writes into `output`.

`Dataset` wraps a list of `Item` objects. It can load JSONL/JSON line-by-line, parquet files through Hugging Face datasets, or a provided in-memory list. Sampling uses `sample_num` and `random_sample` after loading.

## Save behavior

`Dataset.save(save_path)` writes a single JSON array, not JSONL. That means a saved dataset may not be reloadable by code expecting one JSON object per line unless the consuming code accepts JSON arrays. Use explicit JSONL writers for reusable fixtures when agents need to preserve FlashRAG input shape.

## Validation workflow

1. Decide file role: evaluation dataset or retrieval corpus.
2. Confirm every non-empty line is valid JSON object syntax.
3. Check role-specific required fields and types.
4. Check row count, duplicate ids, and empty strings/lists.
5. Keep fixtures tiny for tests, but preserve realistic field names.
6. Route corpus/index follow-up to `retrieval-and-indexing`; route method execution to `pipelines-and-methods`.
