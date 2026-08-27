# ECCV2022-RIFE interpolation workflows

These recipes assume a source checkout, installed dependencies, and a checkpoint directory such as `train_log` containing model weights. Use the bundled command builder first when inputs or checkpoint paths may be wrong.

## Preflight checklist

1. Choose an inference type: image pair, video file, or numbered PNG directory.
2. Confirm model weights:
   ```bash
   test -f train_log/flownet.pkl
   ```
   For a custom directory, replace `train_log` and pass `--model <dir>`.
3. Confirm outputs can be written in the current working directory. The source scripts create `output/`, `vid_out/`, and sometimes `temp/` relative to where they run.
4. For video workflows, confirm `ffmpeg` is installed and visible on `PATH`. Audio transfer and many `skvideo` paths depend on it.
5. For a potentially long video or 4K job, build the command and ask before execution.

## Build commands without running inference

The helper prints the exact source command it would run and can validate inputs/checkpoints:

```bash
python sub-skills/interpolation/scripts/interpolation_command_builder.py --validate image --img frame0.png frame1.png --exp 4 --model train_log
python sub-skills/interpolation/scripts/interpolation_command_builder.py --validate video --video input.mp4 --exp 2 --scale 0.5 --model train_log
```

If the helper reports missing paths or an invalid checkpoint directory, fix those before running the source script.

## Image pair: fixed 2X/4X/16X interpolation

Use `--exp N`, where the temporal factor is `2^N`.

```bash
python inference_img.py --img img0.png img1.png --exp 1 --model train_log
python inference_img.py --img img0.png img1.png --exp 2 --model train_log
python inference_img.py --img img0.png img1.png --exp 4 --model train_log
```

Expected output:

- `--exp 1`: `output/img0.png`, middle frame, and final endpoint (3 images total).
- `--exp 2`: 4X spacing (5 images total).
- `--exp 4`: 16X spacing (17 images total).

The source always includes the two input endpoints in the output sequence. If both input names end with `.exr`, the output names are `output/img*.exr`.

## Image pair: arbitrary timestep with `--ratio`

Use `--ratio` when the user wants one specific intermediate time, such as 0.25 between the first and second frame:

```bash
python inference_img.py --img img0.png img1.png --ratio 0.25 --rthreshold 0.01 --rmaxcycles 10 --model train_log
```

Guidance:

- Use `0 < ratio < 1` for an actual intermediate frame.
- Smaller `--rthreshold` and larger `--rmaxcycles` can improve timestep targeting but add model calls.
- The script still writes a three-image sequence: first input, selected ratio frame, second input.
- `--ratio 0` is not useful for ratio mode because the source treats it as false and falls back to `--exp` recursion.

## Video file: default slow motion

For a 2X output that doubles the input FPS:

```bash
python inference_video.py --video input.mp4 --exp 1 --model train_log
```

For 4X output:

```bash
python inference_video.py --video input.mp4 --exp 2 --model train_log
```

Expected behavior:

- If `--fps` is omitted and `--png` is not used, output FPS is input FPS times `2^exp`.
- Default output name is derived from the input: for example, `input_2X_60fps.mp4`.
- Audio transfer is attempted after interpolation when output is a video and FPS was not manually overridden.

Use `--output` to choose the output file explicitly:

```bash
python inference_video.py --video input.mp4 --exp 2 --output input_rife_4x.mp4 --model train_log
```

## Video file: target FPS / slow-motion effect

If the user wants a specific output FPS rather than automatic multiplication:

```bash
python inference_video.py --video input.mp4 --exp 2 --fps 60 --output input_60fps.mp4 --model train_log
```

Caveat: when `--fps` is supplied, the current script does **not** merge audio. Explain that the result will be silent unless the user separately muxes or edits audio afterward.

## Numbered PNG frame directory

Use this route when the user has extracted frames instead of a video file:

```bash
python inference_video.py --img frames --exp 2 --png --model train_log
```

Requirements:

- The directory must contain PNG files whose stems are integers: `0.png`, `1.png`, `2.png`, ... .
- Avoid names such as `frame_0001.png` unless they are renamed, because the script sorts with `int(filename_without_extension)`.
- `--img` forces PNG output, even if `--png` is omitted.

Expected output:

```text
vid_out/0000000.png
vid_out/0000001.png
...
```

To create a video from the PNG output afterward, use an external ffmpeg command adjusted to the desired frame rate and size, for example:

```bash
ffmpeg -r 60 -f image2 -i vid_out/%07d.png -c:v libx264 -pix_fmt yuv420p rife_60fps.mp4
```

## UHD / 4K / high-resolution input

For high-resolution input, reduce processing scale first:

```bash
python inference_video.py --video input_4k.mp4 --exp 1 --scale 0.5 --model train_log
```

Equivalent UHD shortcut when the user has not set another scale:

```bash
python inference_video.py --video input_4k.mp4 --exp 1 --UHD --model train_log
```

Scale decisions:

- `--scale 0.5` is the repository's recommended 4K starting point.
- `--scale 2.0` can be tried if the output has disordered patterns.
- Valid values are only `0.25`, `0.5`, `1.0`, `2.0`, and `4.0`.
- The final output size stays at the original frame dimensions; scale controls model processing resolution and padding.

## Montage output

Use montage when the user wants an origin/interpolated side-by-side visual comparison:

```bash
python inference_video.py --video input.mp4 --montage --png --model train_log
```

The source crops the center half of each input frame for montage mode and writes side-by-side output frames. `--png` is common for montage review because it avoids video codec/audio complications.

## Audio transfer expectations

Audio merge is automatic only for ordinary video-to-video interpolation with no manual `--fps`:

```bash
python inference_video.py --video input.mp4 --exp 1 --output input_rife.mp4 --model train_log
```

It is not attempted for:

- `--png` output;
- PNG-directory input;
- any run with an explicit `--fps`.

If audio merge fails, the script tries AAC conversion. If that fails too, the interpolated video remains without audio. Use a separate `ffmpeg` mux if the user needs custom audio handling.

## Docker path: reference-only alternative

The repository includes Docker wrappers that call the same source scripts from inside a container. Use Docker only if the user has Docker/GPU-driver access and explicitly wants a containerized run. The wrappers use container-specific paths and should not be copied into runtime commands outside Docker.

Typical shape:

```bash
docker build -t rife -f docker/Dockerfile .
docker run --rm -it -v "$PWD:/host" rife:latest inference_video --exp 1 --video input.mp4 --output input_rife.mp4
```

GPU Docker runs require host GPU runtime support, for example `--gpus all` on a properly configured Docker installation.
