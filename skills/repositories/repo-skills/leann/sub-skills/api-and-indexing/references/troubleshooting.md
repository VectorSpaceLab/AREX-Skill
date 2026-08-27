# API and indexing troubleshooting

Start by recording the exact base path passed to the builder/searcher, listing
its sibling artifacts, reading `.meta.json` as JSON, and checking backend name,
dimensions, embedding configuration, passage sources, `is_compact`, and
`is_pruned`. Do not delete or mutate artifacts during diagnosis.

## Failure matrix

| Symptom | Likely cause | Safe diagnosis and repair |
| --- | --- | --- |
| `Leann metadata file not found at <path>.meta.json` | Passed a `.meta.json`, `.index`, directory, or different base name instead of the build base path; incomplete move; partial build. | Locate the actual `*.meta.json`; remove only its final `.meta.json` suffix to recover the base path. Confirm all siblings. Ignore any broad `rm -rf` suggestion in the exception text; never delete the parent blindly. |
| `Passage index file not found` | `.passages.idx` was omitted, metadata paths were edited, or only part of the family moved. | Move/restore the whole artifact directory. Verify metadata-relative `path`, `index_path`, and matching sibling names. |
| Backend index missing during update | The expected primary `.index` file was not produced, moved, or named from a different base stem. | Compare the base path with the metadata and backend artifacts. Restore a complete known-good family or rebuild in a new directory. |
| Metadata JSON decode error | Truncated or manually edited `.meta.json`. | Restore from backup; otherwise rebuild. Do not guess missing backend configuration. |
| Passage lookup logs `Passage not found` | Backend vector IDs differ from passage IDs, offset map is stale, or JSONL/offset artifacts come from different builds. | For precomputed builds, compare `str(ids[i])` with each buffered passage ID. Verify every offset resolves to a JSON row with the same ID. Rebuild a coherent family rather than editing labels piecemeal. |
| `Mismatch between number of IDs ... and embeddings ...` | `len(ids) != embeddings.shape[0]`. | Validate `(N, D)` and count before calling the builder. Regenerate one aligned batch. |
| Dimension mismatch while building or updating | Configured `dimensions`, stored index width, and new vectors differ; or the update uses another embedding model. | Read stored dimensions/model/options. Regenerate vectors with that exact embedding space or create a new full index. Do not pad/truncate vectors. |
| `No chunks added` | `build_index` called before `add_text`. | Add at least one valid passage. Use `build_index_from_arrays` only when vectors are already available. |
| `All provided chunks are empty or invalid` | Every buffered text is blank or non-string. | Validate and normalize source text before adding it; report dropped record IDs. |
| Precomputed index returns placeholders | `build_index_from_arrays` was called without buffered text. | Rebuild after one aligned `add_text` call per vector. Placeholder mode cannot recover original text. |
| Search returns fewer results than `top_k` | Corpus is smaller, backend returned fewer, passage IDs failed enrichment, or post-search metadata filters removed candidates. | Check corpus size and lookup errors. Disable filters to isolate retrieval, then increase the candidate target if filtering is selective. |
| Filter unexpectedly returns zero | Missing field, nested metadata, unsupported operator, type inconsistency, case mismatch, or list-`in` semantics. | Inspect returned metadata without the filter. Use immediate flat keys and supported operators. Flatten nested/list facets during ingestion. |
| Invalid filter does not raise | Unsupported operators and evaluation errors intentionally fail that result with a warning. | Validate filter structure in application code before calling search; treat unknown operators as input errors. |
| Pure BM25 raises `BM25 scorer failed to initialize` | No readable passages, malformed/empty JSONL, FTS5 unavailable, or the index directory is not writable for on-demand creation. | Validate every nonblank JSONL row, test SQLite FTS5 in the runtime, and make a staged writable copy. Rebuild ordinary text indexes to precreate BM25. |
| Metadata names an FTS5 DB but it is missing | Artifact family was copied incompletely. | Restore the DB or permit one on-demand rebuild from valid passages in a writable complete directory. |
| Hybrid ranking looks dominated by one side | Raw vector and BM25 scores have different scales; fusion does not normalize. | Log IDs/scores from pure vector and pure BM25 runs, tune `vector_weight` on labeled queries, and consider application-side calibrated fusion. |
| Grep says no passages file exists | Grep only discovers `documents.leann.passages.jsonl` in two fixed locations. | Use a build base named `documents.leann` for grep workflows, or use BM25/application-side text search. Do not rename one artifact in isolation. |
| `grep command not found` | System grep is unavailable. | Install it outside the application workflow if permitted, or select BM25/vector search. The bundled smoke does not require grep. |
| Grep returns odd zero-score rows | Regex matched serialized metadata, while scoring counted literal occurrences in text. | Inspect result metadata/text and use a narrower safe pattern; post-filter application-side. |
| Grep query beginning with `-` fails or behaves as an option | The implementation does not insert `--` before the query. | Reject leading-dash grep queries in caller validation or use BM25/application-side matching. |
| `Passage ID '<id>' already exists` during update | Delta reused a live ID without removing it. | For IVF replacement, pass that ID in `remove_passage_ids` and add the replacement once. For HNSW, rebuild to replace/remove. |
| IVF removed fewer IDs than requested | Some requested IDs were stale or absent. | Compare requested IDs with the trusted offset map and investigate synchronizer state before adding replacements. Verify no stale JSONL rows remain. |
| Duplicate or stale IVF results after repeated updates | Remove/add IDs were inconsistent, an earlier update partially failed, or artifact generations were mixed. | Stop writers, restore the last coherent snapshot, then repeat one remove-then-add update. Assert JSONL IDs exactly match live offset IDs and are unique. |
| `Compact HNSW indices do not support in-place updates` | Existing HNSW metadata says compact. | Full rebuild in a fresh directory. To permit future append-only updates, choose non-compact storage at original build time after reviewing storage trade-offs. |
| Modified/removed HNSW content remains or untouched content disappears | HNSW low-level update is append-only, or a fallback rebuilt only the changed subset. | Reload the entire source corpus and perform a full staged rebuild. Confirm unchanged and changed sentinel documents before publishing. |
| HNSW update ignores custom new ID | The HNSW path reassigns IDs from backend `ntotal`. | Do not depend on caller IDs for low-level HNSW append. Use result metadata for application identity or full rebuild with stable IDs. |
| Update fails after writing part of its work | Process interruption, disk-full, permission error, or backend write failure. | Treat the directory as suspect. Compare to the pre-update snapshot. IVF adds backend vectors before passage append, so passage rollback alone cannot prove consistency; restore/rebuild rather than retrying blindly. |
| Search hangs or port conflicts around `5557` | Recompute server/daemon collision, stale process, or another searcher requested the same port. | Close searchers, inspect active LEANN processes/ports, then retry with one owner or another `expected_zmq_port`. The manager may choose a different actual port. |
| Files cannot be removed or replaced after search | Native backend or daemon still holds handles. | Exit every searcher context and call `cleanup()`. Disable daemon use for one-shot tests. Replace only after handles are released. |
| First search triggers a model/provider failure even for intended BM25 use | Constructor warmup ran with its default `True`. | Construct with `enable_warmup=False`, `recompute_embeddings=False`, and `use_daemon=False`, then call `vector_weight=0.0`. |
| Provider prompt appears duplicated or incompatible | Stored build/query templates and per-call `provider_options["prompt_template"]` were mixed. | Inspect stored embedding options and use one query-template source. Route provider configuration to the embeddings sub-skill. |

## Artifact integrity probe

For a trusted local index, this read-only probe catches the most common passage
corruption. Loading `.idx` uses pickle, so run it only on artifacts you trust.

```python
import json
import pickle
from pathlib import Path

base = Path("run-artifacts/candidate-index/documents.leann")
meta_path = Path(f"{base}.meta.json")
jsonl_path = Path(f"{base}.passages.jsonl")
offset_path = Path(f"{base}.passages.idx")

meta = json.loads(meta_path.read_text(encoding="utf-8"))
with offset_path.open("rb") as stream:
    offsets = pickle.load(stream)

seen = set()
with jsonl_path.open(encoding="utf-8") as stream:
    for line_number, line in enumerate(stream, 1):
        if not line.strip():
            continue
        row = json.loads(line)
        assert row["id"] not in seen, f"duplicate ID on line {line_number}"
        seen.add(row["id"])

with jsonl_path.open(encoding="utf-8") as stream:
    for passage_id, offset in offsets.items():
        stream.seek(offset)
        row = json.loads(stream.readline())
        assert row["id"] == passage_id

assert seen == set(offsets), "JSONL and offset map contain different live IDs"
assert meta["dimensions"] > 0
```

Run this before and after an IVF modification sequence. A mismatch means the
index family is not publication-safe even if a few searches still succeed.

## Escalation boundaries

- Backend storage flags, graph parameters, native count probes, and algorithmic
  recall: [backends and storage](../../backends-and-storage/SKILL.md).
- Model availability, credentials, endpoint failures, and prompt templates:
  [embeddings and chat](../../embeddings-and-chat/SKILL.md).
- CLI synchronizer snapshots, watch mode, daemon commands, and document-level
  rebuild decisions: [CLI operations](../../cli-operations/SKILL.md).
