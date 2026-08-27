# Downloader and Gensim-Data

## API basics

```python
import gensim.downloader as api

all_info = api.info()
text8_info = api.info("text8")
path = api.load("text8", return_path=True)
corpus = api.load("text8")
```

`api.info(name=None, show_only_latest=True, name_only=False)` returns metadata.
`api.load(name, return_path=False)` downloads if needed and either returns a path
or loads the resource object.

## Cache location

Gensim uses `GENSIM_DATA_DIR` when set; otherwise it defaults to a user cache
directory. Set the variable before import/use when the task needs a specific disk
location:

```bash
export GENSIM_DATA_DIR=/path/to/cache
python -m gensim.downloader -i text8
```

Do not hard-code private cache paths in reusable instructions. For large models,
confirm free disk space and cache policy first.

## Download safety checklist

1. Run `api.info(name)` or `python -m gensim.downloader -i name`.
2. Check size, license/source, expected object type, and cache path.
3. Use `return_path=True` if the workflow only needs a file path.
4. Avoid loading multi-gigabyte pretrained vectors into memory unless the task
   explicitly requires it.
5. Record whether network access is available; downloader falls back to local
   cache only if the cache exists.

## CLI examples

```bash
python -m gensim.downloader -i name
python -m gensim.downloader -i text8
python -m gensim.downloader -d text8
```

Use `-d` only after approval to download. Use `-i` for metadata-only planning.
