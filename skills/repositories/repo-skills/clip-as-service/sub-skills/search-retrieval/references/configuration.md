# Search Configuration

## Required components

A CLIP Search Flow needs:

1. A CLIP encoder executor, usually `clip_server.executors.clip_torch.CLIPEncoder`.
2. An AnnLite indexer executor, `annlite.executor.AnnLiteIndexer`.
3. `n_dim` equal to the selected model output dimension.
4. A `workspace` path for persistent index files.

## Common `n_dim` values

| Model pattern | `n_dim` |
| --- | ---: |
| `ViT-B-32::*`, `ViT-B/32`, `ViT-B-16::*`, `ViT-B/16` | 512 |
| `RN101::*` | 512 |
| `RN50::*`, `RN50x64::*`, `ViT-H-14::*`, `ViT-g-14::*`, `CN-CLIP/RN50`, `CN-CLIP/ViT-H-14` | 1024 |
| `RN50x4::*`, `ViT-B-16-plus-240::*`, `M-CLIP/XLM-Roberta-Large-Vit-B-16Plus` | 640 |
| `RN50x16::*`, `ViT-L-14::*`, `ViT-L-14-336::*`, `ViT-L/14@336px`, most `M-CLIP/*Vit-L-14`, `CN-CLIP/ViT-L-14*` | 768 |

If uncertain, read [../server-runtime/references/model-overview.md](../../server-runtime/references/model-overview.md) and validate with the bundled checker.

## AnnLite fields

| Field | Location | Meaning |
| --- | --- | --- |
| `n_dim` | `executor.uses.with` | Vector dimension; must match the encoder model. |
| `limit` | `executor.uses.with` | Default top-k for search when client does not override. |
| `workspace` | executor item | Directory where AnnLite stores index state. |
| `shards` | executor item | Number of indexer shards. |
| `polling` | executor item | Endpoint fanout policy for sharded executors. |

## Polling rules

Use this shape for sharded search:

```yaml
polling:
  /index: ANY
  /search: ALL
  /update: ALL
  /delete: ALL
  /status: ALL
```

`/index: ANY` sends a document to one shard so it is not duplicated. `/search: ALL` asks every shard, because the nearest neighbor could live anywhere. Update/delete/status operations also need `ALL` to keep shard state consistent.

## Client/server split

- Search server host: install `clip-server[search]` and start the Flow.
- Caller host: install `clip-client` and call `Client.index`/`Client.search`.
- Use the same server URI scheme and port that the Flow prints.

## Static validation

```bash
python sub-skills/search-retrieval/scripts/check_search_config.py search-flow.yml --model-name ViT-B-32::openai
```

The checker validates the Flow contains both CLIPEncoder and AnnLiteIndexer modules, warns about `n_dim` mismatches, checks workspace presence, and inspects sharded polling values. It does not start a server.
