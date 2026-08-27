# Index Update Workflows

## Safety model

`IndexUpdater` can permanently mutate index files when `persist_to_disk()` is called. Treat an index directory as mutable state, not a pure cache.

Recommended workflow:

1. Verify the target index path by printing `searcher.index`.
2. Back up the entire index directory or work on a copy.
3. Apply `remove(...)` and `add(...)` to a single `Searcher` instance.
4. Search with the same `Searcher` to validate in-memory behavior.
5. Call `persist_to_disk()` only when the mutation is intended.
6. Construct a new `Searcher` and repeat a small query to validate reload behavior.

Never call `persist_to_disk()` against a shared production index while another writer is updating the same directory. ColBERT's updater does not provide a cross-process transaction lock.

## Remove pids

Removal is pid-based:

```python
updater = IndexUpdater(config, searcher, checkpoint=None)
updater.remove([10, 42])
```

Behavior:

- Invalid pids raise `ValueError("Invalid PIDs", invalid_pids)`.
- Valid removals update the current in-memory IVF immediately.
- The current `Searcher` no longer returns those pids after removal if enough alternatives exist.
- Disk artifacts are unchanged until `persist_to_disk()`.

When persisted, removed passages keep their pid positions but their doclens are set to `0`, their embeddings are removed from the chunk tensors, affected chunk metadata are adjusted, later chunks' embedding offsets are shifted, and global metadata is updated.

## Add passages

Adding is passage-text based:

```python
updater = IndexUpdater(config, searcher, checkpoint="checkpoint-or-model")
new_pids = updater.add(["new passage text", "another passage"])
```

Behavior:

- A checkpoint is required. Without it, `add(...)` raises a `ValueError` from the updater.
- Passages are encoded with `CollectionEncoder` and compressed with the existing index codec.
- New pids start at `len(searcher.ranker.doclens)` at add time.
- The current `Searcher` sees the appended passages immediately.
- Disk artifacts are unchanged until `persist_to_disk()`.

After persistence, added embeddings and doclens are written to the last chunk when capacity allows, otherwise to newly created chunk files.

## Add/remove without persistence

If a user asks whether add/remove changes survive reload:

- Same `Searcher` instance: yes, the mutation is visible immediately.
- New `Searcher` before persistence: no, it reloads the previous disk state.
- New `Searcher` after persistence: yes, provided the disk write completed and the same index path/config are used.

This is a useful hard-case test: add a very distinctive passage, verify it appears in the current searcher, create a new searcher before persistence and verify it does not appear, persist, reload again, and verify it appears.

## Persist to disk

Call:

```python
updater.persist_to_disk()
```

Expected disk updates include:

- `metadata.json` changes, including `num_chunks` and `num_embeddings`.
- Existing chunk files such as `doclens.N.json`, `N.codes.pt`, `N.residuals.pt`, and `N.metadata.json` may be rewritten.
- New chunk files may be created if additions exceed the last chunk capacity.
- `ivf.pid.pt` is written and should become the preferred updated IVF mapping.

Use a backup/copy strategy because a crash or full disk during persistence can leave partial chunks, metadata offsets, doclens, codes, residuals, or IVF files out of sync.

## Coalesce index artifacts

The ColBERT utility `colbert.utils.coalesce` combines a multi-chunk index into a single-chunk output directory. The utility reads `metadata.json`, all `doclens.N.json`, `N.codes.pt`, `N.residuals.pt`, the last chunk metadata, and `plan.json`, then writes a new directory with `doclens.0.json`, `0.codes.pt`, `0.residuals.pt`, `0.metadata.json`, `metadata.json`, `plan.json`, and copied shared files such as centroids and IVF files.

Use coalescing when a workflow needs a compact single-file index layout after many updates. Do not overwrite the source index in place. Write to a new output directory and compare it before switching serving traffic.

A safe adapted invocation pattern is:

```bash
python -m colbert.utils.coalesce --input updated-index-dir --output coalesced-index-dir
```

Validation checks after coalescing:

- `metadata.json` has `num_chunks` set to `1` in the output.
- `doclens.0.json` length equals the total passage slots, including zero-length removed pids.
- `0.codes.pt` and `0.residuals.pt` have lengths matching `metadata["num_embeddings"]`.
- A fresh `Searcher` can load the coalesced index and answer a small query.

## Production serving handoff

For production-like flows, use two separate phases:

1. Update phase: copy index, apply `IndexUpdater`, persist, reload, and optionally coalesce.
2. Serve phase: start a read-only API process against the updated/coalesced index.

Do not update the same index directory that a long-running search API process is actively using. Prefer atomic directory promotion outside ColBERT, then restart or explicitly reload the serving process.
