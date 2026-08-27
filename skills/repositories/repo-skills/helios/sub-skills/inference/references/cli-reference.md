# Inference CLI reference

This sub-skill's bundled helper lives at `scripts/run_helios_inference.py`.
It is designed to cover the common Helios generation shapes without depending
on the original repository checkout.

## Key options

| Option | Meaning |
| --- | --- |
| `--model-id` | Hub or local model identifier such as a Helios checkpoint |
| `--mode` | `t2v`, `i2v`, or `v2v` |
| `--prompt` | Text prompt used for generation |
| `--image-path` | Reference image for image-to-video |
| `--video-path` | Reference video for video-to-video |
| `--output` | Output mp4 path |
| `--height`, `--width` | Target render size |
| `--num-frames` | Number of frames to generate |
| `--guidance-scale` | Guidance strength |
| `--pyramid-steps` | Per-stage step counts for the pyramid pipeline |
| `--amplify-first-chunk` | Turn on the first-chunk boost used in the demo-style flow |
| `--skip-first-chunk` | Skip the first chunk when a task needs that behavior |
| `--use-zero-init`, `--no-use-zero-init` | Toggle the zero-init path; the live diffusers default is on |
| `--low-vram` | Enable single-GPU group offload |
| `--cp-backend` | Context parallel backend: `ring`, `ulysses`, `unified`, or `ulysses_anything` |
| `--parallelism` | Enable multi-GPU context parallelism if launched under `torchrun` |
| `--distilled` | Use the distilled scheduler path |
| `--seed` | Reproducibility seed |

## Runtime model notes

- For multi-GPU runs, launch with `torchrun`; the helper initializes the process
  group from the `RANK` environment variable and maps each rank to a CUDA device.
- The diffusers package exposes `HeliosPyramidPipeline`, `HeliosDMDScheduler`,
  `HeliosScheduler`, and `AutoencoderKLWan`.
- The pipeline constructor accepts an `is_distilled` flag.
- The local source pipeline has additional chunk/history controls; the bundled
  helper keeps the common path while remaining self-contained.

## Recommended launch sequence

1. `python scripts/check_helios_env.py`
2. `python scripts/run_helios_inference.py --help`
3. Run the actual generation command with a small prompt first.
