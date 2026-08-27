# Finetuning Data Formats

InternLM-XComposer 2.5 accepts either a single JSON list or a text manifest that points to one or more JSON lists. Keep data files small enough to validate before launching training; the training job itself is the expensive part.

## 2.5 JSON sample schema

Use `conversations` in actual data. The README prose uses the singular word "conversation" in one place, but the shipped examples and loader use the plural key.

### Text-only sample

```json
{
  "id": "text-0",
  "conversations": [
    {"from": "human", "value": "Tell me a story about pandas."},
    {"from": "bot", "value": "Once there was a curious panda..."}
  ]
}
```

### Single-image sample

2.5 single-image data can omit `<ImageHere>` in the prompt. The visual input is supplied by the `image` field.

```json
{
  "id": "image-0",
  "image": "images/panda.jpeg",
  "conversations": [
    {"from": "human", "value": "Describe this image in detail."},
    {"from": "bot", "value": "The image shows a panda..."}
  ]
}
```

### Multi-image sample

For multiple images, keep one `<ImageHere>` token per image and make the order readable, for example `Image1: <ImageHere>; Image2: <ImageHere>; ...`.

```json
{
  "id": "multi-0",
  "image": ["images/a.jpg", "images/b.jpg"],
  "conversations": [
    {"from": "human", "value": "Image1: <ImageHere>; Image2: <ImageHere>. Compare them."},
    {"from": "bot", "value": "Image1 is ... while Image2 is ..."}
  ]
}
```

Field rules:

- `id`: string or number; useful for traceability even though the loader does not use it directly.
- `conversations`: non-empty list of turns.
- turn `from`: source examples use `human`/`bot`; loader also accepts `user` as human and treats other roles as assistant-like.
- turn `value`: string prompt or answer text.
- `image`: optional. Use a string for one image/video path, or a non-empty list of strings for multiple images.
- Keep each JSON file homogeneous: all text-only or all image-bearing. The mixer classifies an entire file by whether the first sample has `image`.

## 2.5 `data.txt` manifest schema

A manifest line has one JSON path and, optionally, one numeric sampling field:

```text
path/to/text.json 0.02
path/to/single_image.json 0.01
path/to/multi_image.json 0.01
```

The official shell templates pass `--given_num True`. In that mode, the second field is a sample count in thousands, implemented as `int(float(value) * 1000)`:

- `0.02` means 20 samples per epoch.
- `0.01` means 10 samples per epoch.
- `2` means 2,000 samples per epoch.

When `--given_num False`, the same second field is a ratio instead:

- ratio `< 1`: down-sample to `int(len(file) * ratio)` samples;
- ratio `> 1`: up-sample with replacement to `int(len(file) * ratio)` samples;
- omitted field: keep the JSON list length unchanged.

Operational cautions:

- Do not add blank lines or comment lines to `data.txt`; the loader iterates over every line.
- Keep path tokens free of spaces.
- Relative paths are opened from the training process working directory. If you move the manifest, update paths or launch from the expected directory.

## Direct JSON mode

If `--data_path` ends with `.json`, the loader reads that JSON list directly. This is useful for tiny fixture checks and single-dataset experiments. Sampling counts in `data.txt` do not apply in direct JSON mode.

## Data-mixing behavior

The 2.5 loader builds a `Mix_dataset` from all loaded JSON files:

1. Each JSON file becomes one `Sample_dataset`.
2. The first sample decides whether that file is text-only or image-bearing.
3. Text files enter `datasets_text`; image/video files enter `datasets_multi`.
4. Within each group, file selection is weighted by loaded sample count.
5. `Sample_dataset.get_item()` randomly draws `batch_size` raw samples from the selected file and converts conversation turns into the model's text format.
6. `Mix_dataset.__getitem__()` prefers image-bearing samples while its internal `use_multi` counter is below `batch_size`, then alternates back toward text samples if text data exists.
7. `batch_size` here is the loader's internal packing count. It is separate from Hugging Face `per_device_train_batch_size`, which the official shell templates keep at `1`.

Because grouping is file-level, do not put a text-only sample after an image-bearing first sample in the same JSON file, or the loader will still treat the whole file as image-bearing.

## Legacy placeholder compatibility

| Family | Finetuning placeholder guidance | Other data notes |
| --- | --- | --- |
| 2.5 | Single image: no placeholder required. Multi-image: one ordered `<ImageHere>` per image. | Uses `resolution` + `hd_num`; manifest counts are typically run with `--given_num True`. |
| 2.0 | Image-bearing samples require `<ImageHere>` placeholders, including single-image examples. Multi-image examples use one token per image. | Uses `img_size` for non-4KHD models and `hd_num` for 4KHD. The README warns older code paths about batch-size padding. |
| 1.0 | Published finetuning examples are placeholder-free for vision-language JSON. Other demos may use wrapped UI tokens, but they are not the 1.0 finetune data format. | Legacy scripts use separate VL/TXT data concepts and older model internals. |

Use `scripts/validate_finetune_data.py --family 2.5` for current data, and switch `--family` only when deliberately auditing legacy data.
