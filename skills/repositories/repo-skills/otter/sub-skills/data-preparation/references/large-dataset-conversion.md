# Large dataset conversion safety

Otter data preparation includes three large-data patterns:

1. legacy MIMIC-IT image JSON to parquet;
2. MMC4-style document/image shards to WebDataset tar shards;
3. LAION TSV image/text pairs to WebDataset tar shards.

Only the JSON-to-parquet helper is bundled as a runnable script. WebDataset conversions are described as planning guidance because they can create many large tar files and require explicit user approval, paths, and disk budget.

## Base64 image JSON to parquet

MIMIC-IT originally allowed image JSON files mapping image id to base64 string. Parquet is preferred because it reduces load overhead and exposes a `base64` column that the loader can index by image id.

Use:

```bash
python ../scripts/convert_base64_json_to_parquet.py images.json images.parquet --validate-sample 8
```

For large outputs, write a partitioned parquet directory:

```bash
python ../scripts/convert_base64_json_to_parquet.py images.json images_parquet_dir --rows-per-partition 250000 --validate-sample 16 --overwrite
```

Safety notes:

- The input JSON is still loaded as one object, so confirm memory budget before processing very large files.
- Use a partition size that keeps each parquet part below roughly 2 GB.
- Keep the output index equal to image id; instruction `image_ids` depend on it.
- Validate a sample of base64 payloads before a long conversion.
- Write to a new output path or use `--overwrite` intentionally.

## MMC4-style WebDataset planning

The large MMC4 conversion pattern combines document JSONL shards with matching image tar shards and writes WebDataset tar outputs. The source utility behavior was:

- expand document shard and image shard brace patterns;
- require the number of document shards to match the number of image shards;
- open each image tar;
- for each JSONL document, read image names from `image_info`;
- embed base64 image bytes into each image_info entry as `image_base64`;
- write samples with keys `__key__` and `json` to sharded tar files;
- use tar shard limits around tens of thousands of records and about 10 GB per output shard.

Before running any equivalent conversion, confirm:

1. shard patterns expand to matching ordered lists;
2. image names in each JSONL file exist in the paired tar;
3. output directory has enough free disk for tar shards;
4. interruption policy is clear, because partial tar outputs may need removal or resume handling;
5. downstream training arguments use the produced WebDataset shard pattern rather than MIMIC-IT YAML.

## LAION TSV to WebDataset planning

The LAION-style conversion pattern reads paired TSV files for images and captions, verifies matching keys, and writes WebDataset tar shards. The source utility behavior was:

- create or read line indexes for TSV files;
- pair `image` TSV files with corresponding `text` TSV files;
- parse caption JSON and use the first caption;
- write samples with `__key__`, `png`, and `txt` entries;
- skip rows with missing or malformed captions;
- write tar shards with large max-count/max-size limits;
- process a selected interval of input TSV shards with a bounded worker count.

Before running any equivalent conversion, confirm:

1. line indexes exist or can be generated safely;
2. image and caption TSVs are paired and sorted consistently;
3. caption JSON structure is known;
4. worker count is below file descriptor and memory limits;
5. shard interval and resume point are recorded;
6. output tar pattern is compatible with the training data arguments.

## Choosing MIMIC-IT YAML vs WebDataset shards

| Data type | Use |
|---|---|
| MIMIC-IT instruction JSON + base64 images | MIMIC-IT YAML with `mimicit_path` and `images_path`; validate with this sub-skill. |
| MMC4 interleaved documents | WebDataset shard arguments for MMC4-style pretraining; route command construction to [training](../../training/SKILL.md). |
| LAION/CC3M image-caption pairs | WebDataset shard arguments for LAION/CC3M pretraining; route command construction to [training](../../training/SKILL.md). |

## Operational guardrails

- Ask for explicit permission before starting any conversion expected to exceed minutes, gigabytes, or external download/API access.
- Prefer dry runs with tiny shard intervals or small JSON fixtures.
- Keep conversion logs outside the runtime skill tree.
- Check path collisions before writing outputs.
- If the conversion is interrupted, inspect output integrity before resuming. Do not silently append to a corrupt shard directory.
- After producing MIMIC-IT parquet, validate YAML id links with [validate_mimicit_yaml.py](../scripts/validate_mimicit_yaml.py).
