# Builder authoring reference

This reference distills the TFDS authoring workflow into a self-contained checklist for custom dataset builders.

## Folder shape expected from a standard skeleton

A normal custom dataset folder should be self-contained:

```text
my_dataset/
  __init__.py
  README.md
  CITATIONS.bib
  TAGS.txt
  checksums.tsv
  dummy_data/
  my_dataset_dataset_builder.py
  my_dataset_dataset_builder_test.py
```

Policy:

- Put implementation, README, citations, tags, checksums, dummy data, and tests in the same folder.
- Do not split a new dataset across category-level files such as `category/my_dataset.py` plus separate fake-data/checksums paths.
- Do not depend on the original source checkout when packaging a custom dataset. Metadata and dummy inputs needed for tests should travel with the dataset folder.
- Keep generated skeleton TODO markers only while scaffolding. Before claiming an implementation is ready, resolve the placeholder data URL, homepage, README, citation, tags, dummy data, and test TODOs.

Use [`../scripts/dataset_skeleton_check.py`](../scripts/dataset_skeleton_check.py) for a standalone folder-shape and TODO-marker check.

## Standard builder anatomy

A small or medium dataset usually subclasses `tfds.core.GeneratorBasedBuilder`:

```python
import tensorflow_datasets as tfds


class Builder(tfds.core.GeneratorBasedBuilder):
  """DatasetBuilder for my_dataset."""

  VERSION = tfds.core.Version("1.0.0")
  RELEASE_NOTES = {
      "1.0.0": "Initial release.",
  }

  def _info(self) -> tfds.core.DatasetInfo:
    return self.dataset_info_from_configs(
        features=tfds.features.FeaturesDict({
            "image": tfds.features.Image(shape=(256, 256, 3)),
            "label": tfds.features.ClassLabel(names=["cat", "dog"]),
        }),
        supervised_keys=("image", "label"),
        homepage="DATASET_HOMEPAGE",
    )

  def _split_generators(self, dl_manager: tfds.download.DownloadManager):
    paths = dl_manager.download_and_extract({
        "train": TRAIN_ARCHIVE_URL,
        "test": TEST_ARCHIVE_URL,
    })
    return {
        "train": self._generate_examples(paths["train"]),
        "test": self._generate_examples(paths["test"]),
    }

  def _generate_examples(self, path):
    for image_path in sorted(path.glob("*.jpg")):
      label = image_path.parent.name
      yield image_path.stem, {"image": image_path, "label": label}
```

The inspected package supports `tfds.core.GeneratorBasedBuilder(*, file_format=None, **kwargs)`. Pass `file_format` only when you intentionally choose a supported storage format; otherwise leave it at the default selected by the builder stack.

## `_info`: declare public dataset metadata

`_info` should return a `tfds.core.DatasetInfo` or, for skeleton-style builders, `self.dataset_info_from_configs(...)`.

The inspected `DatasetInfo` signature is:

```text
tfds.core.DatasetInfo(
  *, builder, description=None, features=None, supervised_keys=None,
  disable_shuffling=False, nondeterministic_order=False, homepage=None,
  citation=None, metadata=None, license=None, redistribution_info=None,
  split_dict=None, alternative_file_formats=None, is_blocked=None
)
```

Authoring rules:

- `features` is required for practical builders. It defines the nested structure, tensor shapes, dtypes, and connector metadata users will see when loading the dataset.
- Prefer `self.dataset_info_from_configs(...)` when the folder has metadata files. It attaches the builder and pulls folder metadata consistently.
- Use `supervised_keys=(input_key, target_key)` only when there is a natural supervised tuple.
- Use `disable_shuffling=True` only when record order is semantically important. It preserves key-sorted order but reduces read parallelism.
- Use `nondeterministic_order=True` only when the builder's generation path intentionally trades deterministic write order for speed; do not use it to hide unstable keys.
- Put processing notes in the description when examples were skipped, cropped, normalized, filtered, or otherwise transformed.

## Versions and release notes

The inspected version constructor is:

```text
tfds.core.Version(version, experiments=None, tfds_version_to_prepare=None)
```

Use semantic code versions:

- Patch bump: serialized layout or metadata changed, but users reading a fixed slice get the same examples.
- Minor bump: compatible additions, such as an added feature, while old examples and slices remain stable.
- Major bump: example contents, split membership, keys, or slicing semantics changed.

Always maintain `RELEASE_NOTES` for every public version:

```python
VERSION = tfds.core.Version("2.0.0")
RELEASE_NOTES = {
    "1.0.0": "Initial release.",
    "2.0.0": "Fix label parsing and regenerate examples.",
}
```

Older generated datasets can usually be read if they already exist on disk, but only the current canonical version is normally prepared. Do not silently change data without a version bump.

## Builder configs

The inspected `BuilderConfig` signature is:

```text
tfds.core.BuilderConfig(
  name, version=None, release_notes=None, supported_versions=<factory>,
  description=None, tags=<factory>
)
```

Use configs for externally meaningful variants such as language, year, preprocessing choice, image size, or official dataset edition:

```python
import dataclasses


@dataclasses.dataclass
class MyDatasetConfig(tfds.core.BuilderConfig):
  image_size: tuple[int, int] = (0, 0)


class Builder(tfds.core.GeneratorBasedBuilder):
  BUILDER_CONFIGS = [
      MyDatasetConfig(
          name="small",
          version=tfds.core.Version("1.0.0"),
          release_notes={"1.0.0": "Initial small variant."},
          description="Small 64x64 images.",
          image_size=(64, 64),
      ),
      MyDatasetConfig(
          name="large",
          version=tfds.core.Version("1.0.0"),
          release_notes={"1.0.0": "Initial large variant."},
          description="Large 256x256 images.",
          image_size=(256, 256),
      ),
  ]
```

Rules:

- Give every config a unique `name` and short one-line `description`.
- Access config-specific values with `self.builder_config` inside `_info`, `_split_generators`, and `_generate_examples`.
- If configs have their own code/data versions, put `version`, `release_notes`, and `supported_versions` on the config objects.
- If no config is specified, TFDS defaults to the first config unless `DEFAULT_BUILDER_CONFIG_NAME` is set.

## `_split_generators`: downloads and split declaration

`_split_generators(self, dl_manager)` should download or locate source artifacts, then return split names mapped to example generators.

Modern pattern:

```python
def _split_generators(self, dl_manager):
  root = dl_manager.download_and_extract(DATA_ARCHIVE_URL)
  return {
      "train": self._generate_examples(root / "train"),
      "test": self._generate_examples(root / "test"),
  }
```

The inspected `DownloadManager` exposes:

- `download(url_or_urls)` for supported URL resources.
- `extract(path_or_paths)` for archives.
- `download_and_extract(url_or_urls)` as the common combined path.
- `iter_archive(resource)` to stream archive members without extracting everything.
- `manual_dir` for datasets that require users to manually obtain files.

`download`, `extract`, and `download_and_extract` accept a single value or nested `list`/`dict` structures and return the same structure of path-like objects.

Split rules:

- Preserve official source splits. If the source supplies train/test/validation, expose those names.
- If the source has no official split, expose one split such as `train` or `all` and let users create sub-splits when loading.
- Do not create arbitrary random train/test splits inside the builder unless the upstream dataset defines them.
- The order of returned split keys is the order saved in `builder.info.splits`.
- Download all source files in `_split_generators`; do record-level parsing in `_generate_examples`.

### Legacy `SplitGenerator`

The inspected package still exposes:

```text
tfds.core.SplitGenerator(name, gen_kwargs=None)
```

Existing builders and tests may use a list of `SplitGenerator` objects, but new builders should prefer the explicit dictionary form:

```python
# Prefer this for new code.
return {"train": self._generate_examples(path=train_path)}

# Legacy compatibility only.
return [tfds.core.SplitGenerator(name="train", gen_kwargs={"path": train_path})]
```

## Manual downloads

Use manual downloads only when the dataset cannot be fetched automatically because of login, license, or user agreement requirements.

```python
class Builder(tfds.core.GeneratorBasedBuilder):
  MANUAL_DOWNLOAD_INSTRUCTIONS = """
  Download data.zip from the dataset provider after accepting the license.
  Place data.zip in the manual download directory.
  """

  def _split_generators(self, dl_manager):
    archive_path = dl_manager.manual_dir / "data.zip"
    root = dl_manager.extract(archive_path)
    return {"train": self._generate_examples(root / "train")}
```

If `MANUAL_DOWNLOAD_INSTRUCTIONS` is missing, `dl_manager.manual_dir` access raises an error. Tests should use dummy data and avoid needing private files.

## `_generate_examples`: stable keys and feature dictionaries

`_generate_examples` yields `(key, example)` pairs:

```python
def _generate_examples(self, root):
  for row in read_manifest(root / "labels.csv"):
    key = row["example_id"]
    yield key, {
        "image": root / "images" / f"{key}.jpg",
        "label": row["label"],
    }
```

Key rules:

- Unique: duplicate keys fail generation.
- Deterministic: keys must not depend on temporary directories, unordered filesystem traversal, randomized state, or local absolute paths.
- Comparable: if shuffling is disabled, TFDS sorts by key.
- Safe choices include source IDs, stable filenames such as `path.name`, or line numbers from a deterministic input file.
- Bad choices include full local paths, `os.listdir()` order without sorting, random numbers, timestamps, and constant placeholders such as `"key"`.

Example rules:

- The example dictionary must match the nested structure declared in `_info().features`.
- Feature connectors encode acceptable raw values automatically: images can often be paths, arrays, bytes, or file-like content depending on connector type.
- Parse booleans carefully; avoid Python's `bool("False")` behavior.
- For archive streaming, consume file objects in the iteration order provided by `dl_manager.iter_archive`.

## Registration

A custom dataset must be importable before `tfds.load("my_dataset")` can find it by name. In a package-local dataset collection, registration usually means importing the dataset module from the containing package's `__init__.py` or explicitly importing it before calling `tfds.builder`/`tfds.load`.

Do not treat a generated data directory alone as source-code registration. Prepared data can be discovered for reading, but authoring/debugging the builder still requires importable builder code.

## Checksums

For downloadable datasets, keep `checksums.tsv` in the dataset folder. Register checksums during development, then commit or package the file with the dataset.

Rules:

- If `_split_generators` calls `dl_manager.download` or `download_and_extract`, tests expect those URLs to have checksums unless `SKIP_CHECKSUMS = True` is intentionally set.
- Do not skip checksum validation to hide unstable URLs. Use a clear note if the URL is intentionally un-checksummed.
- When releasing via a package, make sure `checksums.tsv` is included as package data.

For command details, route to `cli-workflows`; this sub-skill only owns the authoring policy.
