# Troubleshooting

## TensorFlow 2.x import or runtime failures

**Symptoms:** `AttributeError: module 'tensorflow' has no attribute 'Session'`, `AttributeError: module 'tensorflow' has no attribute 'contrib'`, or failure around `tf.contrib.opt.ScipyOptimizerInterface`.

**Likely cause:** `neural_style.py` is written for TensorFlow 1.x. TensorFlow 2 removed `tf.contrib` and changes eager/session behavior.

**Recovery:** Use a TensorFlow 1.x-compatible runtime for this repo, or explicitly port the source before running. For command construction only, use `scripts/inspect_cli_defaults.py` because it does not import TensorFlow.

## Protobuf descriptor errors with TensorFlow 1.x

**Symptom:** `TypeError: Descriptors cannot not be created directly` while importing TensorFlow 1.15.

**Likely cause:** TensorFlow 1.x generated protobuf files are incompatible with protobuf 4.x.

**Recovery:** In a private legacy runtime, use `protobuf<3.21` such as `protobuf==3.20.3`, then rerun `python -m pip check` and `scripts/check_runtime.py`.

## Missing VGG-19 `.mat` weights

**Symptoms:** `scipy.io.loadmat` error, file-not-found error for `imagenet-vgg-verydeep-19.mat`, or graph construction never starts.

**Likely cause:** The repo does not bundle VGG-19 MatConvNet weights; they must be downloaded/provided separately.

**Recovery:** Pass `--model_weights /path/to/imagenet-vgg-verydeep-19.mat` or run from a directory containing the default filename. Use `scripts/check_runtime.py --model-weights <file>` before a long render.

## OpenCV image read returns no image

**Symptoms:** `OSError: [Errno 2] No such file`, missing content/style/mask image, or unexpected path in error.

**Likely causes:**

- The command passed a full path as `--content_img` instead of splitting directory and filename.
- `--style_imgs_dir` points at a different directory from style image filenames.
- Mask filenames are not under `--content_img_dir`.
- The path uses shell `~` in a context that did not expand.

**Recovery:** Use the bundled image command builder for still-image paths. It derives directory/name flags and expands `~` before printing a command. For masks, read the advanced-controls troubleshooting page.

## GPU is visible but TensorFlow cannot use it

**Symptoms:** TensorFlow reports no GPU, CUDA library load failures, invalid device, or GPU kernel incompatibility.

**Likely cause:** Host GPU visibility does not guarantee an old TensorFlow 1.x GPU wheel matches the driver, CUDA/cuDNN version, Python version, or GPU architecture.

**Recovery:** Treat GPU as an optional backend unless the user explicitly requires full video rendering. Verify TensorFlow GPU with `scripts/check_runtime.py --check-gpu`; otherwise pass `--device /cpu:0` for CPU-compatible command review or small smokes.

## Process is killed or runs out of memory

**Symptoms:** killed process, TensorFlow allocation error, no output before optimizer completion, or severe slowdown.

**Likely causes:** Large `--max_size`, L-BFGS optimizer memory, high frame count, multiple styles, or GPU VRAM limits.

**Recovery:** Lower `--max_size`, try `--optimizer adam`, run fewer iterations for smoke, shorten video frame ranges, and avoid judging quality from a one-iteration smoke.

## Interactive shell wrappers block automation

**Symptoms:** `stylize_image.sh` or `stylize_video.sh` waits for dependency/GPU prompts.

**Likely cause:** The repo shell wrappers are designed for interactive use.

**Recovery:** Use bundled planners/builders instead of copying wrapper prompts into automation:

- still images: `sub-skills/image-stylization/scripts/build_image_command.py`;
- advanced flags: `sub-skills/advanced-controls/scripts/plan_advanced_args.py`;
- video pipeline: `sub-skills/video-stylization/scripts/plan_video_pipeline.py`.

## Video prerequisites fail

**Symptoms:** missing `ffmpeg`, missing `ffprobe`, missing `.flo` files, missing `reliable_*.txt`, or static optical-flow binary failures.

**Likely causes:** Video is a multi-stage workflow: frame extraction, optical flow, temporal consistency masks, TensorFlow rendering, and video assembly. The source binaries are platform-specific and full execution is expensive.

**Recovery:** Use the video planner first, verify `ffmpeg`/`ffprobe`, then inspect `video-stylization/references/optical-flow-files.md`. If flow files cannot be produced, switch `--init_frame_type` from `prev_warped` to `prev` or `content` and explain the temporal-consistency tradeoff.

## Full render verification is unavailable

**Symptoms:** The user wants proof of artistic output quality but the environment lacks VGG weights, GPU, or time budget.

**Recovery:** Be explicit about the verification boundary. CLI help, parser defaults, command builders, and runtime imports can be checked without a render; full image/video output requires VGG weights and a compatible runtime. If the user supplies weights, run a tiny disposable smoke before a real render.
