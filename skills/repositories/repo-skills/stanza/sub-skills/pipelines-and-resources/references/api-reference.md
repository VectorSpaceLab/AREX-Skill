# API reference

This sub-skill is about the neural pipeline, multilingual routing, downloads, and local model inspection.

## Quick imports

```python
import stanza
from stanza import Pipeline, MultilingualPipeline, DownloadMethod
from stanza.resources.common import download
from stanza.resources.list_installed import list_installed
```

## Installed signatures

Observed in the prepared environment:

```python
Pipeline(lang='en', dir='<default model dir>', package='default', processors={}, logging_level=None, verbose=None, use_gpu=None, model_dir=None, download_method=DownloadMethod.DOWNLOAD_RESOURCES, resources_url='<default resources url>', resources_branch=None, resources_version='1.14.0', resources_filepath=None, proxies=None, foundation_cache=None, device=None, allow_unknown_language=False, **kwargs)

MultilingualPipeline(model_dir='<default model dir>', lang_id_config=None, lang_configs=None, ld_batch_size=64, max_cache_size=10, use_gpu=None, restrict=False, device=None, download_method=DownloadMethod.DOWNLOAD_RESOURCES, processors=None)

download(lang='en', model_dir='<default model dir>', package='default', processors={}, logging_level=None, verbose=None, resources_url='<default resources url>', resources_branch=None, resources_version='1.14.0', model_url='default', proxies=None, download_json=True)

list_installed(model_dir='<default model dir>', print_table=True, include_test_models=False)
```

## DownloadMethod

- `DownloadMethod.NONE`: do not download anything; fail fast if files are missing.
- `DownloadMethod.REUSE_RESOURCES`: reuse an existing `resources.json`, but still fetch missing models.
- `DownloadMethod.DOWNLOAD_RESOURCES`: refresh `resources.json` and overwrite stale models when needed.

String forms such as `"none"`, `"reuse_resources"`, and `"download_resources"` are normalized by `Pipeline`.

## Pipeline

`Pipeline` is the main neural pipeline for one language.

### Input forms
- `str`: raw text
- `list[str]`: bulk string processing
- `list[Document]`: bulk `Document` processing
- `Document`: single document

### Common methods
- `pipe(text_or_doc)` is the same as `pipe.process(...)`
- `pipe.process(doc, processors=None)` accepts `str`, `list`, or `Document`; the optional processor list can be a string, list, tuple, or set
- `pipe.bulk_process(docs)` wraps each string in a `Document` and processes a batch
- `pipe.process_many(iterable)` always returns a list and preserves order
- `pipe.stream(iterator, batch_size=50)` yields processed documents lazily and reindexes sentence numbers across the stream

### Processors and packages
`Pipeline` accepts the common selection forms used by the resource resolver:
- `processors="tokenize,pos,lemma"`
- `processors=["tokenize", "pos"]`
- `processors={"tokenize": "spacy"}`
- `package="default"`
- `package={"tokenize": "combined", "pos": "combined"}`

When `processors` is a string/list/tuple, the package argument can be a string or a dict. When `processors` is a dict, package is usually left as `None`.

### Common pipeline kwargs
- `tokenize_pretokenized=True` for already segmented input
- `tokenize_no_ssplit=True` to suppress sentence splitting
- `pretagged=True` or `depparse_pretagged=True` when tags are already present
- `allow_unknown_language=True` for custom language/model setups
- `*_model_path` kwargs for explicit local model files
- `device='cpu'`, `device='cuda'`, or `device='cuda:0'` for explicit placement

### Device selection
- `device` wins when provided.
- If `device` is omitted, `use_gpu=None` or `use_gpu=True` lets Stanza choose the best available device.
- `use_gpu=False` forces CPU.
- The pipeline warns and falls back to CPU when GPU is requested but not available.

## MultilingualPipeline

`MultilingualPipeline` routes each document through a per-language `Pipeline` after language identification.

Key behavior:
- It accepts a single string, a list of strings, or a list of `Document` objects and preserves the singleton/list shape on output.
- It builds a dedicated `langid` pipeline for the `multilingual` language.
- It caches language-specific pipelines up to `max_cache_size`.
- `lang_configs` can be a plain dict or a `defaultdict` of per-language settings.
- `default_processors` can be supplied as a comma string or sequence and will be filtered against each language's available processors.
- `restrict=True` narrows language identification to the configured language set.

Typical forms:

```python
from collections import defaultdict

lang_configs = {
    "en": {"processors": "tokenize,pos,lemma,depparse,ner"},
    "fr": {"processors": "tokenize,pos,lemma,depparse"},
}
pipe = stanza.MultilingualPipeline(lang_configs=lang_configs)

lang_configs = defaultdict(lambda: dict(processors="tokenize"))
pipe = stanza.MultilingualPipeline(lang_configs=lang_configs, restrict=True)
```

## download

`stanza.download(...)` resolves packages through the resources file, downloads default or per-processor models, and validates MD5 checks. It is the right entry point when you want to stage resources explicitly before building a pipeline.

Important points:
- `package='default'` with no processors downloads the language's default bundle zip.
- Specific `processors`/`package` combinations can pull dependencies such as pretrains and charlm files.
- `download_json=False` is only safe when a valid `resources.json` is already present.
- Pass `proxies={"http": ..., "https": ...}` if your network requires them.

## list_installed

`list_installed(...)` inspects local model caches without downloading anything.

Return rows include:
- `version`
- `lang`
- `lang_name`
- `processor`
- `package`
- `path`
- `size_bytes`

Use this first when you need to decide whether to run offline, refresh a cache, or pick a package name.

## Verification basis

These facts were distilled from Stanza 1.14.0 source, tests, demos, and installed-package signature inspection. Check the root provenance file before treating them as current for a different checkout or package version.
