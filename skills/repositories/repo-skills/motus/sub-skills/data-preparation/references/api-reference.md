# Data API and sampling reference

## Factory and batch APIs

```python
create_dataset(config: OmegaConf, val: bool = False)
collate_fn(batch: list[dict | None]) -> dict | None
```

Supported factory values are `robotwin`, `ac_one`, `latent_action`,
`aloha_agilex_2`, and `lerobot`. Dataset-specific constructor parameters are
forwarded from `config.dataset.params` after common settings are added.

```python
load_video_frames(video_path, frame_indices, target_size=None)
load_first_frame(video_path, frame_idx, target_size)
get_video_frame_count(video_path)
resize_with_padding(frame, (height, width))
normalize_actions(actions, action_min, action_max)
denormalize_actions(actions, action_min, action_max)
```

Video helpers use Decord on CPU and raise on out-of-range indices. The supplied
inspection wheel imports successfully but pip may report its legacy wheel tag
as unsupported; keep a modern Decord/FFmpeg installation for actual decoding.

## Sampling

For robot datasets, define:

```text
A = num_video_frames * video_action_freq_ratio
physical_span = A * global_downsample_rate
condition_idx = random index up to total_frames - physical_span - 1
action_idx[i] = min(condition_idx + (i + 1)*global_downsample_rate,
                    total_frames - 1)
video_idx[j] = action_idx[(j + 1)*video_action_freq_ratio - 1]
```

For latent-action data, `action_idx[i]` starts at the condition frame and
video indices start one step later. The latent-action loader avoids the final
latent-action index when clamping. Short videos fall back to condition index 0
but can still produce repeated/clamped indices; use sufficiently long episodes.

## Normalization and language

Robot normalization is a per-dimension min/max transform loaded from the
selected embodiment statistics. Preserve the same stats for later action
recovery. WAN language embeddings are padded/truncated to the WAN text length
(typically 512) and projected by the video module. Qwen VLM inputs require
processor-produced `input_ids`, `attention_mask`, `pixel_values`, and
`image_grid_thw`; the collator pads token dimensions before model use.

## Three-view image layout

The bundled helper accepts HWC RGB/BGR NumPy arrays and returns a T-shaped
image: the head view occupies the original top region; left and right wrist
views are resized to half the head height/width and placed side by side below.
For a head `(H,W,3)`, output is `(H + H//2, W, 3)` (the source helper's older
shape formula is inconsistent; the bundled helper validates the actual result).
