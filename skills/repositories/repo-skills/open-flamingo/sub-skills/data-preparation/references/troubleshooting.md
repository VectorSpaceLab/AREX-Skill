# OpenFlamingo data-preparation troubleshooting

## MMC4 conversion issues

### Symptom: many `Did not find ... downloaded` warnings

Likely causes:

- The raw MMC4 image downloader encountered dead URLs or skipped files.
- `--image_dir` does not match the expected `<image_dir>/<zip-position>/<image_name>` layout.
- The ZIP brace expansion order does not match the image subdirectory numbering.

Actions:

1. Inspect the first expanded ZIP and image directory pair:

   ```bash
   python - <<'PY'
   import braceexpand
   zips = list(braceexpand.braceexpand('data/mmc4-zips/shard_{0..3}.zip'))
   print(list(enumerate(zips)))
   PY
   find data/mmc4-images/0 -maxdepth 1 -type f | sed -n '1,10p'
   ```

2. Confirm that `image_name` values in a bounded metadata sample exist under the corresponding image subdirectory.
3. If the downloader numbered image directories by source shard ID instead of zero-based expanded position, create a matching directory/symlink layout or convert ZIPs in an order that matches the existing directories.
4. A small number of missing images is expected for stale web URLs; a near-total miss usually indicates path/layout mismatch.

### Symptom: base64 or PIL image errors during conversion

Likely causes:

- Downloaded image file is corrupt, truncated, or not an image.
- Image has an unusual mode or format that Pillow cannot decode.
- The process lacks permission to read files under `--image_dir`.

Actions:

1. Open a failing image directly:

   ```bash
   python - <<'PY'
   from PIL import Image
   p = 'data/mmc4-images/0/example.jpg'
   img = Image.open(p).convert('RGB')
   print(img.size, img.mode)
   PY
   ```

2. Re-download corrupt images if the source is still available.
3. If only a few images fail, continue; the converter warns and omits `image_base64` for those images.
4. If every image fails, check the file type and permissions before rerunning conversion.

### Symptom: no JSON member found in an MMC4 ZIP

Likely causes:

- The ZIP is not an MMC4 metadata shard.
- The archive contains nested directories or unexpected member suffixes.
- The file is corrupt or an HTML error page saved as `.zip`.

Actions:

```bash
python - <<'PY'
import zipfile
p = 'data/mmc4-zips/shard_0.zip'
with zipfile.ZipFile(p) as zf:
    print(zf.namelist()[:20])
PY
```

Use only shards that contain a readable JSON/JSONL metadata member.

### Symptom: brace expression does not expand as expected

Likely causes:

- Shell expansion happened before the Python script saw the brace expression.
- The expression uses syntax not supported by `braceexpand`.
- Quotes were omitted around a path containing braces.

Actions:

- Quote brace patterns in Python-script invocations:

  ```bash
  --zip_files 'data/mmc4-zips/shard_{0..9}.zip'
  ```

- Preview expansion explicitly:

  ```bash
  python - <<'PY'
  import braceexpand
  print(list(braceexpand.braceexpand('data/mmc4-zips/shard_{0..9}.zip')))
  PY
  ```

### Symptom: output tar shards are too large or too small

Important distinction:

- `--num_files_per_shard` in the bundled MMC4 converter means input ZIP metadata files per output tar stream, not JSON records per tar.
- MMC4 ZIPs can contain different numbers of records and images; output tar sizes may vary.

Actions:

- Reduce `--num_files_per_shard` if tar files are too large for storage or transfer.
- Increase it if too many tiny tar files create file-system overhead.
- For distributed training without dataset resampling, ensure the number of tar shards is at least the total number of data-loader workers across all ranks.

## Training data schema issues

### Symptom: MMC4 training silently skips many samples

Likely causes:

- Records have no `image_base64` after conversion.
- Decoded images are too small or corrupt.
- Similarity scores are below `--mmc4_textsim_threshold`.
- Token truncation leaves too few `<image>` tokens.

Actions:

1. Validate a bounded sample before training:

   ```bash
   python scripts/validate_open_flamingo_data.py \
     --mode mmc4-json \
     --input-path data/mmc4-zips/shard_0.zip \
     --max-records 100
   ```

2. Check a converted tar sample by extracting one JSON member in a scratch location if the user allows local inspection.
3. Lowering the similarity threshold may admit more image/text pairs, but changes training data semantics; get user approval before changing training hyperparameters.

### Symptom: LAION samples are filtered out

Likely causes:

- Missing `.txt` caption member.
- Image suffix is not one of `.jpg`, `.jpeg`, or `.png`.
- Captions/images do not share sample keys inside the tar.

Actions:

```bash
tar -tf data/laion/shard-0000.tar | sed -n '1,40p'
```

Look for pairs such as `000001.txt` and `000001.jpg`.

### Symptom: ChatGPT-generated sequence validation fails

Likely causes:

- Missing `example` text.
- Missing `image_map` dictionary.
- Placeholder keys in `example` do not match keys in `image_map`.
- Mapped image entries use a key other than `base64_image`.

Actions:

- Ensure placeholders follow `_!_IMAGE1_!_`, `_!_IMAGE2_!_`, ... numbering.
- Ensure each mapped entry has a decodable base64 image string before training.

## VQA result-filling issues

### Symptom: duplicate `question_id` error

Likely causes:

- Multiple distributed ranks wrote overlapping predictions and files were concatenated without de-duplication.
- A retry appended to an existing predictions file.

Actions:

- Merge distributed outputs by unique `question_id` before filling.
- Prefer deterministic conflict handling outside the filler script; the filler intentionally errors on duplicates to avoid silently choosing the wrong answer.

### Symptom: many missing question IDs are filled with empty answers

Likely causes:

- The predictions file covers only a test-dev subset, while the full test file contains all test questions.
- The wrong test questions JSON was passed to `--vqa_test_questions_json_path`.
- Prediction IDs use strings while test IDs use integers, or vice versa.

Actions:

1. Confirm that the full test questions JSON is the intended target.
2. Check a few IDs in both files:

   ```bash
   python - <<'PY'
   import json
   preds = json.load(open('outputs/predictions.json'))
   qs = json.load(open('data/questions.json'))['questions']
   print('pred ids', [p['question_id'] for p in preds[:5]])
   print('test ids', [q['question_id'] for q in qs[:5]])
   PY
   ```

3. The bundled filler compares IDs after stringifying, so integer/string representation differences should not prevent matches; persistent mismatches usually mean the wrong question file.

### Symptom: output schema is rejected by an external evaluator

Likely causes:

- Dataset argument does not match the target evaluator.
- VQAv2 expects `question_id`/`answer`, while VizWiz output from the OpenFlamingo helper expects `image`/`answer`.
- The evaluator requires a specific split's full question list.

Actions:

- Re-run with the correct `--dataset` value.
- Inspect the first output records:

  ```bash
  python - <<'PY'
  import json
  data = json.load(open('outputs/filled.json'))
  print(data[:3])
  print(len(data))
  PY
  ```

- Compare the output length to the length of the `questions` list in the test questions file.

### Symptom: answers look over-normalized

The filler applies VQA-style normalization: newlines/tabs are removed, punctuation is normalized, articles are dropped, words such as `two` become `2`, and known contractions are restored. This mirrors the scoring helper used by OpenFlamingo. If a downstream service requires raw answers, keep a copy of the unfilled raw predictions before running the filler.

## Huge JSON and memory safety

Questions and annotation files can be large. The native evaluation helpers usually load full JSON files into memory, but data-preparation checks should avoid unnecessary full reads.

Recommended practice:

- Use `--max-records` validators for schema preflights.
- Inspect short file prefixes only for file-name/schema discovery.
- Avoid repeatedly opening full annotation files in loops.
- If a full fill is required, the filler necessarily loads the prediction list and full questions list once; ensure enough memory and disk for the output file.
