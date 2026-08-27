# SDK Workflow Recipes

Use these self-contained recipes as starting points for DataChain pipeline code.
They avoid original repository examples and use public API patterns only.

## 1. Read Files, Extract Metadata, Save a Dataset

```python
import datachain as dc
from pydantic import BaseModel

class ImageMeta(BaseModel):
    width: int
    height: int

def get_meta(file: dc.ImageFile) -> ImageMeta:
    img = file.read()
    return ImageMeta(width=img.width, height=img.height)

images = (
    dc.read_storage("s3://bucket/images/", type="image", anon=True)
    .settings(parallel=8, prefetch=16)
    .map(meta=get_meta)
    .save(
        "image_metadata",
        attrs=["cast:container", "scope:bucket", "source:images"],
        description="Image dimensions for files in the images bucket prefix.",
    )
)
images.show(5)
```

Rules:

- `read_storage` paths for buckets/prefixes should end in `/`.
- Annotate UDF return types. A Pydantic model becomes a nested DataChain signal.
- Save UDF-bearing stages so later prompts can reuse `dc.read_dataset("image_metadata")`.

## 2. Merge Storage with Sidecar Metadata

```python
import datachain as dc

files = dc.read_storage("gs://bucket/images/", anon=True)
labels = dc.read_csv("gs://bucket/labels.csv", anon=True)

# Metadata-only function: bind to file.path so DataChain does not download bytes.
def basename(path: str) -> str:
    return path.rsplit("/", 1)[-1]

labeled = (
    files
    .map(name=basename, params=["file.path"])
    .merge(labels, on="name", right_on="filename")
    .select_except("labels.filename")
    .save("labeled_images")
)
```

When all transformation logic is column-based, use `mutate`, `filter`, and
`merge` from the Query Engine. Use `map` only when Python logic or file access is
needed.

## 3. Multi-Stage Expensive Pipeline

Split expensive stages into separate saved datasets. Each stage can be rerun,
versioned, checkpointed, and reused.

```python
# stage_1_extract_text.py
import datachain as dc

def read_text(file: dc.TextFile) -> str:
    return file.read()

(
    dc.read_storage("s3://docs/", type="text", anon=True)
    .settings(parallel=8)
    .map(text=read_text)
    .save("docs_text")
)
```

```python
# stage_2_embed_text.py
import datachain as dc
from datachain import llm

(
    dc.read_dataset("docs_text")
    .settings(llm="openai/text-embedding-3-small", parallel=8)
    .map(embedding=llm.embed("text"))
    .save("docs_text_embeddings")
)
```

```python
# stage_3_rank.py
import datachain as dc

query_embedding = [...]  # compute or load once
(
    dc.read_dataset("docs_text_embeddings")
    .mutate(distance=dc.func.cosine_distance("embedding", query_embedding))
    .order_by("distance")
    .limit(20)
    .save("docs_ranked_for_query")
)
```

Do not filter out problem-specific rows before the expensive embed/classify
stage. Save the full expensive result first, then filter downstream.

## 4. Structured Local File Reads and Exports

Use local temporary or project data paths when the task is local and small:

```python
import datachain as dc

rows = dc.read_csv("file://data/labels.csv")
summary = (
    rows
    .group_by(count=dc.func.count(), partition_by="category")
    .order_by("count", descending=True)
)
summary.to_csv("outputs/category_counts.csv")
```

Export choices:

- `to_csv`, `to_json`, `to_jsonl`, `to_parquet`: flat files; nested model leaves
  flatten with dotted names.
- `to_database`: SQL table write with `on_conflict` and `column_mapping` when
  needed.
- `to_storage`: copy file payloads; choose `placement="filepath"` when you need
  to preserve the source directory layout.
- `to_pandas`: only for bounded subsets that fit memory.

## 5. Delta and Retry for Incremental Processing

Use `delta=True` when a source changes incrementally. Use `delta_retry` when
previous output rows with errors or missing rows must be reprocessed.

```python
import datachain as dc

class Result(dc.DataModel):
    content: str
    error: str | None = None

def process(file: dc.TextFile) -> Result:
    try:
        return Result(content=file.read())
    except Exception as exc:  # keep failures visible for delta_retry
        return Result(content="", error=str(exc))

(
    dc.read_storage(
        "s3://bucket/text/",
        type="text",
        update=True,
        delta=True,
        delta_on="file.path",
        delta_compare="file.etag",
        delta_retry="result.error",
    )
    .map(result=process)
    .save("processed_text")
)
```

Do not combine delta casually with `merge`, `union`, `subtract`, `diff`,
`file_diff`, `distinct`, `agg`, or `group_by`; those operations usually need the
full logical dataset. Use `delta_unsafe=True` only when you have reasoned through
consistency for every participating delta source.

## 6. LLM Classification with Usage Accounting

```python
import datachain as dc
from datachain import llm

(
    dc.read_storage("s3://support-tickets/", type="text", anon=True)
    .settings(llm="anthropic/claude-haiku-4-5", parallel=4)
    .map(
        llm.classify(
            "file",
            into=["billing", "bug", "feature", "other"],
            include_usage=True,
        ),
        output={"category": str, "usage": dc.llm.Usage},
    )
    .save("support_ticket_categories")
)
```

Aggregate token usage later with Query Engine sums over nested usage fields. Do
not bake secrets into pipeline code; use environment variables or a callable
`llm_params` setup when credentials must be supplied.

## 7. Optional ML Integration Pattern

Optional ML examples may require package extras and model downloads. Keep them
explicit and separate from the base pipeline:

```bash
pip install 'datachain[torch]'
```

```python
import datachain as dc

# After installing torch extras, DataChain can produce a PyTorch Dataset.
train, test = dc.toolkit.train_test_split(dc.read_dataset("image_metadata"), [0.8, 0.2])
pt_dataset = train.to_pytorch()
```

If `import datachain.torch` fails, install the torch extra or keep the workflow
in base DataChain exports.
