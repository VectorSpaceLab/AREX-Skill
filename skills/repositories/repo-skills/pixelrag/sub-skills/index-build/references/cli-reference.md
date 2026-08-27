# Index CLI Reference

## Umbrella stage dispatch

`pixelrag <stage> [args...]` lazily imports the selected stage and prints an install hint if the required extra is missing.

Stages relevant to indexing:

- `pixelrag chunk`
- `pixelrag embed`
- `pixelrag build-index`
- `pixelrag index`
- `pixelrag monitor`

## `pixelrag index build`

End-to-end source -> render -> chunk -> embed -> index.

```bash
pixelrag index build --config pixelrag.yaml --source ./docs --source-type local --output ./index --device auto --limit 10 --force
```

Flags:

| Flag | Meaning |
| --- | --- |
| `--config`, `-c` | Config path; defaults to `pixelrag.yaml` or `pixelrag.yml` if present. |
| `--source`, `-s` | Override `source.path`. |
| `--source-type` | Override source type: `kiwix`, `web`, `pdf`, or `local`. |
| `--output`, `-o` | Override output directory. |
| `--device` | `auto`, `cpu`, `mps`, or `cuda`. |
| `--limit`, `-n` | Process only the first N documents. |
| `--force`, `-f` | Delete old tiles/embeddings before rebuilding. |

## `pixelrag chunk`

```bash
pixelrag chunk --shard-dir ./tiles --workers 8
pixelrag chunk --tiles-dir ./all-shards --workers 32 --dry-run
```

Use `--force` to rechunk even if `chunks.json` exists. Use `--delete-tiles` only when you intentionally want to remove original tile images after chunking.

## `pixelrag embed`

The GPU embedder is designed for shard-scale runs with Qwen VL embedding models and GPU workers.

```bash
pixelrag embed --shard-dir ./tiles --output-dir ./embeddings --gpu-ids 0,1 --backend sglang --batch-size 128
```

For small CPU/MPS checks, prefer the local module:

```bash
python -m pixelrag_embed.embed_cpu --shard-dir ./tiles --output-dir ./embeddings --device auto --limit 5
```

## `pixelrag build-index build`

```bash
pixelrag build-index build --embeddings-dir ./embeddings --output-dir ./index \
  --nlist 4096 --nprobe 128 --metric ip --gpu-id -1
```

Qdrant mode:

```bash
pixelrag build-index build --embeddings-dir ./embeddings --output-dir ./index \
  --backend qdrant --qdrant-url http://localhost:6333 --collection pixelrag \
  --qdrant-client-config ./qdrant-client.json --qdrant-quantization-config ./quantization.json
```

Use `--append` or `--recreate` explicitly when an existing Qdrant collection is involved.

## API entry points for Python callers

- `pixelrag_index.config.load_config(path=None)`
- `pixelrag_index.config.make_source(config)`
- `pixelrag_index.pipelines.build(config: dict, limit=None, force=False) -> Path`
- `pixelrag_embed.chunk.process_shard(shard_dir, dry_run=False, force=False, delete_tiles=False, progress=True) -> dict`
- `pixelrag_embed.index.build_ivf(...)`
- `pixelrag_embed.index.build_qdrant(...)`
