# OpenFlamingo data-preparation workflows

Use these workflows from a directory where you can reference this sub-skill's `scripts/` directory. Replace placeholder paths with user-provided dataset locations. The commands are designed to be safe preflights; full conversion, training, and evaluation remain expensive and data-dependent.

## 1. Validate MMC4 metadata before conversion

Run a bounded schema check against either a plain JSON/JSONL file or an MMC4 ZIP shard. The validator does not decode all images or scan an entire dataset by default.

```bash
python scripts/validate_open_flamingo_data.py \
  --mode mmc4-json \
  --input-path data/mmc4-zips/shard_0.zip \
  --max-records 50
```

Expected success signals:

- `checked_records` is greater than zero.
- The report lists `text_list`, `similarity_matrix`, and `image_info` checks as passed.
- Missing `image_base64` is acceptable for pre-conversion ZIP metadata when `image_name` exists.

If validating an already converted JSON sample, at least one `image_info` entry should contain `image_base64`.

## 2. Convert MMC4 ZIP shards plus downloaded images to WebDataset tar shards

Inputs:

- Downloaded MMC4 ZIP metadata shards.
- Downloaded raw image files arranged as `<image_dir>/<zip-position>/<image_name>`.
- Enough local disk space for tar shards containing base64-encoded JPEG data.

Command:

```bash
python scripts/convert_mmc4_to_wds.py \
  --output_dir data/mmc4-wds \
  --zip_files 'data/mmc4-zips/shard_{0..9}.zip' \
  --image_dir data/mmc4-images \
  --num_files_per_shard 5
```

Important details:

- Keep the `--zip_files` brace expression quoted unless you intentionally want the shell to expand it before Python starts.
- The converter uses `braceexpand` and preserves the expanded order. The zero-based position in that expanded list selects the image subdirectory.
- The converter reads the first JSON member in each ZIP and processes it line by line.
- Missing image files are warned about and the corresponding `image_base64` field is omitted, matching the tolerant native behavior. Training-time preprocessing later drops records with no usable images.
- `--num_files_per_shard` controls how many input ZIP shards are written before the WebDataset writer advances to the next output tar stream.

After conversion, validate shard names cheaply:

```bash
python scripts/validate_open_flamingo_data.py \
  --mode webdataset-name \
  --input-path 'data/mmc4-wds/{000000000..000000001}.tar'
```

Then pass the produced tar brace pattern to training as `--mmc4_shards` when the user has requested training.

## 3. Check LAION shard assumptions before training

This sub-skill does not download LAION. Before training, confirm that the user-provided LAION WebDataset tar shards were built with image/text pairs:

```text
sample-key.txt
sample-key.jpg      # or .jpeg / .png
```

Cheap checks:

```bash
python scripts/validate_open_flamingo_data.py \
  --mode webdataset-name \
  --input-path 'data/laion/shard-{0000..0009}.tar'
```

For a deeper local inspection, list a tiny tar header sample with standard tools instead of extracting the dataset:

```bash
tar -tf data/laion/shard-0000.tar | sed -n '1,20p'
```

Look for paired `.txt` and `.jpg`/`.jpeg`/`.png` suffixes sharing sample keys.

## 4. Validate VQA-style prediction JSON

Before result filling, validate the prediction list produced by an evaluation run:

```bash
python scripts/validate_open_flamingo_data.py \
  --mode vqa-predictions \
  --input-path outputs/vqav2_testdev_predictions.json \
  --max-records 1000
```

Expected input shape:

```json
[
  {"question_id": 123, "answer": "two dogs"}
]
```

The validator checks list shape, required keys, duplicate IDs within the inspected prefix, and answer types. It does not require predictions for every final test question; that is the filler script's job.

## 5. Fill VQAv2 test/test-dev results

EvalAI-style VQAv2 submissions require an answer for every question in the full test questions file, not only the test-dev subset that may have been predicted.

```bash
python scripts/fill_vqa_testdev_results.py \
  --dataset vqav2 \
  --input_path outputs/vqav2_testdev_predictions.json \
  --vqa_test_questions_json_path data/vqav2/v2_OpenEnded_mscoco_test2015_questions.json \
  --output_path outputs/vqav2_test2015_filled.json
```

Output shape:

```json
[
  {"question_id": 123, "answer": "two dogs"},
  {"question_id": 124, "answer": ""}
]
```

The output is ordered exactly as the full test questions file. Predictions for question IDs not present in that file are ignored with a warning.

## 6. Fill VizWiz test results

VizWiz output from the native helper uses the image filename key rather than `question_id` in the final file.

```bash
python scripts/fill_vqa_testdev_results.py \
  --dataset vizwiz \
  --input_path outputs/vizwiz_test_predictions.json \
  --vqa_test_questions_json_path data/vizwiz/test_questions_vqa_format.json \
  --output_path outputs/vizwiz_test_filled.json
```

Output shape:

```json
[
  {"image": "VizWiz_test_00000000.jpg", "answer": "can"},
  {"image": "VizWiz_test_00000001.jpg", "answer": ""}
]
```

## 7. Use TextVQA/VizWiz converted annotation files

For VizWiz and TextVQA evaluation, use VQA-format converted questions/annotations. The expected file names typically follow:

```text
train_questions_vqa_format.json
train_annotations_vqa_format.json
val_questions_vqa_format.json
val_annotations_vqa_format.json
```

VizWiz also has a `test_questions_vqa_format.json` for final/test submissions. TextVQA image IDs are string stems and images are read as `<image_id>.jpg`.

## Safety notes

- Do not run full MMC4 conversion unless the user has provided local ZIP shards, image downloads, and sufficient disk capacity.
- Do not claim that training/evaluation was executed from `--help`, validation, or tiny synthetic tests.
- Avoid loading huge questions or annotations repeatedly. Use bounded validators or read small prefixes for schema checks.
- When final evaluation is requested, remember that the evaluation runtime also needs model weights, images, Python dependencies, and the VQA-style annotation paths. Some evaluation workflows require `scikit-learn` even when the base package metadata does not install it automatically.
