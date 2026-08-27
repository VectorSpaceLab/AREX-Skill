# Resources and cache

This reference explains where Stanza stores resources, how package names are resolved, and how to inspect or refresh the cache safely.

## Cache layout

The default local model cache is versioned. The useful mental model is:

```text
<model_dir>/resources.json
<model_dir>/<lang>/<processor>/<package>.pt
```

Examples:
- `en/tokenize/combined_nocharlm.pt`
- `fr/mwt/combined.pt`
- `en/ner/ontonotes_charlm.pt`

The prepared environment reports the current default model dir through the Stanza cache settings. If `STANZA_RESOURCES_DIR` is set, Stanza treats that as the active model root.

## What lives in the resource files

Stanza keeps language-to-default-package maps and package bundles in its resource metadata modules; the active public view is the downloaded `resources.json` plus the package's default maps.

Useful maps and constants:
- `PACKAGES`: nested package bundles for a language
- `default_treebanks`: canonical default treebank per language
- `default_pretrains`: derived default pretrain map
- `no_pretrain_languages`: languages that intentionally do not get a default pretrain

When you need to reason about a package name, do not guess. Check the resolver logic and the package maps.

## Download flow

`stanza.download(...)` follows two main paths:

1. If `package='default'` and no processors are requested, it downloads the language's default bundle zip and unpacks it.
2. Otherwise it resolves the requested processors and package names, adds dependencies, and downloads individual files.

The resolver may add:
- tokenizer MWT support when the package expects it
- pretrain files
- forward/backward charlm files
- other dependency files listed in the resources metadata

The download helpers validate MD5 checksums. If a file already exists but its checksum is stale, Stanza redownloads or refreshes it depending on the download method.

## DownloadMethod guidance

- `NONE`: offline only; nothing is fetched
- `REUSE_RESOURCES`: reuse existing `resources.json`, but still repair missing models
- `DOWNLOAD_RESOURCES`: refresh `resources.json` and update stale files

Use `NONE` for inspection, `REUSE_RESOURCES` when you trust the resource map but want missing files repaired, and `DOWNLOAD_RESOURCES` when you want a full refresh.

## List installed models

Use the built-in inspector before deciding whether to run a pipeline:

```bash
python -m stanza.resources.list_installed --help
python -m stanza.resources.list_installed
python -m stanza.resources.list_installed --include-test-models
```

Behavior to remember:
- With the default cache layout, all versioned caches under the platform root are scanned.
- With a custom `STANZA_RESOURCES_DIR`, only that directory is scanned.
- `include_test_models=True` adds `stanza_test` fixtures if they exist.

## Safe download and proxy notes

`download_file(...)` routes Hugging Face URLs through `huggingface_hub` when no proxy is configured, and falls back to raw `requests` when proxies are in use.

For restricted networks:
- pass a proxy dict to `stanza.download(...)` or `Pipeline(...)`
- or pre-stage the model files and use `DownloadMethod.NONE`

## Cache staleness recovery

If a model file exists but is out of date or corrupt:
1. inspect the installed cache with `list_installed`
2. rerun with `DownloadMethod.DOWNLOAD_RESOURCES`
3. if needed, delete the stale language/processor/package file or directory and redownload

Typical stale-cache symptoms:
- unexpected checksum refreshes
- a file present on disk but rejected by the loader
- mixed old and new resource versions in the cache

## Verification basis

These resource and cache behaviors were distilled from Stanza 1.14.0 source, tests, demos, and installed-package inspection. Check the root provenance file before treating them as current for a different checkout or package version.
