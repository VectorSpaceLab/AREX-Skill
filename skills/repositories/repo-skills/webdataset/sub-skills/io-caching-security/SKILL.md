---
name: io-caching-security
description: "Route WebDataset URL opening, stream caching, secure mode, custom
  gopen schemes, and handler choices without re-teaching full reading
  pipelines."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# IO, Caching, and Security

Use this sub-skill when the task is about WebDataset's opener and cache boundary: choosing how URLs are opened, deciding whether a source is cached or streamed, adding a custom scheme, or diagnosing secure-mode and broken-pipe failures. Do not expand into full sample decoding or training loops here.

## Route here for

- `gopen(...)` and `gopen_schemes[...]` decisions for local paths, `file:`, `pipe:`, `http:`, `https:`, `gs:`, `hf:`, `ais:`, `htgs:`, `scp:`, and `sftp:` resources.
- `FileCache`, `StreamingOpen`, `LRUCleanup`, `url_to_cache_name`, cache validation, and cache-size cleanup.
- Secure mode via `WDS_SECURE=1` or `webdataset.utils.enforce_security = True`.
- `GOPEN_REWRITE`, `GOPEN_VERBOSE`, `GOPEN_BUFFER`, `WDS_CACHE`, `WDS_CACHE_SIZE`, `WDS_VERBOSE_CACHE`, and `USE_AIS_FOR`.
- Choosing `reraise_exception`, `ignore_and_continue`, `warn_and_continue`, `ignore_and_stop`, or `warn_and_stop`.
- Diagnosing `Broken pipe`, cache-dir, missing executable, and pickle/torch security blocks.

## Route away from here

- How openers feed sample extraction, decoding, batching, and loader composition -> `../reading-pipelines/SKILL.md`.
- Shard creation, encoders, and writer pipe caveats -> `../shard-writing/SKILL.md`.
- Cloud credential setup and secret management -> reference only; do not teach it here.

## Start with these references

- `references/api-reference.md` for verified signatures, scheme coverage, and env vars.
- `references/workflows.md` for safe opener patterns, cache setup, custom schemes, and handler selection.
- `references/troubleshooting.md` for broken pipes, cache failures, and security blocks.
- `scripts/check_io_security.py` for a no-network smoke check.

## Fast decisions

1. If the input is a trusted shell command, `pipe:` is allowed only because the caller trusts the command text.
2. If you want streaming only, set `cache_dir=None` or `cache_size=0`.
3. If you want caching, keep `url_to_name` flat and let `FileCache` validate the downloaded shard.
4. If you want hardening, set `WDS_SECURE=1` before opening anything.
5. If you need a provider-specific stream, register a callable in `webdataset.gopen_schemes[...]` instead of hiding auth inside a one-off shell pipe.

## Minimum success checks

- `gopen` reads a local file and a trusted `pipe:` source in non-secure mode.
- Secure mode blocks local/file/pipe/rewrite plus pickle/torch loads, while `-` stdin/stdout remains usable.
- Cache names are flat, remote objects land under the cache root, and `LRUCleanup` deletes the oldest files first.
- The chosen handler either continues, stops, or re-raises exactly as its return value says.

If the request is really about how those openers are used inside a data pipeline, stop here and hand off to `../reading-pipelines/SKILL.md`.
