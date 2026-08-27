# WebDataset API Reference Overview

Read this for the high-level package surface before opening a focused sub-skill reference. The generated skill is aligned with WebDataset distribution/module version 1.0.2.

## Public package identity

```python
import webdataset as wds
print(wds.__version__)  # 1.0.2
```

The package exports the main read, write, stream, handler, and helper surfaces from the top-level `webdataset` module. Prefer `import webdataset as wds` in user-facing examples.

## Main API families

| Family | Core symbols | Owning sub-skill |
| --- | --- | --- |
| Read pipelines | `WebDataset`, `DataPipeline`, `FluidInterface`, `WebLoader`, `SimpleShardList`, `ResampledShards`, `DirectoryShardList`, `tarfile_to_samples`, `shuffle`, `decode`, `to_tuple`, `batched`, `unbatched`, `with_epoch`, `repeat`, `RandomMix`, `RoundRobin` | [reading-pipelines](../sub-skills/reading-pipelines/SKILL.md) |
| Shard writing | `TarWriter`, `ShardWriter`, writer encoders, `numpy_dumps`, `torch_dumps`, tenbin helpers | [shard-writing](../sub-skills/shard-writing/SKILL.md) |
| IO/cache/security | `gopen`, `gopen_schemes`, `FileCache`, `StreamingOpen`, `LRUCleanup`, `url_to_cache_name`, `enforce_security`, exception handlers | [io-caching-security](../sub-skills/io-caching-security/SKILL.md) |

## Verified root signatures

| API | Signature or constructor shape | Notes |
| --- | --- | --- |
| `WebDataset` | `(urls, handler=reraise_exception, mode=None, resampled=False, repeat=False, shardshuffle=None, cache_size=-1, cache_dir=None, url_to_name=pipe_cleaner, detshuffle=False, nodesplitter=single_node_only, workersplitter=split_by_worker, select_files=None, rename_files=None, empty_check=True, verbose=False, seed=None)` | Main reader; set `shardshuffle` explicitly. |
| `DataPipeline` | `(*args, **kwargs)` | Explicit ordered stage pipeline. |
| `WebLoader` | `(*args, **kw)` | Thin `DataLoader` wrapper with fluid interface. |
| `TarWriter` | `(fileobj, user='bigdata', group='bigdata', mode=0o0444, compress=None, encoder=True, keep_meta=False, mtime=None, format=None)` | Single tar writer. |
| `ShardWriter` | `(pattern, maxcount=100000, maxsize=3e9, post=None, start_shard=0, verbose=1, opener=None, **kw)` | Rollover writer. |
| `gopen` | `(url, mode='rb', bufsize=8192, **kw)` | Unified stream opener. |

## Minimal environment check

Run the bundled checker when a user asks whether an environment can use this package:

```bash
python scripts/check_env.py
```

Use `--require-torch` when the task specifically needs PyTorch `DataLoader`/`WebLoader` behavior. The checker creates a tiny local shard and reads it back; it does not access the original source checkout or the network.

## Optional dependencies and dynamic imports

Base metadata declares `braceexpand`, `numpy`, and `pyyaml`. Common workflows may also need:

- Pillow for image encoding/decoding (`pil`, `rgb`, `jpg`, `png`, `ppm`, `tiff`).
- torch for `DataLoader`, `WebLoader`, `decode("torch...")`, and `pth` payloads.
- msgpack or cbor for those field suffixes.
- External commands such as `curl`, `gsutil`, or `ais` for specific stream openers.

Do not install the whole development extra unless the task is repository development. For ordinary package use, install only the optional dependency that matches the workflow.

## Sub-skill routing rule

If the task is about data already stored as shards, start with [reading-pipelines](../sub-skills/reading-pipelines/SKILL.md). If it is about creating shards, start with [shard-writing](../sub-skills/shard-writing/SKILL.md). If it is about URL trust, caching, secure mode, or opener failures, start with [io-caching-security](../sub-skills/io-caching-security/SKILL.md).
