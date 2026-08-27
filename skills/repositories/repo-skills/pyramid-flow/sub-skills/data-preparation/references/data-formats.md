# Pyramid-Flow data formats

This reference distills the data-facing contracts used by Pyramid-Flow annotations, dataset loaders, and precomputed text/VAE artifacts. Paths shown here are examples only; use paths that are valid in the runtime project where the Pyramid-Flow workflow is executed.

## JSONL rules

- Use UTF-8 JSON Lines: one JSON object per non-empty line.
- Keep path fields as strings. Relative paths are resolved by the process that runs the dataset or extractor; be consistent about the working directory or pass a clear data root to your own wrapper.
- Keep prompt fields as strings. The `text` value is used directly by text encoders or returned by dataset classes.
- Validate rows before extraction or training with `scripts/check_dataset_fixtures.py`.

## Annotation row schemas

### Image-text rows

Used by `ImageTextDataset` for image-generation training and by VAE mixed image/video workflows.

```json
{"image": "images/example.jpg", "text": "a concise image caption"}
```

Required fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `image` | string | Image file path readable by PIL. |
| `text` | string | Prompt/caption text. |

### Final video training rows

Used by `LengthGroupedVideoTextDataset` when both VAE latents and text features have been precomputed.

```json
{"video": "videos/example.mp4", "text": "a concise video caption", "latent": "latents/example-latent-384.pt", "text_fea": "text_feature/example-text.pt"}
```

Required fields for the final precomputed training layout:

| Field | Type | Meaning |
| --- | --- | --- |
| `video` | string | Original video path retained for provenance and optional reprocessing. |
| `text` | string | Prompt/caption text. |
| `latent` | string | Path where the VAE latent `.pt` tensor is saved. |
| `text_fea` | string | Path where the text-feature `.pt` dictionary is saved. |

### Text-feature extraction rows

The text-feature extractor only reads `text` and `text_fea` from each row. It creates the parent directory of `text_fea` if needed.

```json
{"text": "a concise video caption", "text_fea": "text_feature/example-text.pt"}
```

Rows may also include `video` and `latent`; those fields are passed through for later stages but are not consumed by text-feature extraction.

### VAE-latent extraction rows

The VAE-latent extractor reads `video`, `latent`, and optionally `frames`.

```json
{"video": "videos/example.mp4", "latent": "latents/example-latent-384.pt", "frames": [0, 1, 2, 3, 4]}
```

- `frames` is optional. When omitted, the extractor samples frame indices from `0` up to `num_frames - 1`.
- Include `text` and `text_fea` too when the same JSONL will become the final DiT training annotation.

### Causal VAE raw training rows

Causal VAE training uses raw image/video annotations rather than the DiT precomputed latent layout.

```json
{"video": "videos/example.mp4"}
{"image": "images/example.jpg"}
```

Training launch details belong in `../../training-workflows/SKILL.md`; this sub-skill only owns row validation and loader-facing format checks.

## Dataset loader contracts

The following signatures and return keys were verified from live Pyramid-Flow loader inspection.

| Loader | Constructor signature | Input rows | Returned keys |
| --- | --- | --- | --- |
| `ImageTextDataset` | `(anno_file, add_normalize=True, ratios=[1.0, 0.6, 1.666...], sizes=[(1024,1024), (768,1280), (1280,768)], crop_mode='random', p_random_ratio=0.0)` | `image`, `text` | `video`, `text`, `identifier` |
| `LengthGroupedVideoTextDataset` | `(anno_file, max_frames=16, resolution='384p', load_vae_latent=True, load_text_fea=True)` | `video`, `text`, `latent`, and usually `text_fea` | `video`, `prompt_embed`, `prompt_attention_mask`, `pooled_prompt_embed`, `identifier` when `load_text_fea=True`; otherwise `video`, `text`, `identifier` |
| `VideoDataset` | `(anno_file, resolution=256, max_frames=6, add_normalize=True)` | `video` | `video`, `identifier` |
| `ImageDataset` | `(anno_file, resolution=256, max_frames=8, add_normalize=True)` | `image` | `video`, `identifier` |
| `VideoFrameProcessor` | `(resolution=256, num_frames=24, add_normalize=True, sample_fps=24)` | video file path | `(video_tensor, None)` on success |

Notes:

- Image loaders return image or packed-image tensors using the key `video` so training code can share a video-like interface.
- The dataset classes catch many exceptions and retry another random row. Validate fixtures first to avoid confusing recursive retries when a one-row fixture is bad.
- Video decoding uses OpenCV (`cv2.VideoCapture`) and frame conversion from BGR to RGB.

## Shape expectations

### Image-text dataset item

A verified tiny image fixture returned:

```text
keys: identifier, text, video
video tensor shape: [3, height, width]
identifier: image
```

The configured `sizes` list uses `(width, height)`, while crop operations receive `(height, width)`.

### Precomputed video latent item

`LengthGroupedVideoTextDataset` loads `latent = torch.load(row['latent'], map_location='cpu')`, then checks hard-coded spatial sizes:

| Dataset `resolution` | Expected raw precompute size | Expected latent spatial shape |
| --- | --- | --- |
| `384p` | width `640`, height `384` | height `48`, width `80` |
| `768p` | width `1280`, height `768` | height `96`, width `160` |

The loaded latent must be a 5D tensor-like object shaped as:

```text
[batch_or_sample, 16, latent_time, latent_height, latent_width]
```

The channel dimension at index `1` must be `16`. The loader truncates `latent_time` to `max_frames` with `latent[:, :, :cur_temp]`.

### Text feature dictionary

The text-feature extractor saves one dictionary per row with these keys:

```text
prompt_embed
prompt_attention_mask
pooled_prompt_embed
```

Each value should be tensor-like and is saved with a leading batch dimension for the single row. The exact hidden sizes depend on the selected text encoder and checkpoint family; validate key presence and tensor rank before relying on model-specific dimensions.

## Local validation commands

Run these from the generated skill tree or pass the script path explicitly:

```bash
python scripts/check_dataset_fixtures.py check-imports
python scripts/check_dataset_fixtures.py validate-jsonl --kind image-text --annotation annotation/image_text.jsonl
python scripts/check_dataset_fixtures.py validate-jsonl --kind video-training --annotation annotation/video_text.jsonl
python scripts/check_dataset_fixtures.py smoke-fixtures --exercise-loaders
```

The smoke fixture command creates tiny synthetic files, validates the row schemas and tensor shapes, and can exercise the live Pyramid-Flow loaders when `dataset.dataset_cls` is importable.
