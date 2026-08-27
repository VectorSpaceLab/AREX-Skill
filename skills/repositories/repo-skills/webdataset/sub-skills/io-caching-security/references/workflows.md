# Workflows

Use these patterns when the task is about opening bytes safely, caching them, or deciding how to recover from opener failures. Keep the scope at the trust boundary; if the request turns into sample decoding or loader composition, hand off to `../../reading-pipelines/SKILL.md`.

## 1. Pick the opening strategy first

| Situation | Preferred choice | Why |
| --- | --- | --- |
| Trusted local file on disk | `gopen(path, "rb")` | Fastest and simplest. |
| Trusted shell command | `gopen("pipe:...", "rb")` | Lets a shell command stream bytes directly. |
| Remote shard that should be cached | `WebDataset(..., cache_dir=..., cache_size=...)` or `FileCache` | Downloads once, then reuses the local copy. |
| Remote shard that should stay streaming-only | `cache_dir=None` or `cache_size=0` | Avoids the cache path entirely. |
| Special provider or authenticated source | Custom `gopen_schemes[...]` callable | Keeps the trust boundary explicit and reusable. |

## 2. Use `pipe:` only for trusted shell text

`pipe:` is not a parser; it is shell execution. Use it only when the command text is already trusted.

```python
import shlex
import webdataset as wds

path = "/tmp/sample.tar"
with wds.gopen(f"pipe:cat {shlex.quote(path)}", "rb") as stream:
    data = stream.read()
```

For writes, the shell command must consume stdin:

```python
with wds.gopen(f"pipe:cat > {shlex.quote(path)}", "wb") as stream:
    stream.write(b"payload")
```

If a local file must enter the cache path, the common recipe is to wrap it in a trusted `pipe:cat ...` command. That is a deliberate trust-boundary decision, not a default behavior.

## 3. Cache remote shards safely

Prefer the constructor-level cache knobs when the caller is already building a WebDataset object:

```python
import webdataset as wds

ds = wds.WebDataset(
    urls,
    cache_dir="/tmp/webdataset-cache",
    cache_size=10_000_000,
    url_to_name=wds.cache.url_to_cache_name,
    handler=wds.handlers.warn_and_continue,
)
```

Rules that matter:

- Keep `url_to_name` flat; `FileCache` rejects names with `/`.
- Use `url_to_cache_name` as the safe default for ordinary remote URLs.
- Override `url_to_name` when a `pipe:` command or provider URL would otherwise collapse distinct shards to the same cache file.
- If the cache directory is missing, create it first. `WebDataset` checks that path before building the pipeline.
- If you want cache cleanup, set a positive `cache_size` and a cleanup interval; otherwise the cache can grow without bound.

A direct `FileCache` is useful when you only need the cached opener itself:

```python
from webdataset.cache import FileCache, url_to_cache_name

cached = FileCache(cache_dir="/tmp/webdataset-cache", url_to_name=url_to_cache_name)
```

## 4. Register custom schemes instead of hiding auth in a shell pipe

When a source needs a special client or a provider-specific stream, register a callable in `gopen_schemes` before the dataset is created.

```python
import webdataset as wds


def open_custom(url, mode="rb", bufsize=8192, **_kw):
    # Return a readable or writable binary stream here.
    raise NotImplementedError


wds.gopen_schemes["custom"] = open_custom
```

Use this pattern when repeated `pipe:` invocations are causing broken pipes or when a persistent client is safer than a subprocess per shard. Keep credentials and provider auth outside this subtree; this skill only teaches the opener boundary.

## 5. Choose a handler intentionally

| Need | Handler | What happens |
| --- | --- | --- |
| Fail fast | `reraise_exception` | Re-raises the original exception. |
| Skip silently and keep going | `ignore_and_continue` | Returns `True`. |
| Skip with a warning | `warn_and_continue` | Warns, pauses briefly, returns `True`. |
| Stop silently | `ignore_and_stop` | Returns `False`. |
| Stop with a warning | `warn_and_stop` | Warns, pauses briefly, returns `False`. |

Use the same recovery policy on the opener and the downstream tar/decoder stage when the caller wants one consistent response to corrupt data.

## 6. Harden the boundary

1. Set `WDS_SECURE=1` or `webdataset.utils.enforce_security = True` before opening anything.
2. Remove `GOPEN_REWRITE` if URL rewriting is not part of the approved trust boundary.
3. Prefer HTTP/HTTPS, stdin/stdout, or a custom callable over `pipe:` when the source is not fully trusted.
4. Replace pickled payloads (`pkl`, `pyd`, `pth`) with non-pickled encodings when possible.
5. Remember that secure mode blocks local/file/pipe/rewrite and pickle/torch loads, but it does not rewrite the rest of the pipeline for you.

## 7. Smoke the boundary locally

Run the bundled helper after changing opener, cache, or handler logic:

```bash
python scripts/check_io_security.py
```

The helper uses only local files and temporary cache data. Do not extend it into a credential or network test.

## 8. Cross-links

- How these openers are consumed inside `WebDataset` and `WebLoader`: `../../reading-pipelines/SKILL.md`.
- Pipe-writer caveats and shard creation details: `../../shard-writing/SKILL.md`.
