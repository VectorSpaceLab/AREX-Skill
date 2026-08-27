# Data Formats for Sana Video, World Modeling, and Streaming

Use this reference to validate inputs and outputs before planning GPU commands.

## Prompt formats

### SANA-Video T2V prompt text file

A native SANA-Video prompt file is newline-delimited text. Each non-empty line is treated as one prompt.

Example:

```text
A cinematic drone shot of waves crashing against rugged cliffs at sunset.
A woolly mammoth herd walks through a snowy meadow with soft depth of field.
```

Planning notes:

- `--motion_score N` appends ` motion score: N.` to each prompt in the native script when `N > 0`.
- The native script also supports prompt splitting with a split token, but common usage is one prompt per line.
- `--txt_file` must point to the file; native command wrappers default to a sample prompt file when omitted.

### SANA-Video I2V/TI2V prompt text file

I2V prompt lines combine prompt text and an image path using the image split token `<image>`.

Example:

```text
A woman stands against a sunset backdrop, hair moving gently in the breeze.<image>asset/samples/i2v-1.png
A cow gallops across a dusty field under a clear sky.<image>asset/samples/i2v-2.png
```

Planning notes:

- Use `--task=ltx` on the native command for this path.
- The image path is parsed from the same line after `<image>`.
- The selected config still controls output resolution and VAE stride.

### SANA-WM prompt file

SANA-WM uses a UTF-8 prompt file passed with `--prompt`. The file content is read, stripped, and must not be empty.

Example:

```text
A first-person view across an immense dry lakebed with a black sports car in the foreground. The camera moves gently forward while clouds drift slowly.
```

### SANA-Streaming V2V prompt

SANA-Streaming V2V takes the edit instruction directly with `--prompt`, not as a prompt file. It also takes `--video_path` for the source video.

Example:

```bash
--prompt "Transform the entire scene into a watercolor painting." --video_path input.mp4
```

## Frame-count conventions

| Workflow | Common value | Rule or caveat |
| --- | --- | --- |
| SANA-Video short 480p/720p | `81` | 5 seconds at 16 fps plus first frame. |
| LongSANA | `seconds * fps + 1` | Native long path often uses `cfg_scale=1.0`. |
| SANA-WM bidirectional/chunk-causal | `161`, `321`, or `961` | Native script snaps to nearest `8*k+1` because the LTX-2 VAE temporal stride is 8. |
| SANA-WM streaming | `241` default, `961` for ~60s | Snaps to `8 * refiner_block_size * k + 1`; default `refiner_block_size=3`, so values are `24*k+1`. |
| SANA-Streaming V2V `bidirectional_short` | `81` | Short-video editing path; default negative prompt is applied if omitted. |
| SANA-Streaming V2V `long_streaming` | `969` | Source video must decode at least this many frames. |

Frame-count examples at 16 fps:

| Seconds | Frames (`seconds*16+1`) |
| --- | --- |
| 5 | 81 |
| 10 | 161 |
| 15 | 241 |
| 20 | 321 |
| 60 | 961 |

SANA-Streaming V2V long uses 969 by default because its long training/inference horizon is model-specific rather than exactly `60*16+1`.

## Resolution and latent stride facts

| Family | Pixel size | VAE | Latent channels | Temporal/spatial stride |
| --- | --- | --- | --- | --- |
| SANA-Video 480p | `480 x 832` typical | WanVAE | 16 | `[4, 8, 8]` |
| SANA-Video 720p | `704 x 1280` typical | LTX-2 VAE | 128 | `[8, 32, 32]` |
| SANA-WM | fixed `704 x 1280` output | LTX-2 VAE | 128 | `[8, 32, 32]` |
| SANA-WM streaming | fixed `704 x 1280` output | causal LTX-2 VAE | 128 | `[8, 32, 32]` |
| SANA-Streaming V2V | default `704 x 1280` | LTX-2 / chunk-tile LTX-2 | 128 | `[8, 32, 32]` |

For 720p / world-model / streaming paths, treat 32-pixel divisibility and `8*k+1` temporal conventions as normal constraints.

## SANA-WM action DSL

The action string is a comma-separated list of segments:

```text
<keys>-<frames>,<keys>-<frames>,none-<frames>
```

Examples:

```text
w-100,dw-60,w-100,aw-60
w-35,aw-60,dw-100,aw-55,w-25,none-50
w-80,dw-40,w-80,aw-40
```

Allowed keys and updated mapping:

| Key | Meaning |
| --- | --- |
| `w` | forward |
| `s` | back |
| `a` | yaw left |
| `d` | yaw right |
| `i` | pitch up |
| `k` | pitch down |
| `j` | strafe left |
| `l` | strafe right |
| `none` | hold/no keys for the segment |

Important update:

- `a/d` are now yaw, not strafe.
- `j/l` are now strafe, not yaw.
- Swap `a/d` with `j/l` if reproducing older-release action strings.

Action rollout details:

- Segment durations must be positive integers.
- Held keys are de-duplicated in the native rollout.
- The rollout returns `(N+1,4,4)` camera-to-world poses for `N` held-key frames.
- Default speeds are `translation_speed=0.025` and `rotation_speed_deg=0.6` per frame.
- Motion is smoothed: new key presses take effect immediately, releases coast gently.

Validate action strings without running a model:

```bash
python sub-skills/video-world-streaming/scripts/validate_camera_controls.py \
  --action "w-80,dw-40,w-80,aw-40" \
  --num-frames 241 \
  --wm-streaming
```

## SANA-WM camera trajectory `.npy`

`--camera` expects a NumPy `.npy` array with shape:

```text
(F, 4, 4)
```

Semantic contract:

- Each matrix is camera-to-world (`c2w`).
- Coordinate convention is OpenCV-style: `+X` right, `+Y` down, `+Z` forward.
- Bottom row should be close to `[0, 0, 0, 1]`.
- Rotation determinants should be close to `1`.
- If the file has more frames than requested, native code truncates. If fewer, generation is capped by trajectory length.

Validation command:

```bash
python sub-skills/video-world-streaming/scripts/validate_camera_controls.py \
  --camera camera_c2w.npy \
  --num-frames 321
```

SANA-WM benchmark trajectory exports use `.npz` files containing arrays such as:

- `c2w`: `(961,4,4)`.
- `intrinsics`: `(961,3,3)`.
- `fps`: scalar `16`.
- `num_frames`: scalar `961`.

For runtime generation, extract the arrays to `.npy` or otherwise provide equivalent `.npy` files to the command surface.

## SANA-WM intrinsics `.npy`

Accepted `--intrinsics` shapes:

| Shape | Meaning | Native handling |
| --- | --- | --- |
| `(3,3)` | Single camera intrinsics matrix | Broadcast to all frames. |
| `(F,3,3)` | Per-frame intrinsics matrices | Truncated, broadcast if one frame, or time-resampled to requested frame count. |
| `(4,)` | `[fx, fy, cx, cy]` vector | Broadcast to all frames. |
| `(F,4)` | Per-frame `[fx, fy, cx, cy]` vectors | Truncated, broadcast if one frame, or time-resampled. |

If omitted:

- SANA-WM estimates intrinsics with Pi3X from the input image.
- It scales the estimate back to source image pixels and then transforms it to the 704 x 1280 crop.
- It aborts if horizontal or vertical FOV is outside `[25°, 120°]`.

Use the bundled validator:

```bash
python sub-skills/video-world-streaming/scripts/validate_camera_controls.py \
  --intrinsics intrinsics.npy \
  --num-frames 321
```

## Source video for SANA-Streaming V2V

`--video_path` accepts:

- A local MP4 path.
- An `hf://<repo>/<path>` URI for released demo videos.

Decode behavior:

- The script reads frames with PyAV via ImageIO until `num_frames` are collected.
- If no frames are decoded, it raises an error.
- If fewer than `num_frames` are decoded and `num_frames != 81`, it raises a short-decode error.
- Frames are resized/cropped to `height x width` and normalized to `[-1, 1]` before VAE encoding.

Practical validation:

```bash
python - <<'PY'
import imageio.v3 as iio
path = "input.mp4"
count = 0
for _ in iio.imiter(path, plugin="pyav"):
    count += 1
print(count)
PY
```

Compare the printed count with planned `--num_frames`.

## Output MP4 checks

After any generation run, verify:

- Output path exists.
- File size is nonzero and grows for progressive streaming output.
- The MP4 decodes at least one frame.
- Decoded frame count matches the expected workflow when feasible.
- Resolution matches the planned `height x width`.

Minimal decode check:

```bash
python - <<'PY'
import imageio.v3 as iio
path = "output.mp4"
frames = 0
shape = None
for frame in iio.imiter(path, plugin="pyav"):
    frames += 1
    shape = frame.shape
print({"frames": frames, "last_shape": shape})
PY
```

For SANA-WM streaming, the MP4 may be valid and grow while inference is still running. Check again after process completion for final frame count.
