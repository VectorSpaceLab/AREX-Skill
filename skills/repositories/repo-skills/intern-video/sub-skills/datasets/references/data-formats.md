# InternVideo data formats and readiness

This reference summarizes dataset evidence from the InternVid and instruction-data docs, InternVideo2 dataset docs/configs/loaders, InternVideo3 SFT dataset code, and InternVideo-Next pretraining loaders.

## Dataset releases and identifiers

- **InternVid:** large-scale video-text data for multimodal understanding/generation. The docs describe a partial 10M subset, a full 230M video-text annotation release, InternVid-Aesthetics-18M, and ViCLIP checkpoints trained on InternVid subsets.
- **InternVid query metadata:** `queries.jsonl` is JSONL with one query per line, including `search_word_id` and bilingual `search_word` text used for YouTube retrieval.
- **Instruction data:** VideoChat instruction data V1 contains about 7K detailed descriptions and 4K multi-turn conversations generated from WebVid-10M video text, emphasizing spatiotemporal and causal/temporal features.
- **InternVideo2 single-modality datasets:** docs point to Kinetics-400/600/700/710, Moments in Time, Something-Something V1/V2, ActivityNet, HACS, and K-Mash-style merged data.
- **InternVideo2 multi-modality datasets:** public pretraining sources include CC3M, CC12M, SBU, VG, COCO, WebVid, and InternVid; evaluation follows VINDLU-style JSON files without compression.
- **InternVideo3 SFT data:** release notes describe long-video SFT data with YouTube video ids and QA annotations. The local SFT code consumes meta JSON plus JSONL chat annotations.

## InternVid query JSONL

One JSON object per line:

```json
{"search_word_id": "feeding ducks", "search_word": "喂鸭子"}
```

Validation expectations:

- Required string keys: `search_word_id`, `search_word`.
- IDs should be unique for downstream indexing.
- This file is search/source metadata, not a video-caption annotation file.

## InternVideo2 single-modality lists

VideoMAE-style pretraining and action-recognition loaders use line-oriented files. The delimiter is controlled by a `split` argument and defaults to a space.

| Use | Line format | Notes |
|---|---|---|
| Decord video file mode | `<video-path> <label>` | Media path is joined with a `prefix`/data root. If extension is missing, some loaders append `.mp4`. |
| Frame-folder mode | `<frame-folder> <total-frame-count> <label>` | Used when not decoding video files; image naming is typically `img_%05d.jpg`. |
| Classification CSV-style loaders | two columns: media path and label | Parsed through pandas with the configured delimiter. |

Pitfalls:

- Spaces in media paths break the default parser.
- `--sampling_rate=1` appears in sparse-sampling notes; do not change it without understanding frame/crop/clip counts.
- `PREFIX`, `DATA_PATH`, `INTERNVIDEO2_DATA_PATH`, and `INTERNVIDEO2_MODEL_PATH` are configuration concepts; validate actual paths before launch.

## InternVideo2 multi-modality JSON arrays

Pretraining and retrieval loaders generally use JSON arrays loaded with `json.load`. Config entries carry `anno_path`, `data_root`, `media_type`, and optional flags.

Common records:

```json
{"image": "relative/image.jpg", "caption": "a concise caption"}
```

```json
{"video": "relative/video.mp4", "caption": "a video caption", "duration": 0}
```

```json
{
  "video": "relative/video.mp4",
  "audio": "relative/audio.wav",
  "caption_main": "visible events",
  "caption_asr": "speech transcript"
}
```

Supported concepts from loaders/configs:

- `media_type`: `image`, `video`, `audio`, or `audio_video`.
- Caption can be `caption`, `captions`, or multiple caption-like keys for AVS-style augmentation.
- `crop_bbox` can crop images when enabled.
- `read_clip_from_video` expects `video_start_frame` and `video_end_frame`.
- Audio-video records may either provide an `audio` file or request audio extraction from video, with optional zero-audio padding.
- The SQLite converter creates an `annos(id, <media_type>, caption)` table from JSON lists, but many runtime loaders still read JSON directly.

## InternVideo3 SFT meta JSON

A meta file maps dataset names to specs:

```json
{
  "train_long_video": {
    "annotation": "annotations/train.jsonl",
    "media_root": "media/",
    "sample_ratio": 1.0,
    "fps": 4,
    "video_min_frames": 4,
    "video_max_frames": 2048,
    "rand_video_max_frames": 24,
    "video_max_total_pixels": 100663296
  }
}
```

Required by config loop: `annotation`. Defaults exist for `media_root` and `sample_ratio`; visual/tokenization fields override config defaults per dataset. If the annotation value is a directory, the builder discovers `.jsonl` files recursively.

## InternVideo3 SFT JSONL messages

Each line is an OpenAI-like chat object:

```json
{
  "id": "sample-001",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "video_url",
          "video_url": {
            "url": "videos/example.mp4",
            "image_wh": [1920, 1080],
            "origin_video_length": 900,
            "origin_fps": 30.0,
            "processed_video_length": 120,
            "processed_fps": 4.0,
            "frames_timestamp": [0.0, 0.25]
          }
        },
        {
          "type": "text",
          "text": "<VIDEO_CONTEXT> Answer with evidence from the relevant time span.",
          "conversation_timestamps": [[1.0, 7.5]]
        }
      ]
    },
    {"role": "assistant", "content": "A grounded response."}
  ]
}
```

Key requirements:

- Roles are restricted to `system`, `developer`, `user`, `assistant`, and `pretrain`.
- Image content uses `type: "image_url"` and nested `image_url.url`; video content uses `type: "video_url"` and nested `video_url.url`.
- `image_wh` is strongly recommended and required for reliable visual token counting/packing.
- Text placeholders must match media items: `<IMG_CONTEXT>` for images, `<VIDEO_CONTEXT>` for videos.
- If either `processed_video_length` or `processed_fps` appears, both must appear.
- If `frames_timestamp` appears with processed frames, the timestamp list length must match `processed_video_length`.
- `conversation_timestamps` in text should match the number of `<VIDEO_CONTEXT>` placeholders in that text item.

## InternVideo-Next multi pretraining list

The default InternVideo-Next stage1/stage2 entry points use the multi pretraining dataset builder. Its list format is:

```text
<source> <video-path> <total_time> <start_time> <end_time> <label>
```

Use `-1` time values only when intentionally skipping clip-time adjustment. The `source` string can affect augmentation; `ssv2` disables horizontal flip through a separate transform.

## Path-readiness checklist

- Confirm whether paths are relative to `media_root`, `prefix`, `data_root`, or already absolute/user-managed.
- Check that local files exist only when the user has staged data and requested path checks.
- Skip path-existence checks for object-storage URIs unless credentials/config are approved.
- Validate video suffixes against decoder support: common supported suffixes include `.mp4`, `.avi`, `.mov`, `.webm`, `.flv`, `.wmv`, `.mkv`, `.rmvb`, and `.ts` for InternVideo3 SFT video loading.
- For frame folders, verify actual frame names and counts before expensive jobs.
- For YouTube-derived datasets, expect missing/deleted videos even when annotation syntax is valid.

## Bundled validator mapping

| Target | Validator format |
|---|---|
| InternVid `queries.jsonl` | `internvid-queries` |
| InternVideo2 multi-modality JSON array | `internvideo2-json` |
| InternVideo3 SFT meta JSON | `internvideo3-meta` |
| InternVideo3 SFT annotation JSONL | `internvideo3-jsonl` |
| InternVideo2/Next line-oriented pretraining lists | `pretrain-list` |
| Unknown file | `auto` for syntax-based best effort |
