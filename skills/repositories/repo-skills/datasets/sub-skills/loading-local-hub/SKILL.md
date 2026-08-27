---
name: loading-local-hub
description: "Load datasets from the Hub, local files, packaged builders, Python
  objects, generators, and disk snapshots while choosing safe offline or
  authenticated network paths."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Loading Local and Hub Datasets

Use this sub-skill when the task is to get data into `datasets` before transformation: Hub repositories, local files/directories, packaged modules such as `csv` or `json`, Python-native objects, generator functions, or snapshots previously written with `save_to_disk`.

## Choose the Loading Path

- **Hub dataset**: use `load_dataset("namespace/name", name=..., split=..., revision=..., token=...)`; read [loading workflows](references/loading-workflows.md#hub-datasets) for revision, token, and offline boundaries.
- **Local files or directories**: use a packaged module such as `csv`, `json`, `parquet`, `text`, `imagefolder`, or `audiofolder` with explicit `data_files` or `data_dir`; read [loading workflows](references/loading-workflows.md#local-files-and-directories).
- **Inspect before loading**: use `load_dataset_builder(...)` to inspect configs, features, and splits before materializing rows; read [API reference](references/api-reference.md#builder-inspection).
- **Already saved snapshot**: use `load_from_disk(dataset_path, storage_options=...)` for directories produced by `save_to_disk`; read [API reference](references/api-reference.md#disk-snapshots).
- **In-memory or generated data**: use `Dataset.from_dict`, `Dataset.from_list`, `Dataset.from_pandas`, `Dataset.from_generator`, or `DatasetDict`; read [API reference](references/api-reference.md#python-object-loaders).

## Safety Boundaries

- Treat Hub access, remote URLs in `data_files`, and uncached revisions as network operations; avoid them unless the user expects network access.
- Never print or persist Hub tokens. Prefer `token=True` only when the user has authenticated locally; pass a token value only from a secret manager or environment variable.
- Prefer explicit `revision` for reproducibility and explicit `data_files` mappings for deterministic splits.
- For transformations, streaming iteration patterns, batching, filtering, or maps, route to `../processing-streaming/SKILL.md`.
- For feature schemas, casting, media decoding, and output formats, route to `../features-formats/SKILL.md`.
- For cache cleanup, push/share operations, and `datasets-cli`, route to `../sharing-cli-cache/SKILL.md`.

## Bundled Helper

Run [scripts/create_local_loading_fixture.py](scripts/create_local_loading_fixture.py) to create a tiny local multi-split CSV fixture and optional example snippets. This is safe and self-contained; it does not import `datasets`, access the network, or depend on the source checkout.

## Troubleshooting

Read [troubleshooting](references/troubleshooting.md) when loading fails due to missing files, ambiguous split inference, config selection, private Hub auth, offline mode, local format inference, `load_from_disk` path mistakes, or `storage_options` for remote filesystems.
