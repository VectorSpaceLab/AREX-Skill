# Troubleshooting

Use this reference for the opener/cache/security boundary only. If the issue turns into sample decoding, batching, or node/worker splitting, hand off to `../../reading-pipelines/SKILL.md`.

## 1. Secure mode blocked the source

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `gopen: unsafe_gopen is False, cannot open local files` | Secure mode is on and you tried a plain path. | Use a trusted remote opener, stdin/stdout, or disable secure mode only in a trusted environment. |
| `gopen: unsafe_gopen is False, cannot open local files` on `file:` | Secure mode also blocks `file:` URLs. | Same as above. |
| `gopen_pipe: unsafe_gopen is False, cannot open pipe URLs` | Secure mode blocked `pipe:` shell execution. | Move the trust boundary outward or replace `pipe:` with a custom callable opener. |
| `rewrite_url: unsafe_gopen is False, cannot rewrite URLs using environment variables` | Secure mode blocked `GOPEN_REWRITE`. | Remove the rewrite or turn secure mode off before any open call. |
| `Unpickling is not allowed for security reasons when enforce_security is set.` | Secure mode blocked pickle-based decoding. | Replace the payload format or isolate the load in a trusted step. |
| `torch.loads is not allowed for security reasons when enforce_security is set.` | Secure mode blocked torch payload decoding. | Use a non-pickled encoding or a trusted preprocessing step. |

Notes:

- Set `WDS_SECURE=1` or `webdataset.utils.enforce_security = True` before opening anything.
- `WDS_PYTORCH_WEIGHTS_ONLY=1` only changes the `torch.load(..., weights_only=...)` argument when torch loading is allowed; it does not override secure mode.
- Secure mode does **not** block `http`/`https` or `-` stdin/stdout.

## 2. Broken pipe or unstable `pipe:` source

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Broken pipe` | The shell command closed early or the consumer stopped reading. | Start with `GOPEN_VERBOSE=1` and inspect the child exit status. |
| `pipe exit [141 ...]` | SIGPIPE from a pipe writer/reader shutdown. | Treat it as a trust-boundary signal; if it repeats, replace the shell pipe with a custom opener. |
| Repeated reconnects or flaky S3 reads through `pipe:` | The command spawns a new client for every shard. | Register a persistent client-backed callable in `gopen_schemes` instead of keeping the shell pipe. |

Notes:

- The built-in openers already tolerate common SIGPIPE-style exit codes, so persistent failures usually mean the shell command itself is unstable.
- If the broken pipe comes from a writer path, cross-link to `../../shard-writing/SKILL.md`.
- Do not encode secrets in the pipe text. This subtree is not the place to design credential flows.

## 3. Cache-dir and cache-name failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `cache directory ... does not exist` | `WebDataset(..., cache_dir=...)` was given a missing path. | Create the directory first, or pass a valid existing cache root. |
| Cache entries all collapse to one filename | The `url_to_name` function is too weak, or a `pipe:` command collapsed to the same name every time. | Use a flat but stable naming function such as `url_to_cache_name`, or override `url_to_name` with a command-aware function. |
| `... is not a tar archive, but a ...` | `FileCache` validation rejected the downloaded file. | Check the URL, the file contents, and whether the source is actually a tar/gzip shard. |
| Cache keeps growing | Cleanup is disabled or the size limit is too large. | Set a positive `cache_size` and cleanup interval, or run `LRUCleanup` directly. |

Notes:

- `WebDataset` checks `cache_dir` early. Direct `FileCache` is laxer and creates destination subdirectories on demand.
- If validation fails and the detailed message mentions the `file` command, install that tool or inspect the shard manually.
- `url_to_cache_name` accepts only strings. If a non-string leaks in, that is a caller bug.

## 4. Unsupported opener or missing dependency

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `no gopen handler defined` | The URL scheme is not in `gopen_schemes`. | Register a callable for that scheme or use a built-in opener. |
| `unknown mode` | The opener was asked for something other than `rb` or `wb`. | Use binary read or write mode. |
| `curl`/`gsutil`/`ais` not found | The built-in opener depends on an external executable. | Install the executable or switch to a custom opener. |
| `huggingface_hub` import failure | The `hf:` opener needs the Hugging Face client library. | Install the dependency or use another source. |

## 5. What to check first

1. Turn on `GOPEN_VERBOSE=1` and, for caching, `WDS_VERBOSE_CACHE=1`.
2. Verify whether secure mode is active.
3. Verify that the URL scheme is actually supported.
4. Verify that the cache name is flat and unique.
5. Verify that the chosen handler matches the intended continue/stop policy.

If the issue is still unresolved after those checks, the remaining problem is usually outside this sub-skill's scope: either a downstream pipeline issue or a provider-specific auth problem.
