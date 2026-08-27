# Video Workflow

## When to read

Read this for video-to-video style transfer, frame-sequence stylization, optical-flow preprocessing, or temporal consistency settings. For still images, use the image route first and then add advanced controls only as needed.

## Pipeline shape from the source wrapper

The repo-maintained video wrapper performs these steps:

1. Locate `ffmpeg` or `avconv`; it also uses `ffprobe` to read stream width and height.
2. Ask the user to confirm dependencies and CUDA availability.
3. Refuse the run unless the user says a CUDA GPU is available.
4. Convert the input video into PPM frames under a temporary video-input folder.
5. Compute optical flow and reliability masks between adjacent frames.
6. Run `python neural_style.py --video ...` over the frame range.
7. Assemble output frames back into a video.
8. Delete the temporary frame folder.

The bundled planner script preserves the command order but does not execute heavy or destructive steps. Use it to review paths, basename sanitization, frame formats, and neural-style flags:

```bash
python sub-skills/video-stylization/scripts/plan_video_pipeline.py \
  --video ./clip.mp4 \
  --style ./styles/kandinsky.jpg \
  --work-dir ./video_input \
  --output-dir ./video_output \
  --end-frame 50 \
  --device /gpu:0
```

## Source defaults and important flags

| Flag | Source default | Meaning |
| --- | --- | --- |
| `--video` | false | Enables video/frame loop. |
| `--start_frame` | `1` | First frame number. |
| `--end_frame` | `1` | Last frame number. |
| `--first_frame_type` | `content` | Init image for the first frame in source code. |
| `--init_frame_type` | `prev_warped` | Init image for later frames. Requires flow files. |
| `--video_input_dir` | `./video_input` | Directory containing input frames and flow files. |
| `--video_output_dir` | `./video_output` | Directory for stylized output frames. |
| `--content_frame_frmt` | `frame_{}.ppm` | Python `str.format` template used by source to load frames. |
| `--backward_optical_flow_frmt` | `backward_{}_{}.flo` | Current-to-previous flow filename template. |
| `--forward_optical_flow_frmt` | `forward_{}_{}.flo` | Previous-to-current flow filename template. |
| `--content_weights_frmt` | `reliable_{}_{}.txt` | Reliability/consistency mask filename template. |
| `--temporal_weight` | `200.0` | Weight added to temporal loss after the first frame. |
| `--first_frame_iterations` | `2000` | Iterations for frame 1. |
| `--frame_iterations` | `800` | Iterations for subsequent frames. |

The README text and source are not perfectly aligned in all places. Prefer the source defaults above when constructing commands for the inspected commit.

## Planning from a video file

The source wrapper extracts frames as PPM files. For a clip named `input%demo.mp4`, the wrapper replaces `%` with `x` in the basename before creating a temporary folder. The planner mirrors this sanitization so generated path names match source behavior.

The extracted frame pattern has two forms:

- `ffmpeg`/printf form for extraction: `frame_%04d.ppm`.
- `neural_style.py` Python-format form for loading: `frame_{}.ppm`, with frame numbers zero-padded by the source before formatting.

Do not confuse these two patterns when adapting commands.

## Planning from pre-extracted frames

If the user already has frames and flow files:

1. Confirm frame filenames match `--content_frame_frmt` after zero-padding.
2. Set `--video_input_dir` to the directory containing frames and flow files.
3. Set `--start_frame` and `--end_frame` to the available range.
4. If flow files are not available, choose `--init_frame_type prev`, `content`, `random`, or `style` instead of `prev_warped`, and explain that temporal consistency will be weaker.

## Temporal consistency

For frames after the first, the source adds a short-term temporal loss using the previous stylized frame warped to the current frame. The default `prev_warped` path requires:

- previous output frame in `--video_output_dir` using `--content_frame_frmt`;
- backward `.flo` file for current-to-previous flow;
- reliability text files for both frame directions.

Long-term temporal helper functions exist in the source, but the inspected `stylize(...)` path calls the short-term temporal loss. Do not promise long-term temporal consistency unless a refreshed checkout changes that call path.

## Safe verification strategy

Because full video renders need model weights, TensorFlow 1.x, optical-flow artifacts, and substantial compute, validate in layers:

1. Run the planner `--help` and a dry-run command plan.
2. Check `ffmpeg` and `ffprobe` availability outside a long render.
3. Validate frame and flow file names with the optical-flow reference.
4. Run a one- or two-frame smoke only when VGG weights and a compatible runtime are already present.
