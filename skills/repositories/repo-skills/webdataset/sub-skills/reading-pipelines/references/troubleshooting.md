# Troubleshooting

This file lists the common read-side failure modes and the first fixes to try.

| Symptom | Likely cause | First fix | Route |
| --- | --- | --- | --- |
| `No samples found in dataset` | Too few shards for the worker count, or the splitters removed everything | Check shard count, shard list, and `nodesplitter` / `workersplitter`. Use `empty_check=False` only when you deliberately accept empty slices. | stay here |
| `you need to add an explicit nodesplitter ...` | Multi-node training is using the default `single_node_only` splitter | Pass `nodesplitter=wds.split_by_node` or otherwise choose a node split strategy. | stay here |
| `Cannot find ... in sample keys` or `to_tuple`/`rename` missing-key errors | The sample field names do not match the projection spec | Fix the extension names, use `rename` / `rename_keys`, or switch to `extract_keys(..., ignore_missing=True)`. | stay here |
| `DecodingError` | A decoder failed on a particular field | Inspect the attached `key`, `url`, `k`, and `sample`. If the field is optional, use a handler to continue or drop the sample. | stay here |
| `keys don't match in different samples` during batching | The batched samples do not have a consistent dict structure | Normalize the sample shape before `batched()`, or use a tuple projection that always returns the same keys. | stay here |
| `unbatched` fails on nested structures | The batch is not a flat tuple/list or equal-length dict | Flatten the structure first; nested dicts with mismatched lengths are not a supported use case. | stay here |
| Memory use spikes after decode | Shuffle was applied after decode | Move `shuffle()` earlier so the buffer holds encoded bytes rather than decoded tensors or images. | stay here |
| `decode("pil")` or image decode fails | Pillow is missing, or the requested image handler is unavailable | Install the missing optional dependency or fall back to a non-image decoder. | stay here |
| `torch*` / `torch_audio` / `torch_video` decode fails | The optional torch family dependency is missing | Use a decoder that matches the installed environment, or keep the field raw until a later stage. | stay here |
| Column-store inner read fails with empty shards | The nested `WebDataset` is being split by nodes or workers | Set `nodesplitter=None` and `workersplitter=None` on the inner reader; use `resampled=True` when the inner stream must stay alive. | stay here |
| `pipe:` or local-file access is blocked | Secure mode is active | Route the issue to [io-caching-security](../../io-caching-security/SKILL.md). |
| Readback from a freshly written shard looks wrong | The write step is probably wrong, not the read step | Use the sibling [shard-writing](../../shard-writing/SKILL.md) skill and then rerun the bundled smoke helper. |

## Extra notes

- `WebDataset(shardshuffle=None)` is a warning state, not a good default.
- `ResampledShards(empty_check=True)` raises when no shard URLs are found.
- `DirectoryShardList` requires a real directory path ending in `/`.
- `select_files` and `rename_files` run before tar grouping, so errors there can look like missing keys later.
- `WebLoader` repeats and `with_epoch()` problems often show up as the wrong number of batches rather than a hard error.

## What to do first

1. Confirm the shard list expands to what you expect.
2. Confirm node and worker splitters are appropriate for the current process count.
3. Confirm the decoder matches the payload type.
4. Confirm batching happens after the sample shape is stable.
5. If the source was just written, verify the writer side first.
