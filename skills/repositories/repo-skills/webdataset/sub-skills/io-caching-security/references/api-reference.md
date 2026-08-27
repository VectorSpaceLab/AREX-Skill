# API Reference

This reference is grounded in the source and native tests. If a behavior is not listed here, treat it as unverified.

## Verified opener surface

| Symbol | Signature | What it does |
| --- | --- | --- |
| `gopen.gopen` | `gopen(url, mode='rb', bufsize=8192, **kw)` | Unified opener. Local paths and `file:` URLs are opened directly when secure mode is off; `-` maps to stdin/stdout; all other schemes dispatch through `gopen_schemes`. Only `rb` and `wb` are supported. |
| `gopen.rewrite_url` | `rewrite_url(url)` | Applies `GOPEN_REWRITE` rules before dispatch. Secure mode blocks rewriting. |
| `gopen.gopen_schemes` | dispatch table | Verified keys in the installed package: `__default__`, `pipe`, `http`, `https`, `ais`, `sftp`, `ftps`, `scp`, `gs`, `htgs`, `hf`. `file:` and bare paths are handled directly in `gopen`, not through the table. |
| `gopen.gopen_file` | `gopen_file(url, mode='rb', bufsize=8192)` | Opens local files; strips a `file:` prefix before calling `open()`. |
| `gopen.gopen_pipe` | `gopen_pipe(url, mode='rb', bufsize=8192)` | Runs the shell text after `pipe:` with `shell=True`. This is an intentional trust-boundary feature, not a safe parser. Secure mode blocks it. |
| `gopen.gopen_curl` | `gopen_curl(url, mode='rb', bufsize=8192)` | Uses `curl` for `http`, `https`, `sftp`, `ftps`, and `scp`-style access. |
| `gopen.gopen_gsutil` | `gopen_gsutil(url, mode='rb', bufsize=8192)` | Uses `gsutil` for `gs:` access. |
| `gopen.gopen_ais` | `gopen_ais(url, mode='rb', bufsize=8192)` | Uses `ais` for `ais:` access. |
| `gopen.gopen_htgs` | `gopen_htgs(url, mode='rb', bufsize=8192)` | Normalizes `htgs://` to `gs://` and reads through `curl`. |
| `gopen.gopen_hf` | `gopen_hf(url, mode='rb', bufsize=8192)` | Resolves `hf://` URLs through `huggingface_hub` and reads through `curl`. |
| `gopen.gopen_error` | `gopen_error(url, *args, **kw)` | Raises `ValueError` for unsupported schemes. |

### Opener notes

- `pipe:` is a shell-execution boundary. Treat the command text as trusted code.
- Built-in pipe/open helpers tolerate common SIGPIPE-style exit codes (`141`), and the `curl`-based openers also tolerate the usual read/write truncation codes.
- `USE_AIS_FOR` can remap any colon-separated scheme list to the AIS opener at import time.
- `GOPEN_BUFFER` affects local/file buffering; `GOPEN_VERBOSE=1` prints opener and pipe exit information.

## Cache and cleanup surface

| Symbol | Signature | What it does |
| --- | --- | --- |
| `cache.url_to_cache_name` | `url_to_cache_name(url, ndir=0)` | Produces a cache filename from a URL. For local/http/https/ftp/ftps/gs/s3/ais URLs it uses the tail path component(s); otherwise it URL-encodes the whole string. Non-string input is rejected. |
| `cache.FileCache` | `FileCache(cache_dir=None, *, url_to_name=url_to_cache_name, verbose=False, validator=check_tar_format, handler=reraise_exception, cache_size=-1, cache_cleanup_interval=30)` | Downloads remote URLs into a cache directory, validates them, and returns local file paths. Local/file URLs bypass the cache and return the original local path. |
| `cache.LRUCleanup` | `LRUCleanup(cache_dir=None, cache_size=1000000000000, keyfn=os.path.getctime, verbose=False, interval=30)` | Deletes the oldest cached files first until the total size falls below the target. Concurrent delete races are ignored. |
| `cache.StreamingOpen` | `StreamingOpen(verbose=False, handler=reraise_exception)` | Opens local/file URLs directly and delegates everything else to `gopen`. Useful when you want streaming without the cache path. |

### Cache notes

- `FileCache` asserts that the cache name has no `/`; keep custom `url_to_name` functions flat.
- The default `WebDataset` constructor uses `url_to_name=cache.pipe_cleaner`, which is only a heuristic for `pipe:` strings. Replace it when different commands must map to different files.
- `FileCache` validates downloads with `check_tar_format` by default and deletes invalid files before raising a `ValueError`.
- `check_tar_format` uses magic-number checks. If it needs a more detailed error message, it falls back to the `file` command.
- In the `WebDataset` constructor, `cache_dir` must already exist. Direct `FileCache` usage is laxer because it creates its destination directory tree when it downloads.
- `cache_size=0` in `WebDataset` selects direct streaming. A positive cache size enables cleanup; a negative cache size keeps caching but skips cleanup.

## Security helpers

| Symbol | Signature | What it does |
| --- | --- | --- |
| `utils.enforce_security` | module-level flag | Initialized from `WDS_SECURE`. When true, it blocks local/file/pipe access and URL rewriting. |
| `autodecode.torch_loads` | `torch_loads(data: bytes)` | Loads torch payloads on CPU when allowed. Secure mode blocks it. `WDS_PYTORCH_WEIGHTS_ONLY=1` only changes the `torch.load(..., weights_only=...)` argument when loading is allowed. |
| `autodecode.unpickle_loads` | `unpickle_loads(data)` | Loads pickle payloads when allowed. Secure mode blocks it. |

## Handler surface

| Symbol | Signature | Return meaning |
| --- | --- | --- |
| `handlers.reraise_exception` | `reraise_exception(exn)` | Re-raises the exception. |
| `handlers.ignore_and_continue` | `ignore_and_continue(exn)` | Returns `True` to keep going. |
| `handlers.warn_and_continue` | `warn_and_continue(exn)` | Warns, pauses briefly, returns `True`. |
| `handlers.ignore_and_stop` | `ignore_and_stop(exn)` | Returns `False` to stop. |
| `handlers.warn_and_stop` | `warn_and_stop(exn)` | Warns, pauses briefly, returns `False`. |

### WebDataset constructor points that matter here

`WebDataset(..., handler=reraise_exception, mode=None, resampled=False, repeat=False, shardshuffle=None, cache_size=-1, cache_dir=None, url_to_name=cache.pipe_cleaner, detshuffle=False, nodesplitter=single_node_only, workersplitter=split_by_worker, select_files=None, rename_files=None, empty_check=True, verbose=False, seed=None)`

Use the constructor when you want the opener, cache, and handler decisions to travel together. The relevant knobs are `handler`, `cache_dir`, `cache_size`, and `url_to_name`.

## Environment variables

| Variable | Effect |
| --- | --- |
| `WDS_SECURE` | Initial value for `utils.enforce_security`. |
| `WDS_CACHE` | Default cache directory. The constructor also uses it to override `cache_dir`. |
| `WDS_CACHE_SIZE` | Default cache size. The constructor also uses it to override `cache_size`. |
| `WDS_VERBOSE_CACHE` | Verbosity for cache activity. |
| `GOPEN_REWRITE` | URL rewrite rules in `pattern=replacement;...` form. |
| `GOPEN_VERBOSE` | Verbose logging for opener and pipe exit status. |
| `GOPEN_BUFFER` | Buffer size for local/file opens. |
| `USE_AIS_FOR` | Colon-separated list of schemes to route to AIS. |
| `WDS_PYTORCH_WEIGHTS_ONLY` | Controls `weights_only` when torch loading is allowed. |

## Flat-name rule

If a custom cache name function returns a path with `/`, `FileCache` will reject it. When a `pipe:` command or provider URL has to map to a cache filename, choose a stable, flat name up front instead of relying on shell text.
