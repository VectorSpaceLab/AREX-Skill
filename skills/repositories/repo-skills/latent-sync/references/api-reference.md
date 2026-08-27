# Shared LatentSync runtime surfaces

Read this when you need the concrete callable surface that underlies multiple sub-skills.

## Core generation pipeline

### `LipsyncPipeline.__call__(...)`

```python
pipeline(
    video_path: str,
    audio_path: str,
    video_out_path: str,
    num_frames: int = 16,
    video_fps: int = 25,
    audio_sample_rate: int = 16000,
    height: int | None = None,
    width: int | None = None,
    num_inference_steps: int = 20,
    guidance_scale: float = 1.5,
    weight_dtype: torch.dtype | None = torch.float16,
    eta: float = 0.0,
    mask_image_path: str = "latentsync/utils/mask.png",
    temp_dir: str = "temp",
    generator=None,
    callback=None,
    callback_steps: int | None = 1,
    **kwargs,
)
```

Important behavior:

- Checks for `ffmpeg` before the run starts.
- Loads the fixed mask with `load_fixed_mask(height, mask_image_path)`.
- Uses `ImageProcessor(..., device="cuda", mask_image=mask_image)` for face masking and restoration.
- Reads Whisper audio features, loops video frames if the audio is longer, and denoises chunk by chunk.
- Writes temporary `video.mp4` and `audio.wav`, then muxes them into the requested output.

### `UNet3DConditionModel.from_pretrained(...)`

```python
unet, resume_global_step = UNet3DConditionModel.from_pretrained(
    model_config: dict,
    ckpt_path: str,
    device="cpu",
)
```

Notes:

- Builds the model from a config dictionary and optionally loads a checkpoint.
- Returns the loaded model plus `resume_global_step`.
- Drops incompatible `conv_in`, `conv_out`, and mismatched cross-attention weights before `strict=False` loading.
- A checkpoint with a missing `state_dict` still raises through the underlying `torch.load`/load-state path.

### `Audio2Feature`

```python
audio_encoder = Audio2Feature(
    model_path="checkpoints/whisper/tiny.pt",
    device=None,
    audio_embeds_cache_dir=None,
    num_frames=16,
    audio_feat_length=[2, 2],
)
```

Methods worth knowing:

- `audio2feat(audio_path)` transcribes audio to Whisper embeddings and optionally caches them.
- `feature2chunks(feature_array, fps)` slices audio features into video-aligned chunks.
- `crop_overlap_audio_window(audio_feat, start_index)` produces the overlap window used by SyncNet-style training.

## SyncNet and training surfaces

### `SyncNetDataset`

```python
dataset = SyncNetDataset(data_dir: str, fileslist: str, config)
```

Notes:

- Uses `fileslist` when present; otherwise recursively discovers `.mp4` files in `data_dir`.
- Requires `config.data.resolution`, `num_frames`, `audio_sample_rate`, `video_fps`, and `audio_mel_cache_dir`.
- Builds positive and negative AV pairs and caches mel spectrograms under `audio_mel_cache_dir`.
- `__getitem__` loops until it finds a usable clip, so malformed data can look like a hang if preflight is skipped.

### `StableSyncNet`

```python
syncnet = StableSyncNet(OmegaConf.to_container(config.model), gradient_checkpointing=False)
vision_embeds, audio_embeds = syncnet(image_sequences, audio_sequences)
```

Notes:

- Returns unit-normalized visual and audio embeddings.
- The visual-channel layout must match the chosen SyncNet config.
- Pixel-space 16-frame configs use 48 visual channels; latent-space 16-frame configs use 64.

## Evaluation surfaces

### `SyncNetEval.evaluate(...)`

```python
av_offset, min_dist, conf = SyncNetEval(device="cuda").evaluate(
    video_path,
    temp_dir="temp",
    batch_size=20,
    vshift=15,
)
```

Notes:

- Converts the input video to images and 16 kHz audio with `ffmpeg`.
- Extracts 224×224 frames and 5-frame/20-MFCC windows.
- Returns the AV offset, minimum distance, and confidence for one detected face track.
- Recreates and deletes its temp directory around the run.

### `syncnet_eval(...)`

```python
av_offset, conf = syncnet_eval(syncnet, syncnet_detector, video_path, temp_dir, detect_results_dir="detect_results")
```

Notes:

- Runs the S3FD-based detector first.
- Raises a face-not-detected failure when no crop videos are produced.
- Averages confidence and offset across all detected crops in the video.

### `eval_fvd(...)`

```python
eval_fvd(real_videos_dir: str, fake_videos_dir: str)
```

Notes:

- Uses MediaPipe face detection on frames 20:36.
- Extracts 16-frame face crops and computes CPU-backed FVD.
- Treats the face detector and frame window as hard prerequisites.

## Use this reference when

- You need to confirm a callable signature before wrapping it in a helper script.
- A config value is coupled to a model shape, audio window, or frame count.
- A failure smells like a data-shape mismatch rather than a missing file.
