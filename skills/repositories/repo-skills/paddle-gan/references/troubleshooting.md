# Troubleshooting and recovery

Treat failures as evidence about one layer, not a reason to retry the whole workflow. Capture the command, environment (`python -m pip show ppgan paddlepaddle` or the installed Paddle variant), config path, device choice, and first traceback line. Stop heavy work while diagnosing.

## Triage order

1. Run [the install checker](../scripts/check_install.py). Add `--require-gpu`, `--require-ffmpeg`, `--require-face`, or `--require-clip` only when the task requires that capability.
2. For YAML failures, run [the config checker](../scripts/check_config.py) without execution, then add overrides one at a time. It accepts existing dotted keys and reports missing paths rather than silently creating them.
3. Check paths, permissions, free disk/RAM/VRAM, and input media independently.
4. Apply the owning leaf's recovery notes: [training](../sub-skills/training-configs/references/troubleshooting.md), [image/face](../sub-skills/image-and-face-apps/references/troubleshooting.md), [video/audio](../sub-skills/video-and-audio-apps/references/troubleshooting.md), [data](../sub-skills/data-preparation/references/troubleshooting.md), or [deployment](../sub-skills/deployment-export/references/troubleshooting.md).

## Installation and imports

**`No module named ppgan` or `paddle`.** Activate the intended environment, compare `python -m pip --version` with `python`, install Paddle first and `ppgan` second, and rerun the checker. An editable install imports the working tree; a regular install imports the built/copied package. Remove stale editable metadata or a shadowing local directory when the reported file is unexpected.

**The `paddlegan` command is missing or crashes.** The snapshot's legacy console entry point points at a non-existent module. Do not use it as a health check; use the linked skill scripts or direct `ppgan` imports instead.

**An optional import fails.** Separate core failures from optional `dlib`, CLIP, audio, or face-backend failures. Route only the requested feature to its leaf, install its extra in the active environment, and rerun a scoped check. A missing CLIP module does not block ordinary image inference.

**`librosa` reports a `pkg_resources`/setuptools error.** Resolve the version compatibility in the environment (rather than changing a workflow), then rerun the install checker. Record the chosen versions for reproducibility.

## Backend and media

**CUDA is unavailable or cuDNN cannot load.** A CPU Paddle build can still parse configs and validate layouts, but cannot substantiate GPU readiness. Select one CUDA-compatible Paddle build, verify driver/CUDA/cuDNN visibility, and check `paddle.is_compiled_with_cuda()` plus device count before retrying. Do not “fix” a CUDA failure by silently switching a requested GPU run to CPU.

**`ffmpeg not found`, decode errors, or audio/video length mismatch.** Put the system executable on `PATH`, verify `ffmpeg -version`, and confirm readable codecs, frame rate, sample rate, and duration. `imageio-ffmpeg` alone may not satisfy a subprocess lookup. Then route to [video/audio troubleshooting](../sub-skills/video-and-audio-apps/references/troubleshooting.md); preserve the failing media and ffmpeg output.

**Out-of-memory or process killed.** First reduce clip/frame resolution, batch size, worker count, or temporal window according to the owning leaf; use CPU only for a requested CPU run or a lightweight diagnostic. Clear stale workers and verify disk space for temporary frames before retrying.

## Config, data, and weights

**YAML parse, missing key, or override error.** Run [the config checker](../scripts/check_config.py) against the exact file. Confirm spelling and nesting; overrides must target existing keys and values should be quoted when YAML types matter. After a successful dry check, route to [training-configs](../sub-skills/training-configs/SKILL.md) or [deployment-export](../sub-skills/deployment-export/SKILL.md) as appropriate.

**Missing dataset folder, split, or unexpected shape.** Do not patch the model first. Route to [data-preparation](../sub-skills/data-preparation/SKILL.md), validate the layout, set an explicit `dataroot`, and check permissions and representative files. For video datasets, validate frame ordering and audio/video alignment as well.

**Weights are missing, incompatible, or auto-download hangs.** Confirm the model family, checkpoint format, expected key/prefix names, and local path. Prefer an explicit caller-owned weight path; treat network download as an opt-in operation and retain download errors for diagnosis. Then use the image/face or video/audio leaf guidance.

## Export and deployment

**Expected `.pdmodel`, `.pdiparams`, or metadata files are absent.** Route to [deployment-export](../sub-skills/deployment-export/SKILL.md). Verify the output directory, model prefix, input-size grammar, and checkpoint keys before changing runtime flags. Do not infer export success from a process exit alone.

**TensorRT, Serving, Lite, or C++ runtime fails.** Confirm the installed Paddle build exposes the requested backend and that its libraries/toolchain are present. First validate a standard Paddle Inference path, then enable one deployment feature at a time. Keep Serving startup, native compilation, and benchmarks out of diagnosis unless explicitly requested.

## Recovery boundary

After shared checks pass, stop editing the root router: use the owning leaf's troubleshooting reference for model-specific flags and fallbacks. For a multi-stage request, preserve each stage's outputs and handoff facts (config, checkpoint prefix, input shape, device, and media properties) to the next leaf. A CPU import or config parse is useful evidence, but never evidence that GPU, face, audio, TensorRT, or deployment execution will succeed.
