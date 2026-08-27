# Dataset authoring troubleshooting

Use this table to diagnose custom TFDS builder and dataset collection failures. For CLI flag details, route to `cli-workflows`; for Beam scaling, route to `beam-and-performance`; for external/folder/community formats, route to `formats-and-community`.

## Skeleton and folder issues

| Symptom | Likely cause | Fix |
|---|---|---|
| Builder folder lacks `README.md`, `CITATIONS.bib`, `TAGS.txt`, test, dummy data, or `checksums.tsv`. | Incomplete skeleton or legacy non-folder layout. | Restructure as a self-contained dataset folder and add missing metadata/test/dummy-data files. |
| Many `TODO(...)`, `todo-data-url`, or template placeholders remain. | Skeleton was not fully implemented. | Resolve placeholders before implementation-mode validation. Use scaffold mode only while intentionally drafting. |
| Dummy data cannot be found. | `dummy_data/` missing, empty, or test points to the wrong `EXAMPLE_DIR`. | Put small synthetic source-layout files under the dataset folder's `dummy_data/`, or set `EXAMPLE_DIR` explicitly. |
| Tests depend on a real local checkout path. | Full paths leaked into code, tests, or dummy mappings. | Use package-relative files, dummy-data-relative test mappings, and path-like objects from the download manager. |

Run the standalone checker first:

```bash
python scripts/dataset_skeleton_check.py path/to/my_dataset --mode implementation
```

## Builder registration issues

| Symptom | Likely cause | Fix |
|---|---|---|
| `tfds.builder("my_dataset")` cannot find the custom builder. | The module defining the builder was never imported. | Import the dataset module from package initialization or explicitly import it before lookup. |
| Dataset test says builder is not registered. | Test imports the wrong module or class, or package registration is missing. | Point `DATASET_CLASS` at the actual builder class and ensure package imports register it. |
| A folder of prepared data exists but source builder is still unavailable. | Prepared data discovery is not the same as source-code registration. | Make the builder module importable; do not rely only on generated data directories. |

## `_info` and feature mismatches

| Symptom | Likely cause | Fix |
|---|---|---|
| Element spec differs from `builder.info.features`. | `_generate_examples` yields a structure or dtype different from `FeaturesDict`. | Align yielded examples with `_info` and add dummy examples for each branch. |
| `KeyError` or missing feature while generating. | Example dictionaries omit a declared key or use misspelled nested keys. | Compare every yielded key with the `FeaturesDict` structure. |
| Labels are numeric but users need names. | `ClassLabel(num_classes=...)` used despite known names. | Use `ClassLabel(names=[...])` or `names_file`. |
| Images cannot batch. | Shape is unknown or inconsistent. | Declare static shape when known, or normalize/resize data. |
| Description renders badly in generated docs. | Markdown list lacks blank lines or metadata is too terse. | Add blank lines around lists and include clear processing notes. |

## Split and key issues

| Symptom | Likely cause | Fix |
|---|---|---|
| Duplicate key error. | `_generate_examples` yields repeated keys. | Use stable source IDs, filenames, or line numbers; include split/config prefixes when necessary. |
| Key contains a local temporary path. | Code yields `str(path)` or absolute paths as keys. | Yield `path.name`, `path.stem`, a manifest ID, or another stable relative identifier. |
| Order changes across runs. | Unsorted filesystem traversal, random generation, timestamps, or nondeterministic input order. | Sort inputs and avoid randomness in keys. If source order is required, set `disable_shuffling=True` and use comparable keys. |
| Tests report overlapping splits. | Dummy records are reused or split-specific paths are ignored. | Use different fake examples per split. Whitelist only intentional overlap with `OVERLAPPING_SPLITS`. |
| User asks for arbitrary train/test split not present upstream. | Builder is trying to invent an official split. | Expose the upstream split and let loading-time sub-split APIs handle user splits. Route loading syntax to `data-loading`. |

## Download manager and manual-data issues

| Symptom | Likely cause | Fix |
|---|---|---|
| `manual_dir` access raises an error about instructions. | `MANUAL_DOWNLOAD_INSTRUCTIONS` is missing. | Add clear instructions listing required manual files. |
| Test requires private manual files. | Dummy data does not replace manual artifacts. | Use synthetic dummy data under `dummy_data/`; the test base can provide it as `manual_dir`. |
| Download mapping in test points to the wrong file. | `DL_EXTRACT_RESULT` shape does not mirror the dict/list shape passed to `download_and_extract`. | Match keys and nesting exactly, with values relative to `dummy_data/`. |
| Archive streaming loses files or is slow. | `iter_archive` file objects are consumed out of order or stored for later. | Read each yielded file object immediately during iteration. |
| Non-portable filesystem error in tests. | `open`, `os.listdir`, `os.path.exists`, or similar functions were mocked out. | Use path-like methods (`path.open`, `path.read_text`, `path.iterdir`, `path.exists`) or portable file APIs. |

## Checksum issues

| Symptom | Likely cause | Fix |
|---|---|---|
| Missing checksum failure in `DatasetBuilderTestCase`. | URL was downloaded but not recorded in `checksums.tsv`. | Register checksums during development and keep the checksum file beside the builder. |
| Non-matching checksum. | Upstream artifact changed, wrong URL, corrupted cache, or stale checksum file. | Reconfirm the provider artifact and URL. If the data changed intentionally, update the builder version and checksum file. |
| Checksum file missing from installed package. | Package data excludes `checksums.tsv`. | Include checksum files in package data. |
| `SKIP_CHECKSUMS = True` appears without explanation. | Test is bypassing deterministic download validation. | Add a reason or restore checksum validation. |

## Version/config issues

| Symptom | Likely cause | Fix |
|---|---|---|
| New code changes data but `VERSION` stayed the same. | Versioning policy was missed. | Bump patch/minor/major according to data compatibility and update `RELEASE_NOTES`. |
| Config-specific data changed but builder-level version changed only. | Versions live on configs for configurable datasets. | Put `version`, `release_notes`, and supported versions on config objects when configs own versions. |
| Default config is unexpected. | `DEFAULT_BUILDER_CONFIG_NAME` is unset, so the first config wins. | Set `DEFAULT_BUILDER_CONFIG_NAME` or reorder configs intentionally. |
| BuilderConfig description duplicates dataset description. | Config descriptions are too long or copied from `DatasetInfo`. | Keep config descriptions short and variant-specific. |

## Legacy `SplitGenerator` issues

| Symptom | Likely cause | Fix |
|---|---|---|
| New code uses list of `tfds.core.SplitGenerator`. | Copied an old example. | Prefer returning `{split_name: self._generate_examples(...)}` from `_split_generators`. |
| `gen_kwargs` do not match `_generate_examples` parameters. | Legacy split generator argument mapping is stale. | Convert to dict return form or update `gen_kwargs` names. |
| Review asks about `SplitGenerator(name, gen_kwargs=None)`. | API remains available for compatibility. | Treat it as a compatibility fact, not the preferred authoring pattern. |

## Lazy import and optional dependency issues

| Symptom | Likely cause | Fix |
|---|---|---|
| Importing the package pulls in heavy optional dependencies. | Lazy imports are accessed at module global scope. | Access heavy modules only inside functions/methods when needed. |
| Dataset-specific dependency missing during generation. | Extra is not installed or declared. | Declare the extra in the package metadata and use lazy import access in the builder. |
| Dummy test imports unavailable optional package. | Test data path still exercises heavy real parser. | Use tiny synthetic files and isolate dependency-required logic; skip only when the optional dependency is truly required. |

## Dataset collection issues

| Symptom | Likely cause | Fix |
|---|---|---|
| Collection test says collection is not registered. | Collection module is not imported or class name does not map to expected name. | Ensure the collection module is importable and registered. |
| `DatasetCollectionInfo` lacks description or release notes. | Metadata omitted or side file missing. | Provide inline metadata or include `description.md`/`citations.bib` beside the collection. |
| Referenced dataset/config/version cannot be built. | Bad `DatasetReference`, typo, missing registration, or unsupported version. | Use `naming.references_for` strings carefully and test exact versions. |
| Existing collection version was edited in place. | Versioned collection policy was missed. | Add a new collection version and keep previous mappings unchanged. |

## When to stop and reroute

- If the user wants command-line flags, build options, checksum registration commands, or dry-run command construction, use `cli-workflows`.
- If the builder is Beam-based or the problem is distributed generation/performance, use `beam-and-performance`.
- If the task is wrapping folder data, external TFRecords, HuggingFace datasets, Croissant metadata, or community catalogs, use `formats-and-community`.
- If the user only wants to read, split, decode, or inspect an existing dataset, use `data-loading`.
