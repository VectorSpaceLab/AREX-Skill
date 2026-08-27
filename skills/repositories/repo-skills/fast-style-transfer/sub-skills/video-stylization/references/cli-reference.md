# Video Stylization CLI Reference

## Bundled video stylization runtime flags

| Flag | Required | Default | Meaning |
| --- | --- | --- | --- |
| `--checkpoint CHECKPOINT` | yes | none | Checkpoint directory or `.ckpt` path/prefix. |
| `--in-path IN_PATH` | yes | none | Input video path. |
| `--out-path OUT` | yes | none | Output video path. |
| `--tmp-dir TMP_DIR` | no | random `.fns_frames_<n>/` | Parsed but not used by the inspected `main()` frame flow. |
| `--device DEVICE` | no | `/gpu:0` | TensorFlow device for frame batches. |
| `--batch-size BATCH_SIZE` | no | `4` | Number of frames per TensorFlow batch. |
| `--no-disk NO_DISK` | no | `False` | Parsed as a bool option but not used by the inspected `main()` frame flow. |

## Verified callable signature

```python
evaluate.ffwd_video(path_in, path_out, checkpoint_dir, device_t='/gpu:0', batch_size=4)
```

## Behavior notes

- `transform_video.py main()` parses options, then calls `evaluate.ffwd_video(opts.in_path, opts.out, opts.checkpoint, opts.device, opts.batch_size)`.
- `check_opts` exists in the source and checks checkpoint/output path existence, but the inspected `main()` does not call it before invoking `ffwd_video`.
- `evaluate.ffwd_video` relies on moviepy for reading frames and ffmpeg writing.
- The transform network graph is built with frame height/width from the input video.
- The last partial batch is padded by repeating the final real frame for inference, but only real frame outputs are written.

## Safer command construction

Because `main()` does not call `check_opts`, use the bundled validator to catch missing input/checkpoint/output-parent errors before the actual command:

```bash
python sub-skills/video-stylization/scripts/validate_video_stylization_inputs.py --checkpoint ckpt --in-path input.mp4 --out-path output.mp4 --check-dependencies --probe-video
```

Then run:

```bash
python sub-skills/video-stylization/scripts/run_video_stylization.py --checkpoint ckpt --in-path input.mp4 --out-path output.mp4 --device /gpu:0 --batch-size 4
```

## `--tmp-dir` and `--no-disk` caveat

Older documentation describes temporary frame directories. In the inspected code path, video frames are streamed through moviepy and `evaluate.ffwd_video`; `--tmp-dir` and `--no-disk` do not control the main processing path. Do not promise disk-frame behavior unless the user's checkout has changed and has been refreshed.
