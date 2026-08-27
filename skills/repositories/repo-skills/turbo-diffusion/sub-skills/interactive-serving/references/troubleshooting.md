# Interactive serving troubleshooting

Use this matrix for TUI launch and interactive-loop problems. Route CUDA extension installation, SpargeAttn/SageSLA builds, custom INT8/FastNorm failures, and full backend smoke checks to the acceleration-backends sub-skill.

## Launch/import failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'imaginaire'` from `turbodiffusion-serve` or `python -m turbodiffusion.serve` | Source-layout modules are imported as top-level packages, but the source-layout directory is not on `PYTHONPATH`. | Relaunch with a public source-layout prefix such as `PYTHONPATH=turbodiffusion turbodiffusion-serve ...`, or set the equivalent directory for the user's packaging layout. |
| `ModuleNotFoundError: No module named 'rcm'` | Same source-layout quirk; serving validates resolutions via `rcm.datasets.utils`. | Add the source-layout directory that contains `rcm` to `PYTHONPATH`. Do not hardcode private checkout paths in reusable instructions. |
| Help prints `Megatron-core is not installed.` before normal usage output | Optional training dependency warning surfaced during imports; help can still succeed. | If the command continues to show usage and exits 0, it is not a serving blocker. Route actual training dependency needs to training-and-checkpoints. |
| `No module named turbo_diffusion_ops` or CUDA extension import/build errors | Custom acceleration extension is absent or incompatible. | Do not solve from the TUI. Route to acceleration-backends for build prerequisites, CUDA toolkit/CUTLASS, and custom-op checks. |
| `attention_type=sagesla` fails during model construction | Optional SpargeAttn/SageSLA dependency is unavailable or incompatible. | Use `--attention_type sla` or `--attention_type original` if acceptable, or route to acceleration-backends for SageSLA installation guidance. |

## Mode-specific validation

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `--dit_path is required for t2v mode` | T2V launch omitted the DiT checkpoint. | Add `--mode t2v --dit_path PATH_TO_T2V_CHECKPOINT`. Do not pass I2V high/low paths as a substitute. |
| `--high_noise_model_path and --low_noise_model_path are required for i2v mode` | I2V launch omitted one or both model paths. | Provide both paths: `--mode i2v --high_noise_model_path PATH_HIGH --low_noise_model_path PATH_LOW`. The TUI will ask for the input image later; image path is not a launch argument. |
| I2V starts with one high/low path accidentally pointing to the same file | The parser only checks presence, not semantic high/low pairing. | Verify checkpoint names/metadata before launch. High-noise and low-noise paths should be distinct files from the same I2V checkpoint family and quantization variant. |
| Quantized checkpoint is slow or errors with shape/module mismatch | `--quant_linear` does not match the checkpoint's conversion format. | Use `--quant_linear` for quantized checkpoints and omit it for unquantized checkpoints. Changing this requires a server restart. |

## Resolution and aspect-ratio errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Invalid resolution: VALUE` | `--resolution` is not in the server's resolution map. | Use one of `480p`, `720p`, `480`, `512`, or `720`. Prefer the documented `480p` for T2V defaults and `720p` for I2V defaults unless the checkpoint supports another size. |
| `Invalid aspect ratio: VALUE` | The selected resolution does not have that `--aspect_ratio` key. | Use `1:1`, `4:3`, `3:4`, `16:9`, or `9:16`. |
| I2V output size is surprising with `--adaptive_resolution` | Adaptive mode uses the selected resolution/aspect-ratio area as a budget, then adapts width/height to the entered image's aspect ratio. | Disable `--adaptive_resolution` for fixed dimensions, or keep it and explain that the input image aspect ratio controls the final dimensions. |

## Interactive prompt-loop issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| A prompt line was submitted too early | Multiline prompts require a trailing backslash. | End each continued line with `\`; the server joins lines with newlines before generation. |
| I2V prints `Error: File not found: ...` then `Cancelled.` | The image path entered at the interactive `image` prompt does not exist. | Enter an existing local image path when prompted. The server keeps running and will accept another prompt. |
| Output prompt appears to ignore a missing extension | The TUI appends `.mp4` when the entered output path has no `.mp4` suffix. | Enter the full filename if a specific path is required; otherwise accept the default and note the automatic extension. |
| EOF or `Ctrl-C` at prompt exits or cancels | `KeyboardInterrupt`/EOF is handled by prompt collection. | At the main prompt it exits the server; at image/output prompts it cancels the current generation and returns to the loop when possible. Relaunch only if the process exited. |
| Generation raises an exception but the prompt returns | The TUI catches generation exceptions, prints a traceback, and continues the loop. | Read the first error line. Path/config errors can be fixed in the next prompt only if they concern interactive image/output entries; launch-only config errors require restart. Backend errors should be routed to acceleration-backends. |

## `/set` validation

| Command | Result | Fix |
| --- | --- | --- |
| `/set` with too few or too many tokens | `Usage: /set <param> <value>` | Use exactly one parameter name and one value token. |
| `/set resolution 720p` | Not a runtime parameter. | Restart with `--resolution 720p`; resolution is launch-only. |
| `/set num_steps 5` | `num_steps must be one of [1, 2, 3, 4]` | Choose `1`, `2`, `3`, or `4`. |
| `/set num_samples 0` | `num_samples must be >= 1` | Use at least `1`; higher values increase memory. |
| `/set num_frames 0` | `num_frames must be >= 1` | Use at least `1`; realistic video settings are much larger and require more memory. |
| `/set sigma_max 0` | `sigma_max must be >= 0.1` | Use `>= 0.1`; source defaults are `80` for T2V and `200` for I2V. |
| `/set num_steps two` | Invalid typed value. | Use a numeric value matching the parameter type. |

## When to restart the server

Restart the TUI process to change any launch-only setting: mode, model architecture, checkpoint paths, VAE/text encoder paths, resolution, aspect ratio, attention type, `sla_topk`, quantization, default norm, I2V boundary, adaptive resolution, ODE sampling, or seed. Use `/set` only for `num_steps`, `num_samples`, `num_frames`, and `sigma_max`.
