# Converter API and CLI Reference

## When to read

Read this for exact RobustVideoMatting converter arguments, CLI flags,
input/output layouts, downsample logic, and practical conversion recipes.

## Verified `convert_video` signature

```python
convert_video(
    model,
    input_source: str,
    input_resize: Optional[Tuple[int, int]] = None,
    downsample_ratio: Optional[float] = None,
    output_type: str = "video",
    output_composition: Optional[str] = None,
    output_alpha: Optional[str] = None,
    output_foreground: Optional[str] = None,
    output_video_mbps: Optional[float] = None,
    seq_chunk: int = 1,
    num_workers: int = 0,
    progress: bool = True,
    device: Optional[str] = None,
    dtype: Optional[torch.dtype] = None,
)
```

Important assertions enforced by source:

- `downsample_ratio` must be `None` or `0 < downsample_ratio <= 1`.
- At least one of `output_composition`, `output_alpha`, or
  `output_foreground` must be provided.
- `output_type` must be `"video"` or `"png_sequence"`.
- `seq_chunk >= 1` and `num_workers >= 0`.

## Inputs

`input_source` can be either:

- a video file path, read through PyAV/PIMS, or
- an image-sequence directory. Files are sorted by filename.

`input_resize=(width, height)` resizes every input frame before tensor
conversion. The source code reverses this pair for TorchVision resize, so keep
the user-facing order as width then height.

## Outputs

| Argument | Video mode path | PNG sequence mode path | Meaning |
| --- | --- | --- | --- |
| `output_composition` | video file | directory | Green-screen composite for video mode; RGBA PNGs for sequence mode. |
| `output_alpha` | video file | directory | Alpha prediction. |
| `output_foreground` | video file | directory | Foreground RGB prediction. |

For video output, `output_video_mbps` defaults to `1` when omitted. For image
sequence output, bitrate is ignored.

## Downsample ratio

If `downsample_ratio` is omitted, the converter computes:

```python
min(512 / max(height, width), 1)
```

This makes the low-resolution stage's largest side no larger than 512 pixels.
Manual starting points from the RVM docs:

| Resolution | Portrait | Full-body |
| --- | --- | --- |
| <= 512x512 | 1 | 1 |
| 1280x720 | 0.375 | 0.6 |
| 1920x1080 | 0.25 | 0.4 |
| 3840x2160 | 0.125 | 0.2 |

Higher ratios are not always better; choose based on subject size and memory.

## CLI flags from the source script

The source CLI constructs `Converter(variant, checkpoint, device)` and then
calls `convert_video`.

```bash
python inference.py \
  --variant mobilenetv3 \
  --checkpoint CHECKPOINT \
  --device cuda \
  --input-source input.mp4 \
  --output-type video \
  --output-composition composition.mp4 \
  --output-alpha alpha.mp4 \
  --output-foreground foreground.mp4 \
  --downsample-ratio 0.25 \
  --seq-chunk 12 \
  --output-video-mbps 4
```

Flags:

- `--variant`: required, `mobilenetv3` or `resnet50`.
- `--checkpoint`: required PyTorch state-dict file.
- `--device`: required device string, usually `cpu` or `cuda`.
- `--input-source`: required video file or image sequence directory.
- `--input-resize WIDTH HEIGHT`: optional resize.
- `--downsample-ratio FLOAT`: optional.
- `--output-composition`, `--output-alpha`, `--output-foreground`: optional,
  but at least one is required.
- `--output-type`: required, `video` or `png_sequence`.
- `--output-video-mbps`: default `1`.
- `--seq-chunk`: default `1`.
- `--num-workers`: default `0`.
- `--disable-progress`: disables tqdm progress.

## Bundled image-sequence wrapper

Use this skill's helper when the user has a local checkpoint and frame
directory, especially when avoiding video codecs:

```bash
python scripts/rvm_convert_image_sequence.py \
  --repo-root /path/to/RobustVideoMatting \
  --variant mobilenetv3 \
  --checkpoint rvm_mobilenetv3.pth \
  --input-dir frames \
  --output-dir outputs \
  --device cpu \
  --downsample-ratio 1 \
  --alpha --composition
```

The helper writes `outputs/alpha/`, `outputs/composition/`, and optionally
`outputs/foreground/`. If no output option is provided, it defaults to
composition plus alpha. It does not download weights.

## Frozen TorchScript note

The converter normally infers `device` and `dtype` from `next(model.parameters())`.
For a frozen TorchScript model, pass `device` and `dtype` explicitly to
`convert_video`, because frozen modules may not expose parameters in the same
way.
