# OpenFlamingo data formats

This reference summarizes the data layouts expected by OpenFlamingo training and VQA-style evaluation code. It is intended to be sufficient for data-preparation work without reopening the source repository.

## Training datasets

OpenFlamingo training uses WebDataset tar shards. Pass shard patterns such as `data/mmc4/shard-{000000000..000000099}.tar` or `data/laion/{00000..00999}.tar` to the training command. Quote brace patterns in shell commands so the intended tool, not the shell, performs expansion when required.

### LAION image-text shards

LAION-style samples are ordinary WebDataset samples containing exactly one text caption plus one image payload.

Required per-sample members:

- `*.txt`: UTF-8 caption text.
- One of `*.jpg`, `*.jpeg`, or `*.png`: image bytes.

Important behavior:

- Samples missing `txt` are filtered out.
- Samples missing an image key among `jpg`, `jpeg`, or `png` are filtered out.
- Captions are wrapped at training time as `<image>{caption}<|endofchunk|>{eos_token}` and truncated to a short caption length by default.
- Image decoding happens during WebDataset loading; corrupt image bytes normally appear as PIL/WebDataset decode errors.

A minimal logical sample looks like:

```text
000001.txt
000001.jpg
```

### MMC4 source ZIP metadata

The MMC4 conversion workflow starts from downloaded MMC4 ZIP shards plus a directory of downloaded raw images. Each ZIP is expected to contain a JSON/JSONL metadata file as its first JSON member. The converter reads one JSON object per line from that member.

Required fields per source record:

```json
{
  "text_list": ["sentence 1", "sentence 2"],
  "similarity_matrix": [[0.12, 0.31], [0.47, 0.08]],
  "image_info": [
    {"image_name": "image_0.jpg"},
    {"image_name": "image_1.jpg"}
  ]
}
```

Field meanings:

- `text_list`: ordered text segments/sentences for an interleaved document.
- `similarity_matrix`: image-by-text similarity scores used to choose where `<image>` tokens should be inserted.
- `image_info`: ordered image metadata. Before conversion, each image entry must include `image_name`; after conversion, usable images also include `image_base64`.

The bundled converter looks for image files at:

```text
<image_dir>/<zip-position>/<image_name>
```

where `<zip-position>` is the zero-based position of the ZIP after brace expansion. This mirrors the expected layout produced by the common MMC4 image-download workflow. If your image downloader uses source shard numbers instead of zero-based positions, either arrange symlinks/directories accordingly or adapt the input list so positions match the image directory layout.

### MMC4 WebDataset tar shards

After conversion, each WebDataset sample contains a `json` member. The JSON payload has the source record plus base64-encoded images attached to entries in `image_info`.

Required training-time fields:

```json
{
  "text_list": ["sentence 1", "sentence 2"],
  "similarity_matrix": [[0.12, 0.31], [0.47, 0.08]],
  "image_info": [
    {"image_name": "image_0.jpg", "image_base64": "/9j/4AAQSk..."},
    {"image_name": "image_1.jpg", "image_base64": "/9j/4AAQSk..."}
  ]
}
```

Important behavior:

- Records with no valid base64 images are skipped by training-time preprocessing.
- Images whose decoded byte size is too small may be ignored.
- The similarity matrix is sliced to valid images, negated, and solved as a one-to-one image/text assignment. Pairs below the configured `--mmc4_textsim_threshold` are dropped.
- If too few images remain after filtering or token truncation, preprocessing rejects that sample.

### ChatGPT-generated interleaved sequences

Some OpenFlamingo training variants use experimental ChatGPT-generated interleaved image/text sequences. These are consumed by the same interleaved preprocessing path when the JSON object contains an `is_gpt` marker.

Expected fields:

```json
{
  "is_gpt": true,
  "example": "A caption _!_IMAGE1_!_ followed by another sentence _!_IMAGE2_!_ .",
  "image_map": {
    "_!_IMAGE1_!_": {"base64_image": "/9j/4AAQSk..."},
    "_!_IMAGE2_!_": {"base64_image": "/9j/4AAQSk..."}
  }
}
```

Important behavior:

- Placeholders `_!_IMAGE1_!_`, `_!_IMAGE2_!_`, ... are replaced with OpenFlamingo's `<image>` and `<|endofchunk|>` markers.
- Each mapped image must contain `base64_image` with decodable image bytes.
- Raw images are not bundled in released sequence shards; users must pre-download images and encode them before training.

## VQA-style evaluation JSON

OpenFlamingo evaluates VQAv2, OK-VQA, TextVQA, and VizWiz through a VQA-style dataset wrapper.

### Questions file

Questions files are JSON objects with a top-level `questions` list:

```json
{
  "questions": [
    {
      "question": "What is shown?",
      "image_id": 123,
      "question_id": 456
    }
  ]
}
```

Dataset-specific image conventions:

- **VQAv2 / OK-VQA**: `image_id` is numeric. Images are expected as COCO-style names such as `COCO_val2014_000000000123.jpg` under a `train2014`, `val2014`, or `test2015` directory.
- **VizWiz**: `image_id` is the image filename, for example `VizWiz_val_00000000.jpg`.
- **TextVQA**: `image_id` is a string stem, and images are expected as `<image_id>.jpg`.

### Annotations file

Annotations files are JSON objects with a top-level `annotations` list:

```json
{
  "annotations": [
    {
      "question_id": 456,
      "image_id": 123,
      "question_type": "other",
      "answers": [
        {"answer": "cat", "answer_confidence": "yes", "answer_id": 1}
      ]
    }
  ]
}
```

Notes:

- The `answers` list is used by the VQA metric. Many VQA-style files contain ten answers per question, but the wrapper mainly requires an iterable of objects with `answer`.
- `answer_type` may be present and is used by some VQA metric reports; if absent, the metric treats the type as `other`.
- TextVQA and VizWiz use VQA-format converted annotation files rather than their raw dataset-native annotation formats.

### Prediction list for result filling

The bundled VQAv2/VizWiz result filler expects a JSON list:

```json
[
  {"question_id": 456, "answer": "cat"},
  {"question_id": 789, "answer": "two"}
]
```

Behavior:

- `question_id` is matched against the full test questions file.
- `answer` is normalized using VQA-style punctuation, digit, article, and contraction rules.
- Missing test question IDs are filled with an empty answer.
- Duplicate prediction question IDs are treated as an error by the bundled script.

Output shapes:

- **VQAv2**: list of `{"question_id": <id>, "answer": <normalized-or-empty>}` in full test-question order.
- **VizWiz**: list of `{"image": <image_id>, "answer": <normalized-or-empty>}` in full test-question order, matching the OpenFlamingo helper's expected final format.

The result filler is not a scorer. It prepares complete submission-style JSON after model predictions have already been generated.
