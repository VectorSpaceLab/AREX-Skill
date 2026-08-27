# Dataset Formats and Precomputed Layout

This reference covers the data shapes that must be ready before LTX training. Use it to design or validate manifests and cached preprocessing outputs; use `../scripts/validate_dataset_manifest.py` and `../scripts/inspect_precomputed_latents.py` for safe checks.

## Manifest file types

LTX preprocessing accepts metadata in:

- `.json`: a list of objects.
- `.jsonl`: one JSON object per non-empty line.
- `.csv`: header row plus one row per sample.

Paths in manifest cells are resolved relative to the manifest file's parent directory unless they are absolute. Prefer relative paths so datasets are portable.

## Recognized columns

| Canonical column | Legacy alias | Required when | Output directory | Notes |
|---|---|---|---|---|
| `caption` | — | Always | `conditions/` | Text caption to embed. Can be injected with a LoRA trigger during preprocessing; do not manually duplicate the trigger if using `--lora-trigger`. |
| `video` | `media_path` | Video, image, mixed image/video, target side of V2V/AV2AV/inpainting | `latents/` | Points to target videos or still images. Images need an `F=1` bucket. |
| `audio` | — | Explicit audio, audio-only, or when audio should not be extracted from target video | `audio_latents/` | Overrides auto-extraction from video for explicit target audio. Audio-only datasets require `--audio-durations`. |
| `reference_video` | `ref_media_path` | V2V or AV2AV IC-LoRA | `reference_latents/` | Paired reference media for video IC-LoRA. Same content/frame alignment as target; may be downscaled by preprocessing flags. |
| `reference_audio` | — | A2A or AV2AV IC-LoRA | `reference_audio_latents/` | Paired reference audio for audio IC-LoRA. |
| `video_mask` | — | Video inpainting | `video_masks/` | Image/video mask; preprocessing thresholds to latent-space binary mask. |
| `audio_mask` | — | Audio inpainting | `audio_masks/` | Waveform-like mask or `.pt` tensor; preprocessing thresholds to audio-latent time mask. |

A manifest must contain `caption` plus at least one target media column (`video`, `media_path`, or `audio`). Unknown extra columns are allowed, but similar names such as `text`, `prompt`, `path`, `file`, `ref_video`, or `mask` are not auto-detected unless explicitly renamed before preprocessing.

## Minimal examples

Video or image dataset:

```json
[
  {"caption": "a dancer turns under blue stage lights", "video": "videos/dancer.mp4"},
  {"caption": "a still product photo on a white table", "video": "images/product.png"}
]
```

JSONL equivalent:

```jsonl
{"caption":"a cat plays with yarn","video":"videos/cat.mp4"}
{"caption":"a dog runs through a park","video":"videos/dog.mp4"}
```

CSV equivalent:

```csv
caption,video
"a cat plays with yarn",videos/cat.mp4
"a dog runs through a park",videos/dog.mp4
```

Audio-only:

```json
[
  {"caption": "short piano melody", "audio": "audio/piano.wav"}
]
```

V2V IC-LoRA:

```json
[
  {
    "caption": "turn the edge map into a natural video",
    "video": "targets/clip_001.mp4",
    "reference_video": "references/clip_001_edges.mp4"
  }
]
```

AV2AV or audio IC-LoRA:

```json
[
  {
    "caption": "match the target motion and audio style",
    "video": "targets/clip_001.mp4",
    "reference_video": "references/clip_001_depth.mp4",
    "reference_audio": "references/clip_001_style.wav"
  }
]
```

Inpainting:

```json
[
  {
    "caption": "fill the missing sky region",
    "video": "targets/sky.mp4",
    "video_mask": "masks/sky_mask.mp4"
  }
]
```

## Resolution buckets

Video and image preprocessing uses `WxHxF` buckets separated by semicolons, for example:

```text
960x544x1;960x544x49;512x512x81
```

Rules:

- Width and height must be multiples of the video VAE spatial factors. The default LTX VAE uses factor 32, so `960x544` and `512x512` are valid.
- Frames must satisfy `F % T == 1`, where the default temporal factor is 8. Valid default-frame values include `1, 9, 17, 25, 33, 41, 49, 57, 65, 73, 81, 89, 97, 121`.
- The preprocessing code reads the actual VAE factors from the checkpoint or VAE file; a different VAE can change the spatial or temporal divisibility requirement.
- Images are single-frame samples and require an `F=1` bucket.
- Mixed image + video datasets should include at least one `F=1` bucket and one `F>1` bucket. The later training config must use batch size 1 because variable sample shapes cannot be collated into a larger batch.
- Videos shorter than the smallest requested frame count are skipped by preprocessing. Choose the minimum frame bucket from the shortest intended clips or split/filter clips first.

Bucket selection resizes media while preserving aspect ratio, center-crops to the chosen bucket, and keeps the first `F` frames.

Approximate video token sequence length for default VAE factors:

```text
sequence_length = (H / 32) * (W / 32) * ((F - 1) / 8 + 1)
```

Longer or larger buckets cost more memory during preprocessing and training. Route detailed memory/OOM decisions to `../performance-backends/SKILL.md`.

## Audio duration rules

- When a `video` column exists and audio is auto-extracted from video, the audio duration is derived from the chosen video bucket as approximately `max(F) / 25` seconds.
- Use `audio` for explicit target audio. In a video+audio manifest, audio latent filenames align to the video column when available.
- Audio-only manifests have no video timing, so preprocessing requires `--audio-durations`, for example `2.0;4.0;8.0` seconds.
- Audio duration buckets match each file to the largest bucket that fits; files shorter than the smallest bucket are skipped.
- Use `--skip-audio` only when the training mode does not need target audio latents. If the later mode trains or conditions on audio, `audio_latents/` must be present and non-empty.

## Precomputed directory schema

The default preprocessing output root is `.precomputed/` next to the manifest unless `--output-dir` is set. The training config's `data.preprocessed_data_root` should point to this parent directory.

```text
.precomputed/
  latents/                   # target video/image latents
  conditions/                # caption/text embeddings
  audio_latents/             # target audio latents, auto-extracted or explicit
  reference_latents/         # reference video latents for IC-LoRA
  reference_audio_latents/   # reference audio latents for IC-LoRA
  video_masks/               # latent-space binary video masks
  audio_masks/               # latent-time binary audio masks
```

Typical `.pt` payload keys:

| Directory | Expected keys | Shape hints |
|---|---|---|
| `latents/` | `latents`, `num_frames`, `height`, `width`, `fps` | Video latent tensor is non-patchified `[C, F', H', W']`. |
| `conditions/` | `video_prompt_embeds`, `prompt_attention_mask`, optional `audio_prompt_embeds` | Text features are checkpoint/Gemma-version specific. |
| `audio_latents/` | `latents`, `num_time_steps`, `frequency_bins`, `duration` | Audio latent tensor plus duration metadata. |
| `reference_latents/` | same as `latents/` | Usually mirrors target names; may have smaller `height`/`width` or fewer frames if reference scale flags were used. |
| `reference_audio_latents/` | same as `audio_latents/` | Mirrors sample names for audio reference conditioning. |
| `video_masks/` | `mask` | Binary tensor `[F', H', W']`; values `>0.5` are conditioning/clean tokens. |
| `audio_masks/` | `mask` | Binary tensor `[T]`; values `>0.5` are conditioning/clean tokens. |

## Staleness checklist

Existing `.pt` files are skipped by default. Use a fresh output directory or add `--overwrite` whenever any of these changed:

- LTX checkpoint, split transformer, video VAE, audio VAE, or Gemma/text-encoder path.
- Resolution bucket list or audio duration list.
- LoRA trigger word or caption cleanup flags.
- Reference downscale or temporal scale factor.
- Manifest rows, media paths, captions, references, or masks.

Use `inspect_precomputed_latents.py` to summarize shapes and directory coverage before deciding to reuse cached outputs.
