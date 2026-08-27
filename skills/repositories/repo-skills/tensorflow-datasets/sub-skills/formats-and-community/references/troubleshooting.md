# Troubleshooting formats and community workflows

Start with the smallest local check: classify the source format, inspect metadata, and validate filenames before running downloads, conversions, or full generation.

| Symptom | Likely cause | Fix |
|---|---|---|
| `builder_from_directory` fails before reading examples | Missing `dataset_info.json` or `features.json` | Keep both JSON files beside the shard files; write metadata before loading |
| Feature reconstruction fails | `features.json` does not match serialized `tf.train.Example` fields | Recreate the `FeaturesDict`; compare `features.tf_example_spec` with actual serialized specs; read one example after metadata writing |
| Split slicing or `len(ds)` is wrong | Missing/stale shard lengths or split counts | Recompute split info or pass explicit `SplitInfo` values before `write_metadata` |
| Validator reports no matched shards | Wrong filename template or shards nested under a subdirectory not represented by `--template` | Pass the actual template, including subdirectories, or rename shards to the default pattern |
| Validator reports missing shard indices | A split skipped an index or declared the wrong total shard count | Rename/regenerate shards so indices are zero-based and contiguous per split |
| Validator reports metadata split mismatch | `dataset_info.json` split list differs from shard filenames | Rewrite metadata using split info computed from the final shard set |
| `builder_from_directories` gives inconsistent totals | One folder has different schema, dataset name, version, split naming, or file format | Normalize each folder independently and validate before merging |
| `ImageFolder` misses examples | Unsupported extension or wrong `split/label/file` depth | Use `.jpg`, `.jpeg`, or `.png` files directly under split/label folders |
| `ImageFolder` labels are surprising | Labels are inferred from directory names and sorted | Rename label folders before building; do not expect labels from filenames |
| `ImageFolder` cannot express sidecar annotations | The data is not plain image classification | Use a custom builder in `dataset-authoring` |
| `TranslateFolder` raises count mismatch | Language files for one split have different numbers of lines | Align all `language.split.txt` files so one line equals one example |
| `TranslateFolder` is memory-heavy | It loads all examples during initialization | Use a streaming/generator builder for large corpora |
| `as_data_source` raises unsupported format | The stored file format is not random-access | Use `as_dataset`, or prepare data in a supported random-access format such as ArrayRecord or Parquet |
| ArrayRecord cannot be loaded with `as_dataset` | ArrayRecord is random-access only in this TFDS path | Use `as_data_source` or choose a TensorFlow-readable file format |
| `store_as_tfds_dataset` rejects split inputs | Splits use mixed input types or no splits were provided | Keep all split values as the same kind of input and provide at least one split |
| Stored dataset already exists | `AdhocBuilder` refuses to overwrite an existing prepared dataset by default | Choose a new version/config/data directory, or explicitly plan an overwrite through safe CLI/build workflows |
| HuggingFace load fails immediately | Missing optional package, network block, gated repository, missing token, or unsupported config | Confirm package/cache/token constraints; pass approved token; materialize only after user accepts network/cache cost |
| HuggingFace name does not resolve | Namespace syntax or TFDS-safe normalization mismatch | Use `huggingface:dataset_name` for namespace loading; check config names separately |
| HuggingFace generation has partial failures | Dataset-specific examples raise during retrieval | Avoid `ignore_hf_errors` unless the user explicitly accepts dropped/partial examples |
| Croissant sees no record sets | Wrong `record_set_ids` or JSON-LD has no usable record sets | Inspect available record-set ids and pass exact ids, or fix the Croissant metadata |
| Croissant local files are not found | `mapping` keys do not match file-object names | Map exact Croissant filenames to local files; do not map by arbitrary display names |
| Croissant output has only `default` split | Metadata lacks a joined split record set for the selected record set | Accept the default split or revise Croissant metadata before conversion |
| Croissant output is empty | Filters exclude all records | Remove filters, then reapply one filter at a time |
| CoNLL row mismatch | Input row has a different number of columns from the config's ordered features | Fix separator/column order or use a custom preprocessing path |
| CoNLL-U parsing fails | Non-standard tokenization or unsupported morphology | Add a `process_example_fn` or route detailed builder implementation to `dataset-authoring` |
| Community namespace not found | Missing namespace entry, disabled community dataset visibility, or unavailable namespace path | Correct `community-datasets.toml` and verify path accessibility |
| Community registry path error | One namespace mixes code-import paths and prepared-data roots | Split code and data roots into separate namespaces |
| Community module import finds zero/multiple builders | The module does not expose exactly one concrete `DatasetBuilder` | Fix the external module or route builder implementation/debugging to `dataset-authoring` |
| Dataset collection member load fails | The collection references a missing dataset/config/version or broad load kwargs are incompatible | Use `loader.print_datasets()`, then load the referenced dataset directly with narrowed kwargs |
| Loading all collection members is expensive | `load_all_datasets` calls `tfds.load` for each member | Ask before broad downloads; load a small subset first |

Escalate to another sub-skill when the fix is custom builder authoring, command construction, Beam/cloud scaling, or plain split/decode/loading behavior rather than format/community routing.
