# Testing and validation reference

Use this reference to verify custom TFDS dataset builders with small, local, non-copyrighted dummy data before any full generation or network-heavy run.

## Testing layers

1. **Static folder check**: validate the dataset folder shape and unresolved TODO markers with [`../scripts/dataset_skeleton_check.py`](../scripts/dataset_skeleton_check.py).
2. **Builder test**: use `tfds.testing.DatasetBuilderTestCase` with dummy data.
3. **Feature-specific tests**: use feature expectation helpers when custom feature connectors or tricky encoding behavior are involved.
4. **Safe metadata/API smoke**: instantiate the builder and inspect `builder.info` without downloading real data.
5. **Full generation**: only after the above pass, and only in a controlled temp data directory. Route command construction to `cli-workflows`.

## Dummy data policy

Dummy data should live under the dataset folder:

```text
my_dataset/
  dummy_data/
    ... small fake files matching the source layout ...
```

Rules:

- Dummy data must mimic the structure expected by `_split_generators` and `_generate_examples` after download/extract/manual-dir substitution.
- Keep it tiny: enough examples to exercise splits, configs, labels, feature branches, corrupt-record skipping, and nested structures.
- Use different fake examples in different splits. The base test checks overlap and fails when identical examples appear in multiple splits unless intentionally whitelisted.
- Do not use copyrighted source content. Use synthetic images, text, arrays, archives, labels, and manifests.
- If original data is an archive, dummy data can be an extracted layout if the test patches `download_and_extract`, or a tiny archive if extraction logic itself must be tested.
- If a dataset has manual downloads, dummy data should still be local and fake; it should not require the real manual file.

## DatasetBuilderTestCase skeleton

```python
import tensorflow_datasets as tfds
from . import my_dataset_dataset_builder


class MyDatasetTest(tfds.testing.DatasetBuilderTestCase):
  DATASET_CLASS = my_dataset_dataset_builder.Builder
  SPLITS = {
      "train": 3,
      "test": 1,
  }

  # If download/extract receives a dict, map keys to dummy_data-relative files.
  DL_EXTRACT_RESULT = {
      "train": "train",
      "test": "test",
  }


if __name__ == "__main__":
  tfds.testing.test_main()
```

Important attributes:

| Attribute | Use |
|---|---|
| `DATASET_CLASS` | Builder class object under test. Required. |
| `SPLITS` | Expected number of generated dummy examples per split. Required. |
| `VERSION` | Specific builder version to test. Optional. |
| `BUILDER_CONFIG_NAMES_TO_TEST` | Restrict configs; can contain names or config objects. Defaults to all configs. |
| `DL_EXTRACT_RESULT` | Dummy-data-relative replacement for `download_and_extract`. |
| `DL_EXTRACT_ONLY_RESULT` | Dummy-data-relative replacement for `extract` when extraction is patched separately. |
| `DL_DOWNLOAD_RESULT` | Dummy-data-relative replacement for `download`. |
| `EXAMPLE_DIR` | Alternate fake data directory. Prefer the in-folder `dummy_data/` default. |
| `OVERLAPPING_SPLITS` | Whitelist a split that intentionally reuses examples from another split. |
| `SKIP_CHECKSUMS` | Bypass checksum assertions only with a clear reason. |
| `MOCK_OUT_FORBIDDEN_OS_FUNCTIONS` | Defaults to guarding against `os`/builtin filesystem calls in favor of portable file APIs. |

## What DatasetBuilderTestCase checks

The base test exercises more than importability. It validates that:

- The class is a dataset builder and required abstract methods are implemented.
- The builder is registered enough for loading by name in the current test context.
- `builder.info` is a valid `DatasetInfo` with the expected dataset name.
- Tags are valid when metadata tags are present.
- Dummy data exists under the expected location.
- Download manager calls are patched to dummy files.
- URL checksums are registered for URLs touched by `download` or `download_and_extract`, unless explicitly skipped.
- `download_and_prepare` can serialize the dummy examples.
- `builder.as_dataset(split=...)` returns element specs matching `info.features.get_tensor_info()`.
- The generated example count matches `SPLITS` and the total example count is correct.
- Splits do not contain the same examples unless the overlap is whitelisted.
- Generated keys do not contain the local dummy-data directory path.
- Reloading generated metadata still preserves split counts and loadability.
- Builder config descriptions are not redundant with full dataset descriptions.
- `DEFAULT_BUILDER_CONFIG_NAME`, when set, points at an actual config.

## Mapping dummy data to download manager outputs

If the builder does this:

```python
paths = dl_manager.download_and_extract({
    "metadata": METADATA_URL,
    "images": IMAGES_URL,
})
return {
    "train": self._generate_examples(paths["images"] / "train", paths["metadata"]),
}
```

Then the test can map those keys to dummy-data-relative paths:

```python
DL_EXTRACT_RESULT = {
    "metadata": "metadata.json",
    "images": "images",
}
```

If the builder calls `dl_manager.download(...)` separately from `extract(...)`, use `DL_DOWNLOAD_RESULT` and `DL_EXTRACT_ONLY_RESULT` as appropriate.

## Checksums in tests

When a builder calls `dl_manager.download` or `download_and_extract`, `DatasetBuilderTestCase` records the URLs and checks that checksums exist. Normal policy:

- Keep `checksums.tsv` beside the builder.
- Register checksums during development.
- Package `checksums.tsv` with the dataset if distributing through a Python package.
- Use `SKIP_CHECKSUMS = True` only for intentional exceptions and document the reason in the test or review notes.

A missing checksum failure usually means one of:

- The dataset was never generated with checksum registration during development.
- The checksum file was not packaged or placed beside the builder.
- The test URL differs from the recorded URL after a code edit.
- The builder switched from one URL structure to another and the checksum file is stale.

## Split overlap failures

`DatasetBuilderTestCase` hashes generated examples per split and fails if examples overlap.

Fixes:

- Use distinct dummy records for train/test/validation.
- If a source dataset intentionally duplicates examples across a split such as `all`, add that split to `OVERLAPPING_SPLITS` and explain why.
- Do not paper over accidental reuse caused by a bad `DL_EXTRACT_RESULT` mapping or a generator that ignores split-specific paths.

## Key validation failures

Keys should not include local dummy-data directory paths. Bad:

```python
yield str(path), example
```

Good:

```python
yield path.name, example
```

Also avoid constant keys and unordered traversal:

```python
for path in sorted(root.glob("*.jpg")):
  yield path.stem, example
```

## Filesystem portability checks

The test base mocks many `os` and builtin filesystem functions by default to encourage portable file APIs. Use path-like objects returned by the download manager and `path.open()`, `path.read_text()`, `path.iterdir()`, or TensorFlow file APIs when necessary.

Common fixes:

- Replace `open(path)` with `path.open()` or a portable file wrapper.
- Replace `os.listdir(path)` with sorted `path.iterdir()`.
- Replace `os.path.exists(path)` with `path.exists()`.
- For NumPy loading, pass a file object rather than a plain local path when the test enforces portable I/O.

## Config tests

For many configs, the default test runs all configs. Narrow only when a full config matrix is redundant or expensive for dummy data:

```python
class MyDatasetTest(tfds.testing.DatasetBuilderTestCase):
  DATASET_CLASS = my_dataset_dataset_builder.Builder
  BUILDER_CONFIG_NAMES_TO_TEST = ["small", "large"]
  SPLITS = {"train": 2}
```

If adding a new config/version, update:

- `BUILDER_CONFIGS` in the builder.
- Dummy data or config-specific dummy mappings.
- `BUILDER_CONFIG_NAMES_TO_TEST` if the test is intentionally scoped.
- Version/release notes on the config when config versions are independent.

## Manual download tests

For builders with `MANUAL_DOWNLOAD_INSTRUCTIONS`, the test base provides dummy data as the manual directory. Ensure `_split_generators` reads `dl_manager.manual_dir` only for builders that set manual instructions.

Do not make tests depend on real login-gated or licensed artifacts.

## Feature connector tests

Use dedicated feature expectation tests when:

- A custom connector is added.
- Serialization and decoded user-facing shapes differ.
- There are custom decoders.
- Error behavior matters for invalid inputs.
- Metadata/config/proto round-trip must be proven.

A dataset builder test covers feature integration, but not every low-level connector edge case.

## Static folder validator

The bundled validator is safe to run without importing TFDS:

```bash
python scripts/dataset_skeleton_check.py path/to/my_dataset --mode implementation
```

Useful modes:

- `--mode scaffold`: accept template TODOs while checking folder shape.
- `--mode implementation`: fail unresolved skeleton TODO markers.
- `--kind collection`: validate dataset collection folders.
- `--json`: emit machine-readable results.

## Pre-handoff checklist

- Folder passes the static validator in the expected mode.
- Test file points to the actual builder class and declares all expected splits.
- Dummy data is small, synthetic, and split-disjoint.
- Download manager dummy mappings mirror the real `_split_generators` call shape.
- Checksums are present or intentionally skipped.
- Builder configs and versions have test coverage.
- No test requires network, real credentials, real manual downloads, or full dataset generation.
