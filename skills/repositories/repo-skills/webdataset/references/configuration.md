# Installation and Configuration

Use this reference for package setup, optional dependencies, and environment variables that affect WebDataset behavior.

## Installation patterns

```bash
pip install webdataset
```

For a checkout used in development:

```bash
pip install -e .
```

Do not install the repository's full development extra for ordinary package use. It includes notebook, docs, release, and large ML dependencies that are not required for most loading/writing tasks.

## Optional dependency map

| Need | Typical dependency | Notes |
| --- | --- | --- |
| Core WebDataset import, shard expansion, NumPy arrays | `braceexpand`, `numpy`, `pyyaml` | Declared package dependencies. |
| Image decoding/encoding (`pil`, `rgb`, `jpg`, `png`, `ppm`) | Pillow | Required by image handlers and writer image encoders. |
| PyTorch loaders and tensor payloads | torch | Needed for real `DataLoader`/`WebLoader`, `decode("torch...")`, and `pth` payloads. |
| MessagePack fields | msgpack | Only needed for `mp`, `msg`, or `msgpack` fields. |
| CBOR fields | cbor | Only needed for `cbor` fields. |
| HTTP/HTTPS streaming through built-in opener | `curl` executable | Used by the curl-based `gopen` handlers. |
| GCS/AIS/Hugging Face opener helpers | `gsutil`, `ais`, `huggingface_hub`, provider credentials | Keep credentials outside skill files and scripts. |

## Environment variables

| Variable | Scope | Effect |
| --- | --- | --- |
| `WDS_SECURE` | security | Initializes `webdataset.utils.enforce_security`; when true, blocks local/file/pipe URL access, URL rewriting, pickle loads, and torch loads. |
| `WDS_CACHE` | cache | Overrides default cache directory and constructor `cache_dir`. |
| `WDS_CACHE_SIZE` | cache | Overrides cache size. Positive values enable cleanup behavior where relevant. |
| `WDS_VERBOSE_CACHE` | cache | Prints cache activity. |
| `WDS_SEED` | reading | Overrides the seed used by `WebDataset` when no explicit seed is supplied. |
| `WDS_PYTORCH_WEIGHTS_ONLY` | decoding | Changes the `torch.load(..., weights_only=...)` setting for torch payload decoding when secure mode allows torch loading. |
| `GOPEN_REWRITE` | IO | URL rewrite rules; blocked in secure mode. |
| `GOPEN_VERBOSE` | IO | Prints opener/pipe diagnostic information. |
| `GOPEN_BUFFER` | IO | Buffer size for local/file opens. |
| `USE_AIS_FOR` | IO | Colon-separated schemes routed to the AIS opener at import time. |

## Safe setup checklist

1. Install only the optional dependency family needed by the task.
2. Run `python scripts/check_env.py` from the root skill directory to verify importability and a tiny local round-trip.
3. Use `python scripts/check_env.py --require-torch` when a task depends on PyTorch loader behavior.
4. If secure mode is required, set `WDS_SECURE=1` before importing or opening any data.
5. If caching is required, create the cache directory before constructing `WebDataset(..., cache_dir=...)`.
6. Keep credentials, provider config, and cloud tokens outside generated skill files and helper scripts.

## Where to go next

- Reading and loading behavior: [reading-pipelines](../sub-skills/reading-pipelines/SKILL.md)
- Shard creation and writer encoders: [shard-writing](../sub-skills/shard-writing/SKILL.md)
- Opener, cache, and security boundary: [io-caching-security](../sub-skills/io-caching-security/SKILL.md)
