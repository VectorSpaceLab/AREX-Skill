# Data preparation troubleshooting

Use this reference to fail fast on data layout problems before launching distributed extraction or training.

## Quick diagnosis matrix

| Symptom | Likely cause | Deterministic check | Fix |
| --- | --- | --- | --- |
| `ModuleNotFoundError: jsonlines` | JSONL reader dependency missing. | `python scripts/check_dataset_fixtures.py check-imports --modules jsonlines` | Install the Pyramid-Flow data dependencies in the active environment. |
| `ModuleNotFoundError: cv2` or video decode always returns empty | OpenCV package missing or incompatible. | `python scripts/check_dataset_fixtures.py check-imports --modules cv2` | Install an OpenCV build such as a headless wheel if no GUI is needed. |
| Text-feature extraction fails with `KeyError: 'text_fea'` | Rows do not contain output paths for text features. | `python scripts/check_dataset_fixtures.py validate-jsonl --kind text-features --annotation annotation/video_text.jsonl` | Add a `text_fea` path to every row or use the correct annotation file. |
| VAE-latent extraction fails with `KeyError: 'latent'` | Rows do not contain output paths for VAE latents. | `python scripts/check_dataset_fixtures.py validate-jsonl --kind vae-latents --annotation annotation/video_text.jsonl` | Add a `latent` path to every video row. |
| Training loader fails or recurses through rows | One or more rows have missing files, bad fields, or incompatible `.pt` contents. | Validate with `--kind video-training`; then validate each produced latent/text feature file. | Fix the first failing row rather than relying on loader retry behavior. |
| `AssertionError` on latent spatial shape | VAE latent was extracted at a resolution that does not match the dataset `resolution`. | `python scripts/check_dataset_fixtures.py validate-latent --resolution 384p --path latents/example.pt` | Re-extract with `640x384` for `384p` or `1280x768` for `768p`, or use matching loader settings. |
| Video decode returns `None`, empty frames, or no saved latent | Bad path, unsupported codec, corrupt file, empty video, or frame list outside video length. | Validate row fields, then probe the video with a local OpenCV or ffmpeg check before distributed extraction. | Fix paths/codecs, regenerate the video, or remove the row. |
| No latent file appears after VAE extraction | Source save helper catches save exceptions; parent directory may not exist or be unwritable. | Check output parent paths and filesystem permissions before launch. | Create output directories and use writable storage. |
| Checkpoint load fails for text extraction | `--model_name` does not match checkpoint family or checkpoint path is wrong. | Use `scripts/build_precompute_commands.py text-features` and inspect the emitted command. | Match `pyramid_flux` with a Flux-family checkpoint and `pyramid_mmdit` with an MMDiT/SD3-family checkpoint. |
| Checkpoint load fails for VAE extraction | `--model_path` points at the full model root instead of the Causal VAE directory, or the VAE checkpoint is absent. | Use `scripts/build_precompute_commands.py vae-latents` and inspect `--model_path`. | Point `--model_path` to the Causal Video VAE checkpoint directory. |

## Missing dependency imports

Data-preparation and adjacent precompute code use these imports:

- Required for annotations/loaders: `jsonlines`, `torch`, `torchvision`, `PIL`.
- Required for video decode and VAE latent extraction: `cv2`.
- Common adjacent model dependencies that should be importable before full precompute: `timm`, `sentencepiece`.

Run:

```bash
python scripts/check_dataset_fixtures.py check-imports
```

If only schema validation is needed, `check_dataset_fixtures.py validate-jsonl` uses Python's standard JSON parser and does not require `jsonlines`.

## Missing annotation fields

Field requirements depend on the stage:

| Stage kind for validator | Required fields |
| --- | --- |
| `image-text` | `image`, `text` |
| `video-training` | `video`, `text`, `latent`, `text_fea` |
| `text-features` | `text`, `text_fea` |
| `vae-latents` | `video`, `latent` |
| `vae-video` | `video` |
| `vae-image` | `image` |

Readable failure example:

```text
VALIDATION FAILED: row 1 missing required field(s) for video-training: text_fea
```

Fix the annotation generator so every row has the stage-specific fields. Do not assume the training dataset will surface the bad row cleanly; several loaders catch exceptions and retry random rows.

## Latent shape and resolution mismatch

`LengthGroupedVideoTextDataset` has hard-coded spatial checks:

- `resolution='384p'`: latent height `48`, latent width `80`.
- `resolution='768p'`: latent height `96`, latent width `160`.

The full latent tensor should look like:

```text
[batch_or_sample, 16, latent_time, latent_height, latent_width]
```

A wrong-resolution failure should identify both actual and expected spatial dimensions, for example:

```text
VALIDATION FAILED: latent spatial shape is 47x80; expected 48x80 for 384p
```

Common causes:

- Extracted with the wrong `--width` / `--height`.
- Mixed `384p` and `768p` annotations in one training file.
- Saved a raw video tensor or an intermediate tensor instead of the VAE latent.
- Dropped the batch dimension or channel dimension when post-processing `.pt` files.

Use `scripts/build_precompute_commands.py vae-latents` to keep width/height and raw-frame defaults aligned with the loader.

## Video decode failures

The VAE extractor and raw video dataset use OpenCV. Failure modes include:

- `video` path is resolved from a different working directory than expected.
- Codec support is missing in the installed OpenCV/ffmpeg stack.
- The file is zero-length, corrupt, or contains fewer useful frames than requested.
- A custom `frames` list asks for indices beyond the video duration.
- FPS metadata is invalid, leading to poor sampling behavior in raw `VideoFrameProcessor` use.

Before distributed extraction, probe a failing row locally with a tiny script or media tool and verify at least one frame can be read. Keep the annotation row order stable so failures can be mapped back to the source file.

## Checkpoint path mistakes

Text feature extraction and VAE latent extraction use different checkpoints:

- Text features need the model checkpoint family selected by `--model_name`.
- VAE latents need the Causal Video VAE checkpoint directory.

Use relative or project-specific paths when building commands; do not paste machine-local private environment paths into annotations or reusable scripts. If a command fails while loading weights, first verify that:

1. The path exists in the runtime environment.
2. The checkpoint family matches `pyramid_flux` or `pyramid_mmdit` as selected.
3. The VAE extractor path points to the VAE checkpoint, not just a parent model directory.
4. The process has permission to read checkpoints and write artifact files.

## Synthetic hard cases for review

These cases are intentionally stricter than the repo examples and are good usability checks for this sub-skill:

1. A `video-training` annotation row missing `text_fea` must fail with a message naming the missing field and row number.
2. A latent tensor shaped `[1, 16, 2, 47, 80]` checked as `384p` must fail with a message naming the actual and expected spatial shape.
