---
name: reading-pipelines
description: "Guide agents that need to read, transform, decode, batch, sample,
  mix, split, and validate existing WebDataset shards."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Reading Pipelines

Use this sub-skill when the task is about consuming WebDataset shards or shard lists, not writing them.
It covers the common read path: shard expansion, worker/node splitting, tar-to-sample grouping,
decoding, filtering, tuple extraction, batching, repetition, and PyTorch CPU loader integration.

## Use this when

- You need a fluent read chain such as `WebDataset(...).shuffle(...).decode(...).to_tuple(...)`.
- You need an explicit `DataPipeline` equivalent for the same read flow.
- You need `DataLoader` or `WebLoader` integration on CPU.
- You need shard list behavior such as brace expansion, `::` lists, YAML multi-shard specs,
  directory shard lists, or resampled shard streams.
- You need to handle missing keys, empty datasets, decoder failures, or batch/unbatch mismatch.
- You need recipes for column-store reads, mixing, or distributed splitting.

## Route elsewhere when

- You need to write tar shards or generate WebDataset archives: use [shard-writing](../shard-writing/SKILL.md).
- You need URL opening, cache policy, secure mode, or `gopen` side effects: use
  [io-caching-security](../io-caching-security/SKILL.md).
- You need full training, OCR, or cloud workflows: treat those as reference-only here.

## Canonical read order

1. Confirm the shard format and sample key layout in `references/data-formats.md`.
2. Choose a fluid chain or an explicit `DataPipeline`.
3. Decide on shard splitting: `split_by_node`, `split_by_worker`, `detshuffle`, or `resampled=True`.
4. Decide where decoding happens and whether `partial` or `only` is needed.
5. Add filtering / projection steps such as `select`, `rename`, `rename_keys`, `extract_keys`, or `to_tuple`.
6. Add `batched`, `unbatched`, `with_epoch`, `repeat`, or `with_length` only when the loader contract needs them.
7. If the data comes from a new shard write, validate readback with the bundled smoke helper and then hand off to
   the sibling write-side skill.

## Key references

- [API reference](references/api-reference.md)
- [Canonical workflows](references/workflows.md)
- [Data format notes](references/data-formats.md)
- [Troubleshooting](references/troubleshooting.md)
- [Smoke helper](scripts/smoke_read_pipeline.py)

## Practical defaults

- `WebDataset` defaults to `nodesplitter=single_node_only` and `workersplitter=split_by_worker`.
- `shardshuffle=None` is a warning state; set it explicitly to `False` or a positive buffer size.
- `empty_check=True` raises when a worker sees no samples.
- `decode()` raises `DecodingError` unless you supply a handler.
- `with_length()` only sets `__len__`; it does not change the number of yielded samples.
- `with_epoch()` and `repeat()` control iteration length, not shard contents.

## Good first answers

- "How do I read a local shard?" -> start with `WebDataset(path).decode().to_tuple(...)`.
- "How do I use explicit stages?" -> use `DataPipeline(SimpleShardList(...), tarfile_to_samples(), ...)`.
- "How do I avoid empty-worker failures?" -> check shard count, splitter choice, and `empty_check`.
- "How do I mix datasets?" -> use `RoundRobin` or `RandomMix` after the basic read path.
- "How do I validate a pipeline quickly?" -> run `scripts/smoke_read_pipeline.py`.

Keep the guidance in this sub-skill bounded to reads and transforms. Do not promise
writer-side, network, or training behavior beyond what the bundled references and tests cover.
