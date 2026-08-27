# ECCV2022-RIFE interpolation CLI reference

This reference distills the repository's image-pair and video/PNG-sequence inference scripts so a future agent can build correct commands without reopening source files.

## Shared prerequisites

- Run commands from a source checkout that contains `inference_img.py`, `inference_video.py`, and the `model/` package.
- Install runtime dependencies equivalent to `numpy`, `tqdm`, `sk-video`, `torch`, `opencv-python`, `moviepy`, and `torchvision`. Video reading/writing and audio transfer also require an available `ffmpeg` executable.
- Provide pretrained weights externally. The default checkpoint directory is `train_log`; use `--model <checkpoint-dir>` for any other location.
- For the current source fallback path, the checkpoint directory must contain `flownet.pkl`. The loader strips `module.` prefixes from the saved state dict.
- Inference selects `cuda` automatically when `torch.cuda.is_available()` is true; otherwise it uses CPU. There is no source CLI flag to force CPU, but `CUDA_VISIBLE_DEVICES=""` can hide GPUs.

## Model import and checkpoint behavior

The inference scripts try model classes in this order:

1. `model.RIFE_HDv2.Model`
2. `train_log.RIFE_HDv3.Model`
3. `model.RIFE_HD.Model`
4. fallback: `model.RIFE.Model`

In this checkout, active `model.RIFE_HDv2` and `model.RIFE_HD` modules are not present at those import paths, so ordinary runs fall back to `model.RIFE.Model`. Legacy HD files may exist elsewhere in the source tree, but they are not imported by the current CLIs unless the user supplies compatible extra files. Do not promise HD-model behavior unless the user has verified the exact model code and weights.

## `inference_img.py`: image-pair interpolation

### Command shape

```bash
python inference_img.py --img img0.png img1.png --exp 4 --model train_log
python inference_img.py --img img0.png img1.png --ratio 0.25 --rthreshold 0.02 --rmaxcycles 8 --model train_log
```

### Options

| Option | Meaning | Notes |
| --- | --- | --- |
| `--img A B` | Required two input images. | Both images must be readable by OpenCV and should have compatible dimensions/channels. |
| `--exp N` | Recursive midpoint expansion. | Produces a `2^N` interval sequence: endpoints plus generated intermediate frames. Default is `4`, which creates 16X spacing and writes 17 images. Ignored by the source logic when a truthy `--ratio` is used. |
| `--ratio R` | Arbitrary target timestep between the two input images. | `0 < R < 1` requests a single target timestep by bisection. The script writes the first input, the selected middle frame, and the second input. `0` disables ratio mode because the source checks truthiness. |
| `--rthreshold T` | Ratio tolerance. | Default `0.02`; the bisection stops when the midpoint ratio is inside `R ± T/2`. |
| `--rmaxcycles N` | Max bisection cycles for `--ratio`. | Default `8`; larger values can improve timestep precision but add model calls. |
| `--model DIR` | Checkpoint directory. | Default `train_log`; for fallback `model.RIFE`, expect `DIR/flownet.pkl`. |

### Inputs and outputs

- PNG/JPEG-like inputs are read with `cv2.imread(..., IMREAD_UNCHANGED)`, converted to a tensor in OpenCV channel order, scaled by `1/255`, and written back with `cv2.imwrite`.
- If both input filenames end with `.exr`, the script reads them with `IMREAD_ANYDEPTH` and writes `output/img*.exr` using half EXR output.
- All outputs are written under `output/` relative to the current working directory:
  - non-EXR: `output/img0.png`, `output/img1.png`, ...;
  - EXR pair: `output/img0.exr`, `output/img1.exr`, ...
- The image tensors are padded to the next multiple of 32, and outputs are cropped back to the original height and width.

## `inference_video.py`: video and numbered PNG-sequence interpolation

### Command shapes

```bash
python inference_video.py --video input.mp4 --exp 1 --model train_log
python inference_video.py --video input.mp4 --exp 2 --output output_4x.mp4 --model train_log
python inference_video.py --img frames --exp 2 --png --model train_log
python inference_video.py --video input.mp4 --exp 1 --scale 0.5 --model train_log
python inference_video.py --video input.mp4 --montage --png --model train_log
```

### Options

| Option | Meaning | Notes |
| --- | --- | --- |
| `--video PATH` | Input video file. | Uses OpenCV to inspect FPS/frame count and `skvideo.io.vreader` to stream frames. Either `--video` or `--img` is required; avoid passing both. |
| `--output PATH` | Output video path. | Used only for video output. If omitted, the script derives `<input>_<2^exp>X_<fps>fps.<ext>`. |
| `--img DIR` | Directory of PNG frames. | Forces `--png` behavior. Source expects numeric PNG names such as `0.png`, `1.png`, ..., because it sorts with `int(name_without_.png)`. |
| `--montage` | Create side-by-side montage frames. | The script crops the center half of the input frame and writes pairs of original/reference and interpolated frames side by side. |
| `--model DIR` | Checkpoint directory. | Default `train_log`; for fallback `model.RIFE`, expect `DIR/flownet.pkl`. |
| `--fp16` | Use half tensors on CUDA. | Only activated when CUDA is available; intended for Tensor Core GPUs. Avoid on CPU and be cautious on unsupported CUDA devices. |
| `--UHD` | UHD helper. | If `--scale` is still `1.0`, this changes it to `0.5`. Useful for 4K/high-resolution processing. |
| `--scale S` | Model processing scale. | Must be one of `0.25`, `0.5`, `1.0`, `2.0`, `4.0`. README recommends `0.5` for 4K and trying `2.0` for disordered patterns. |
| `--skip` | Deprecated static-frame flag. | Current script prints that the flag is abandoned; do not rely on it. |
| `--fps N` | Explicit output FPS. | If omitted for video input, output FPS is input FPS times `2^exp`; if set, audio will not be merged. |
| `--png` | Write PNG frames instead of a video. | Outputs `vid_out/0000000.png`, ... relative to the current working directory. Also disables audio merge. |
| `--ext EXT` | Output video extension. | Default `mp4`; OpenCV writer still uses `mp4v` fourcc. |
| `--exp N` | Interpolation factor exponent. | Factor is `2^N`; generated intermediate frames per adjacent pair are `2^N - 1`. Default is `1` for 2X. |

### Outputs and audio behavior

- PNG output writes `vid_out/{frame_index:07d}.png` relative to the current working directory.
- Video output writes either `--output` or a derived name such as `input_2X_60fps.mp4`.
- Audio merge is attempted only when all are true:
  - input is a video file;
  - output is a video, not PNG frames;
  - `--fps` was not manually supplied.
- Audio transfer uses `ffmpeg` to copy audio to a temporary file and then mux it into the interpolated video. If lossless copy fails, it retries AAC audio; if that also fails, the output remains silent.

### Video frame processing details

- Frames are padded before model inference. The padding multiple is `max(32, int(32 / scale))` for video; image-pair mode always pads to multiples of 32.
- `--scale` changes the optical-flow processing resolution passed into `Model.inference`, not the final output dimensions.
- The script has built-in scene/static heuristics: very similar frames may be skipped ahead internally, and very dissimilar frames may be repeated instead of flow-interpolated to avoid bad scene cuts.
- For PNG-frame input, OpenCV reads frames in BGR and the script reverses channels for internal processing, then reverses back before writing.

## Safe helper

Use the bundled helper to build commands and optionally validate paths/checkpoints without running inference:

```bash
python sub-skills/interpolation/scripts/interpolation_command_builder.py --validate image --img img0.png img1.png --ratio 0.25 --model train_log
python sub-skills/interpolation/scripts/interpolation_command_builder.py --validate video --img frames --exp 2 --png --scale 0.5 --model train_log
```
