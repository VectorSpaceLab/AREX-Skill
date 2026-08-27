# Community catalogs and dataset collections

Community namespaces and dataset collections solve different problems. A namespace adds an external source of datasets under a prefix such as `namespace:dataset`. A dataset collection groups already-defined TFDS datasets into a versioned benchmark or task bundle.

## Community namespace model

Community datasets are configured by a TOML file with one table per namespace.

```toml
[huggingface]
info = "Namespace to load datasets on HuggingFace."
paths = ["github://huggingface/datasets/tree/master/datasets"]

[my_prepared_data]
info = "Prepared TFDS folders for a team catalog."
paths = ["gs://bucket-or-local-root/tfds"]
```

Rules:

- `paths` may be a string or a list of strings.
- GitHub-style paths load community builder code through the package/community registry path.
- Filesystem or GCS data roots load prepared builder directories through the data-directory registry path.
- Do not mix code-import paths and prepared-data roots under one namespace; split them into different namespaces.
- For prepared-data namespaces, callers should not pass an overriding `data_dir` to the community builder; the namespace path is the data source.
- Namespace names are part of the dataset string: `tfds.load("namespace:dataset", ...)`.

Use a namespace when the user wants a stable prefix for an external catalog or prepared data root. Use `builder_from_directory` instead when the user only has one local prepared folder and does not need catalog registration.

## HuggingFace namespace

The built-in community example is HuggingFace.

```python
import tensorflow_datasets as tfds

builder = tfds.builder("huggingface:dataset_name")
ds = tfds.load("huggingface:dataset_name", split="train")
```

Operating cautions:

- Treat the first load as network/cache-sensitive unless the user confirms cached data.
- Gated or private datasets may require accepting terms and passing a user token through approved runtime configuration.
- HuggingFace repo names, configs, and split names are normalized to TFDS-safe names during conversion.
- If the user asks to materialize a HuggingFace dataset into TFDS shards, use `HuggingfaceDatasetBuilder` from the format builders reference.
- If the user only asks how to iterate, batch, decode, or inspect a loaded dataset, route to `data-loading`.

## Community wrapper behavior

The community loader imports exactly one `DatasetBuilder` from a community module. If import finds zero builders, multiple builders, abstract methods, or missing optional dependencies, the failure is a builder/code registration problem rather than a loading problem.

For HuggingFace-style builder code, TFDS provides a compatibility wrapper that maps selected `datasets` APIs to TFDS constructs. Useful implications:

- HuggingFace `GeneratorBasedBuilder` and `BeamBasedBuilder` classes can be imported under the wrapper.
- HuggingFace feature types such as `ClassLabel`, `Sequence`, `Translation`, and scalar `Value` are converted to TFDS features.
- The wrapper patches file access through TensorFlow file APIs and handles some list-as-sequence patterns.
- This is an import compatibility layer, not a promise that every dataset-specific optional dependency is installed.

## Dataset collections

Dataset collections group existing TFDS datasets by collection version. They do not parse raw examples and do not define a new dataset namespace.

```python
import tensorflow_datasets as tfds

print(tfds.list_dataset_collections())
loader = tfds.dataset_collection("xtreme")
loader.print_info()
loader.print_datasets()
```

Version selection mirrors dataset names:

```python
loader = tfds.dataset_collection("xtreme:1.0.0")
```

Useful loader methods:

| Method | Use |
|---|---|
| `loader.print_info()` | Show collection description, version, and citation |
| `loader.print_datasets()` | List member names and dataset references |
| `loader.get_dataset_info(member)` | Load metadata for one referenced dataset |
| `loader.load_dataset(member, split=...)` | Load one member through `tfds.load` |
| `loader.load_datasets([...], split=...)` | Load selected members |
| `loader.load_all_datasets(split=...)` | Load every member; potentially expensive |
| `loader.set_loader_kwargs({...})` | Reuse a consistent `tfds.load` configuration |

Loader notes:

- `load_dataset` always forces `with_info=False` internally because it standardizes return types.
- If `split` is passed both directly and in loader kwargs, the direct `split` wins.
- A collection member may carry its own `data_dir`; it is used unless explicitly overridden in loader kwargs.
- Loading all members can trigger many downloads; require user approval for broad network/storage work.

## Selecting namespace, collection, or direct load

| User intent | Best route |
|---|---|
| "I have a prepared TFDS folder." | `builder_from_directory` and external layout checks |
| "I have many prepared folders under one prefix." | community namespace with data-root paths, or direct `builder_from_directories` if it is one logical dataset |
| "I want to expose external builder code under a prefix." | community namespace with code-import path |
| "I want a benchmark suite of existing datasets." | dataset collection |
| "I just want to train on a known public dataset." | `data-loading` |
| "I need to implement a new collection class and test." | `dataset-authoring` for class/test structure, then this reference for loader behavior |
