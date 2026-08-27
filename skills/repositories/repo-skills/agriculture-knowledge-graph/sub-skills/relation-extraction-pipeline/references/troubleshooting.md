# Relation extraction troubleshooting

Use this table to diagnose workflow-specific failures before rerunning alignment, preprocessing, or training.

## Dataset row and preprocessing failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ValueError` from `preprocessing.py datasetjson` | A line in `filtered_data.txt` does not split into exactly six tab-separated fields. | Run the schema checker on the TSV. Remove headers, fix embedded tabs/newlines, and normalize rows to six columns. |
| Header text appears as an entity or relation | Upstream `train_data.txt` header was not removed before preprocessing. | Remove the header before `datasetjson`; the source converter does not skip it. |
| `KeyError` in `dosomething.py filter_dataset` for an entity name | A row references an entity missing from `entities.txt`. | Add the entity with a correct label id or drop the row. Recreate `entity2id.json` after changing `entities.txt`. |
| `IndexError` while creating `entity2id.json` | `entities.txt` has a blank or malformed line. | Ensure every nonblank line has at least two whitespace-separated fields: entity and label id. |
| `country-code.json` missing or malformed | `filter_dataset` expects a JSON list with `cn` country names. | Provide a tiny or full `country-code.json`, or adapt the filter when country filtering is not desired. |
| Expected relations are missing after filtering | `filter_dataset` keeps only a hard-coded relation list. | Edit the relation list deliberately and keep `rel2id.json` in sync. Do not assume `staticResult.txt` controls the kept labels. |
| Duplicate handling removes too much data | Original helper uses `uniq -u`, which drops all copies of duplicated rows. | Use the bundled dedup script with `--mode keep-first` or `--mode sort-unique` unless you explicitly want `drop-all-duplicates`. |
| `dataset_split` crashes or stops early on NA rows | It assumes 2,000 train NA examples and 500 test NA examples. | Generate enough `NA_SAMPLE.txt` rows or edit the constants for a tiny split. |

## Position and segmentation failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `[ERROR] Position error` from the data loader | `head.pos` or `tail.pos` is not a character offset into the sentence, or quotes/whitespace changed the offset. | Validate with the schema checker. Strip one pair of wrapper quotes if needed, recompute offsets, and regenerate `dataset.json`. |
| Entity appears in sentence but loader cannot locate it after Jieba segmentation | The offset points to a later/earlier duplicate mention, or the row uses token offsets rather than character offsets. | Recompute offsets against the exact `sentence` string stored in JSON. For duplicate mentions, ensure the intended occurrence is selected. |
| Many long sentences train poorly | `max_length` defaults to 60 and truncates longer examples. | Inspect length distribution, consider filtering or increasing `max_length`, then delete `_processed_data` and rerun preprocessing. |

## JSON and vector failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `word2vec file doesn't exist` | Training ran from the wrong directory or files were not copied to `data/agriculture`. | Run from the algorithm directory and verify `data/agriculture/word2vec.json` exists. |
| Numeric conversion or NumPy assignment error while loading vectors | `word2vec.json` has inconsistent vector dimensions or nonnumeric values. | Validate with `--word2vec-json`; rebuild the vector JSON from a clean text embedding or a tiny fixture. |
| Out-of-memory during vector conversion or loader preprocessing | Full Chinese word-vector files are large and conversion creates both JSON and NumPy matrix copies. | Use a limited vocabulary for smoke tests. For full training, budget RAM/disk and avoid repeated conversions. |
| Old data persists after editing JSON or config | `_processed_data` cache is stale. | Delete `_processed_data` in the training working directory before rerunning the loader. |
| Unknown relation labels silently become `NA` | Loader maps any relation not in `rel2id.json` to `NA`. | Treat unknown relations as validation errors before training unless intentionally folding them into NA. |

## Fire command and path failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ERROR: Could not consume arg: rel2id` or similar Fire error | README command names differ from the script's Fire map. | Use `rel2json`, `datasetjson`, `word2vecjson`, `na_datasetjson`, `entity2id`, or `dataset_split`. |
| `filter_dataset` command not found in `preprocessing.py` | It is defined in `dosomething.py`. | Run `python dosomething.py filter_dataset` from the relation data directory. |
| `Data file doesn't exist` from loader | `config.root_path` was set from the wrong current working directory. | Run training from the algorithm directory or edit paths in `config.py`. |
| `Dataset dir ... data/nyt ... doesn't exist` while intending agriculture training | `train.py` checks the hard-coded `dataset = "nyt"` variable even though loaders use agriculture files. | Patch `dataset = "agriculture"` and fix model naming before training. Do not rely on the unused CLI argument. |

## TensorFlow and GPU failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No module named tensorflow` | TensorFlow training stack was not installed for the lightweight inspection environment. | Prepare a separate TensorFlow 1.x-compatible environment only if training is required. |
| `module 'tensorflow' has no attribute 'contrib'` | TensorFlow 2.x is installed. | Use TensorFlow 1.x-era code/runtime or port all `tf.contrib`, `tf.layers`, session, and placeholder usage. |
| CUDA/cuDNN load errors | TensorFlow 1.x GPU wheel does not match host CUDA/cuDNN/GPU generation. | Use a matching legacy CUDA stack, a vetted container, or adapt to a modern framework. Document any CPU-only fallback as unverified for GPU training. |
| GPU out-of-memory or other jobs are disrupted | Config uses `per_process_gpu_memory_fraction = 1.0`. | Lower the fraction, limit visible devices, or use a dedicated GPU allocation before training. |
| Assertion failure on batch size and GPUs | `batch_size % len(gpu_list) != 0`. | Change `batch_size` or `gpu_list` so the batch divides evenly across towers. |
| Training starts but metrics are meaningless | Tiny fixtures or relation ids do not represent the real distribution. | Use tiny fixtures only for smoke tests; reserve quality claims for a documented full dataset and recovery target. |

## Upstream alignment and service failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Alignment script cannot query relations | Neo4j relation data was not imported or service credentials/config differ. | Route to the graph/crawler workflows for import and service setup before retrying alignment. |
| Alignment scan appears hung | It recursively scans a Chinese Wikipedia extraction and queries entity pairs; it is expected to be slow. | Use a bounded corpus, add progress logging, or run the parallel variant only after resource planning. |
| Relation-label annotation data is needed | The Django/Mongo tagging UI owns annotation collection. | Route UI and Mongo service setup to the web-app workflow; use this sub-skill only for resulting row/JSON formats. |

## Quick triage commands

```bash
# Built-in tiny fixture for the schema checker.
python sub-skills/relation-extraction-pipeline/scripts/relation_dataset_schema_check.py --self-test

# Show deduplication helper options.
sub-skills/relation-extraction-pipeline/scripts/deduplicate_training_rows.sh --help

# Validate a local dataset without TensorFlow.
python sub-skills/relation-extraction-pipeline/scripts/relation_dataset_schema_check.py \
  --training-tsv relationExtraction/data/filtered_data.txt \
  --rel2id relationExtraction/data/rel2id.json \
  --entity2id relationExtraction/data/entity2id.json \
  --dataset-json relationExtraction/data/dataset.json
```
