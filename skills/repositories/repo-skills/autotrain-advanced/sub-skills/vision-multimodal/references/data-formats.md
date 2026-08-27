# Vision and VLM data formats

## Image classification

Expected local directory shape:

```text
train_dir/
  class_a/
    img001.jpg
    ... at least 5 jpg/jpeg/png files
  class_b/
    img101.png
    ... at least 5 jpg/jpeg/png files
```

Rules enforced by the preprocessor:

- at least two class subfolders;
- each class folder has at least five image files;
- allowed extensions are jpg, jpeg, png (case-sensitive variants are accepted by the source preprocessor);
- no non-image files inside class folders;
- no nested subfolders inside class folders;
- validation data, if provided, must have the same class subfolder names.

## Image regression / image scoring

Expected local directory shape:

```text
train_dir/
  image001.jpg
  image002.png
  metadata.jsonl
```

`metadata.jsonl` requires:

- `file_name` — image file name relative to the directory;
- `target` — numeric target value.

## Object detection

Expected local directory shape:

```text
train_dir/
  image001.jpg
  image002.png
  metadata.jsonl
```

`metadata.jsonl` requires:

- `file_name` — image file name relative to the directory;
- `objects` — object annotations. AutoTrain later converts this into `bbox` and `category` structures for `datasets` imagefolder features.

## VLM

Expected local directory shape:

```text
train_dir/
  image001.jpg
  image002.png
  metadata.jsonl
```

`metadata.jsonl` requires:

- `file_name` — image file name relative to the directory;
- one column for every value in the VLM `column_mapping`;
- common mappings: `text_column` for answer/caption text, `prompt_text_column` for question/prompt text.

Example validator call:

```bash
python skills/disco/autotrain-advanced/sub-skills/vision-multimodal/scripts/validate_vision_data.py \
  --task vlm:vqa \
  --text-column answer \
  --prompt-text-column question \
  train_dir
```

## Local validation helper

The bundled validator checks folders, image counts, metadata presence, file references, and required metadata columns without importing trainer code or uploading data.
