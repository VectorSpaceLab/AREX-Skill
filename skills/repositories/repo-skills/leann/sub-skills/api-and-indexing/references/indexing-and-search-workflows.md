# Indexing and search workflows

## 1. Select an artifact-safe base path

An LEANN index is a family of sibling files, not one file. Resolve a dedicated
index directory and a file-like base name inside it:

```python
from pathlib import Path

index_dir = Path("run-artifacts") / "candidate-index"
index_dir.mkdir(parents=True, exist_ok=False)  # fail rather than merge
base_path = index_dir / "documents.leann"
```

For production replacement, build in a new sibling staging directory, run a
search and artifact validation, close all searchers, then atomically rename or
switch a pointer to the complete directory. Do not reuse a partially failed
build and do not delete an index parent because a missing-metadata error
suggests cleanup.

## 2. Ordinary text build

```python
from leann import LeannBuilder

builder = LeannBuilder(
    backend_name="hnsw",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
)
builder.add_text(
    "LEANN stores text and backend artifacts as an index family.",
    metadata={"id": "doc-001", "source": "notes", "year": 2025},
)
builder.add_text(
    "Search results preserve the passage metadata dictionary.",
    metadata={"id": "doc-002", "source": "manual", "year": 2024},
)
builder.build_index(str(base_path))
```

`build_index` downloads or calls whatever the chosen embedding provider
requires. For provider and prompt-template selection, route to
[embeddings and chat](../../embeddings-and-chat/SKILL.md). Blank or non-string
chunks are skipped; all-empty input fails.

Use stable, unique metadata IDs. The ID is duplicated as the passage top-level
`id` but remains in metadata when supplied there, which is useful for joining
results back to application records.

## 3. Search and deterministic cleanup

```python
from leann import LeannSearcher

with LeannSearcher(str(base_path)) as searcher:
    results = searcher.search(
        "How are artifacts stored?",
        top_k=5,
        complexity=64,
        beam_width=1,
        prune_ratio=0.0,
        pruning_strategy="global",
    )

for result in results:
    print(result.id, result.score, result.text, result.metadata)
```

Use the searcher constructor for recomputation policy:

```python
with LeannSearcher(
    str(base_path),
    recompute_embeddings=False,
    enable_warmup=False,
    use_daemon=False,
) as searcher:
    results = searcher.search("artifact", top_k=3)
```

`recompute_embeddings=False` does not mean “never compute a query vector.” A
semantic search still computes one directly. It avoids the stored-passage
recompute server path. Pure BM25 (`vector_weight=0.0`) and grep
(`use_grep=True`) avoid query embeddings.

## 4. Precomputed-array build

Use precomputed vectors to avoid document-model work during the build. The
query path must still use a compatible embedding model unless only BM25/grep is
used.

```python
import numpy as np
from leann import LeannBuilder

texts = ["alpha orchard note", "beta compiler note"]
ids = ["alpha", "beta"]
embeddings = np.asarray(
    [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
    dtype=np.float32,
)

builder = LeannBuilder(
    backend_name="hnsw",
    embedding_model="the-model-used-to-create-these-vectors",
    dimensions=embeddings.shape[1],
    is_recompute=False,
    is_compact=False,
)
for passage_id, text in zip(ids, texts, strict=True):
    builder.add_text(text, {"id": passage_id})
builder.build_index_from_arrays(str(base_path), ids, embeddings)
```

Preflight assertions should fail before any artifacts are written:

```python
assert embeddings.ndim == 2
assert embeddings.dtype == np.float32
assert embeddings.flags.c_contiguous
assert len(ids) == embeddings.shape[0]
assert len(ids) == len(set(map(str, ids)))
```

The high-level builder validates ID count and configured dimensions, but it does
not ensure buffered passage IDs equal the supplied vector IDs. If these differ,
the backend can return an ID that the passage offset map cannot resolve.

If no text is buffered, placeholders are created. That mode proves backend
plumbing but loses the original text, so it is rarely appropriate for RAG.

Run the bundled [precomputed-index smoke](../scripts/precomputed_index_smoke.py)
for a no-download HNSW build plus pure-BM25 retrieval check. It creates a new
temporary directory by default. Supplying `--output-dir` retains artifacts and
fails if that path already exists.

## 5. Trusted pickle build

```python
import pickle

with open("trusted-embeddings.pkl", "wb") as stream:
    pickle.dump((ids, embeddings), stream)

builder = LeannBuilder(
    backend_name="hnsw",
    embedding_model="the-model-used-to-create-these-vectors",
    dimensions=embeddings.shape[1],
    is_recompute=False,
    is_compact=False,
)
for passage_id, text in zip(ids, texts, strict=True):
    builder.add_text(text, {"id": passage_id})
builder.build_index_from_embeddings(str(base_path), "trusted-embeddings.pkl")
```

Only load a pickle created by a trusted party; pickle can execute code while
loading. Prefer arrays already in memory when possible.

## 6. Low-level `update_index`

Before updating, read `<base>.meta.json` and verify:

- `backend_name` matches the new builder;
- embedding model, mode, options, and dimensions are unchanged;
- HNSW `is_compact` is false for append;
- passage IDs to add are not already live;
- the complete index directory is backed up or staged for critical data.

The update builder only contains the delta:

```python
updater = LeannBuilder(
    backend_name="ivf",
    embedding_model=stored_model,
    embedding_mode=stored_mode,
    dimensions=stored_dimensions,
    **stored_compatible_backend_options,
)
updater.add_text("replacement text", {"id": "doc-017"})
updater.update_index(str(base_path), remove_passage_ids=["doc-017"])
```

### Backend semantics

| Existing index | Low-level API behavior |
| --- | --- |
| IVF add | Embeds valid new chunks, preserves their explicit IDs, calls IVF `add_vectors`, appends passages, and updates offsets/metadata. |
| IVF remove or replace | Calls IVF `remove_ids`, removes IDs from the offset map, compacts JSONL, then optionally adds replacements. Missing requested IDs produce a warning when fewer are removed. |
| Non-compact HNSW add | Appends valid chunks and vectors. IDs are reassigned sequentially from backend `ntotal`; caller-supplied IDs are not preserved by this path. |
| Compact HNSW | Raises `ValueError` because in-place update is unsupported. Rebuild the full corpus. |
| HNSW remove | Not implemented by `update_index`. Do not pass removal IDs and assume deletion occurred. Rebuild the complete corpus. |
| Other backend | No low-level update branch is implemented by this method. Use a full staged rebuild unless that backend's documented API says otherwise. |

IVF modifications should be remove-then-add with the same stable ID. Passage
JSONL is compacted so stale rows do not accumulate. Repeating a modification
must leave JSONL IDs equal to the live offset-map IDs.

Non-compact HNSW is add-only at this API layer. If documents were modified or
removed, reload and rebuild the **entire** corpus; rebuilding only changed
content silently drops unchanged passages. CLI document synchronization makes
higher-level decisions and belongs to [CLI operations](../../cli-operations/SKILL.md).
Backend storage choices belong to
[backends and storage](../../backends-and-storage/SKILL.md).

`update_index` computes new embeddings itself. A model/configuration mismatch
can fail dimensions checks or, worse, produce same-width vectors in an
incompatible space. Persist and reuse the original embedding configuration.

### Update verification

After closing the updater:

1. Reopen a fresh searcher with the same base path.
2. Search a unique phrase from every added/replaced record.
3. Confirm removed phrases are absent for IVF.
4. Load passage JSONL as JSON lines; reject malformed or duplicate IDs.
5. Load the trusted local offset map and confirm each live ID resolves to a row
   with the same ID.
6. Compare metadata passage count and backend count when exposed.
7. Keep the previous complete index until these checks pass.

## 7. Artifact relocation

Metadata records passage paths relative to its own directory, with compatibility
fallbacks. Moving the **whole directory** therefore remains portable. Moving
only `.meta.json`, only `.index`, or only passage files breaks lookup. Never
edit artifact paths blindly; validate JSON, preserve the original, and reopen a
fresh searcher after any deliberate relocation.
