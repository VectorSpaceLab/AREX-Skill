---
name: shard-writing
description: "Route WebDataset tar-shard creation, rollover, sample encoding,
  and local read-back validation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# shard-writing

Use this sub-skill when an agent needs to create WebDataset tar shards, choose shard names or rollover limits, encode common sample values, or verify what was written by reading it back.

## Route here for

- `TarWriter` or `ShardWriter` usage.
- Sample dict conventions with `__key__` and extension-suffixed fields.
- Encoder support for `txt`, `json`, `pyd`, `pth`, `npy`, `npz`, `tenbin`/`tb`, images, and `*.gz` suffixes.
- Shard rollover, `post` hooks, and deterministic tiny dataset generation.
- Read-after-write checks using the reader sub-skill or the bundled smoke script.

## Route elsewhere for

- Loading, decoding, batching, mixing, or consuming shards -> [reading-pipelines](../reading-pipelines/SKILL.md).
- `pipe:` URLs, stream/open behavior, cache rules, or security posture -> [io-caching-security](../io-caching-security/SKILL.md).
- Full Transformers, Ray, OCR, or cloud upload execution -> reference-only; keep only the local write loop here.

## Working rule

1. Decide whether the task needs a single tar stream (`TarWriter`) or a rollover writer (`ShardWriter`).
2. Keep sample keys stable and extension-driven; use `encoder=True` unless the payloads are already bytes or a custom encoder is required.
3. Prefer fixed metadata such as `mtime=0` when reproducibility matters.
4. If the source recipe came from a notebook, keep only the stable write or transform loop and move it into the bundled reference or helper script.
5. Validate by reading the written shard(s) back locally before handing off.
6. If the task depends on pipe URLs, remote streams, or gopen behavior, stop and hand off to the security sub-skill instead of expanding that behavior here.

## Bundled assets

- [references/api-reference.md](references/api-reference.md)
- [references/workflows.md](references/workflows.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [scripts/make_tiny_webdataset.py](scripts/make_tiny_webdataset.py)
