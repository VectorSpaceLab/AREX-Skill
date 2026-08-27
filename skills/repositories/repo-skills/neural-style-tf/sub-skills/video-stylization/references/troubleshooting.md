# Video Troubleshooting

## `ffmpeg` or `ffprobe` is missing

**Symptoms:** the wrapper aborts before frame extraction, or width/height detection is empty.

**Likely cause:** `stylize_video.sh` checks for `ffmpeg` or `avconv`, but it also calls `ffprobe` directly. Having only `avconv` is not enough for the inspected wrapper path.

**Recovery:** Install/provide both frame extraction and probe tools, or pre-extract frames and run `neural_style.py --video` against a frame directory with explicit `--max_size`.

## Wrapper refuses CPU video runs

**Symptom:** `Error: GPU required to render videos in a feasible amount of time.`

**Likely cause:** The source wrapper asks whether CUDA is available and exits unless the answer is `y`. The Python script itself has a `--device` choice of `/gpu:0` or `/cpu:0`, but full video on CPU is normally impractical.

**Recovery:** Use the planner to review commands on CPU, but run full video only in a compatible TensorFlow 1.x GPU environment. For CPU-only smoke, use a tiny one-frame or two-frame setup and lower iteration counts.

## Missing VGG-19 weights

**Symptoms:** `scipy.io.loadmat` fails, or the script cannot find `imagenet-vgg-verydeep-19.mat`.

**Likely cause:** The repo requires external MatConvNet VGG-19 weights; they are not bundled with the generated skill.

**Recovery:** Put the weights where `neural_style.py` will run or pass `--model_weights /path/to/imagenet-vgg-verydeep-19.mat`. Verify path existence before a video run.

## `prev_warped` fails on frame 2 or later

**Symptoms:** missing `.flo` file, missing `reliable_*.txt`, OpenCV remap errors, or previous-frame image read failures.

**Likely causes:**

- Optical-flow files were not generated with the expected `backward_{current}_{previous}.flo` and `reliable_{previous}_{current}.txt` names.
- `--video_input_dir` points at frames but not flow/reliability files.
- `--video_output_dir` does not contain the previous stylized frame.
- `--content_frame_frmt` mismatch causes previous output frame lookup to fail.

**Recovery:** Read `optical-flow-files.md`, confirm frame numbers and unpadded flow filenames, or switch to `--init_frame_type prev`/`content` when flow is unavailable.

## Frame numbering or format mismatch

**Symptoms:** first frame loads but later frames do not, or `No such file` errors refer to unexpected names like `frame_0001.ppm`.

**Likely cause:** The source zero-pads frame numbers before applying `--content_frame_frmt`, whose default is `frame_{}.ppm`. The ffmpeg extraction pattern is different: `frame_%04d.ppm`.

**Recovery:** Keep the extraction pattern and Python format template consistent: extraction creates `frame_0001.ppm`; `neural_style.py` loads it using `frame_{}.ppm` after converting frame `1` to `0001`.

## Output video is missing even though frames were produced

**Symptoms:** stylized frame files exist, but the final `.mp4`/`.mov`/`.mkv` does not.

**Likely causes:** ffmpeg assembly failed, extension or output directory is wrong, or wrapper cleanup removed temporary inputs before debugging.

**Recovery:** Assemble from `--video_output_dir` manually with a known frame pattern. The bundled planner intentionally avoids deletion so intermediate paths can be inspected.

## Static optical-flow binaries do not run

**Symptoms:** `Permission denied`, `Exec format error`, segmentation fault, or missing shared/runtime assumptions despite static binaries.

**Likely cause:** The repo binaries are Linux x86_64 executables from an old pipeline and may not work on the current platform or container.

**Recovery:** Do not copy those binaries into new generated skill content. Use a platform-compatible optical-flow tool that emits `.flo` plus reliability masks, or choose a non-warped initialization mode.

## Video command consumes too much memory or time

**Symptoms:** TensorFlow allocation failure, process killed, very slow frame rendering, or GPU out-of-memory.

**Recovery:** Lower `--max_size`, reduce `--first_frame_iterations` and `--frame_iterations` for a smoke pass, try `--optimizer adam`, shorten the frame range, and keep one style image until the pipeline works. Increase complexity only after a tiny frame-range command succeeds.
