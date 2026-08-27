# Dataset collections reference

Dataset collections group existing TFDS datasets into versioned benchmark or task bundles. A collection is not a dataset builder and does not generate examples; it exposes metadata and versioned dataset references.

## Folder shape

A collection folder should be self-contained:

```text
my_collection/
  __init__.py
  my_collection.py
  my_collection_test.py
  description.md      # optional if description is in code
  citations.bib       # optional if citation is in code
```

Rules:

- The collection implementation, metadata, and test live in the same folder.
- Use a collection only when the deliverable is a named, versioned set of datasets. Do not use it for custom example generation.
- The referenced datasets should already be importable or available through the package's registration mechanism.

## Minimal collection implementation

```python
import collections
from typing import Mapping

from tensorflow_datasets.core import dataset_collection_builder
from tensorflow_datasets.core import naming


class MyCollection(dataset_collection_builder.DatasetCollection):
  """Dataset collection for a benchmark bundle."""

  @property
  def info(self) -> dataset_collection_builder.DatasetCollectionInfo:
    return dataset_collection_builder.DatasetCollectionInfo.from_cls(
        dataset_collection_class=self.__class__,
        description="A benchmark bundle for my task.",
        release_notes={
            "1.0.0": "Initial release.",
            "1.1.0": "Add an extra evaluation dataset.",
        },
    )

  @property
  def datasets(
      self,
  ) -> Mapping[str, Mapping[str, naming.DatasetReference]]:
    return collections.OrderedDict({
        "1.0.0": naming.references_for({
            "train_task": "dataset_a/default:1.0.0",
            "eval_task": "dataset_b:2.1.0",
        }),
        "1.1.0": naming.references_for({
            "train_task": "dataset_a/default:1.0.0",
            "eval_task": "dataset_b:2.1.0",
            "challenge": "dataset_c/special:3.0.0",
        }),
    })
```

## Collection metadata

`DatasetCollectionInfo` contains:

- `name`: derived from the collection class name.
- `description`: markdown text, either passed in code or read from `description.md`.
- `release_notes`: mapping of collection version to notes.
- `citation`: optional BibTeX, either passed in code or read from `citations.bib`.
- `homepage`: optional homepage.

Use `DatasetCollectionInfo.from_cls(...)` so the collection name and optional side files are resolved consistently.

Metadata rules:

- Description should explain the benchmark/task and selection criteria, not just list names.
- Release notes should say what changed between collection versions.
- Citation should cite the collection or benchmark paper when applicable; individual datasets may have their own citations through their builders.
- Keep side-file metadata packaged with the collection folder.

## Dataset references

The `datasets` property returns:

```text
Mapping[collection_version, Mapping[collection_member_name, DatasetReference]]
```

Preferred concise form:

```python
naming.references_for({
    "member_name": "dataset_name/config_name:version",
})
```

Equivalent explicit form:

```python
{
    "member_name": naming.DatasetReference(
        dataset_name="dataset_name",
        config="config_name",
        version="1.0.0",
    ),
}
```

Rules:

- Version every collection release.
- Use explicit dataset versions for reproducibility when the collection is meant to be stable.
- Use clear member names such as `train`, `validation`, `task_name`, or benchmark subset names.
- Keep ordering stable; use an ordered mapping if the order has meaning.
- If a later collection release replaces a dataset version/config, keep the older collection version instead of mutating it in place.

## Testing collections

A minimal collection test:

```python
from tensorflow_datasets.testing.dataset_collection_builder_testing import DatasetCollectionTestBase
from . import my_collection


class TestMyCollection(DatasetCollectionTestBase):
  DATASET_COLLECTION_CLASS = my_collection.MyCollection
```

Optional attributes:

| Attribute | Use |
|---|---|
| `VERSION` | Test a specific collection version. Defaults to the latest. |
| `DATASETS_TO_TEST` | Restrict existence checks to selected member names. Defaults to all. |
| `CHECK_DATASETS_VERSION` | If false, check default dataset versions instead of exact referenced versions. Defaults to true. |

The base test checks:

- The collection is registered.
- `info` is a populated `DatasetCollectionInfo`.
- Referenced datasets exist as builders.
- Referenced dataset configs/versions can be instantiated when `CHECK_DATASETS_VERSION` is true.

## Common collection authoring decisions

### Add a new dataset to a collection

- Add a new collection version instead of modifying the existing version.
- Update `release_notes` for the new collection version.
- Add the reference under the new version only.
- Add or update the collection test if the new dataset has optional registration constraints.

### Update a referenced dataset version

- Add a new collection version.
- Keep the old version's mapping untouched.
- Explain whether the update changes examples, labels, preprocessing, or only metadata.

### Use side files or inline metadata

- Inline `description`/`citation` is convenient for short collections.
- Side files are better for long descriptions and large citations.
- Do not mix conflicting side files and inline metadata; the inline value wins when supplied.

## Collection vs dataset builder

Use a dataset collection when the task is to define a versioned set of existing datasets. Use a dataset builder when the task is to parse source artifacts into examples.

If the user asks for both a custom dataset and a benchmark bundle:

1. Author and test the custom dataset builder first.
2. Ensure it is importable by name.
3. Add a collection reference to that dataset/config/version.
4. Add a collection test.

## Static validation

The bundled validator can check basic collection shape without importing TFDS:

```bash
python scripts/dataset_skeleton_check.py path/to/my_collection --kind collection --mode implementation
```

It checks for the collection implementation file, metadata shape, unresolved TODO markers, and a collection test when present.
