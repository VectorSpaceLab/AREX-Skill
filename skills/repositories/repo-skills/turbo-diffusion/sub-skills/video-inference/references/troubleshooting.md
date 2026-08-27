# Troubleshooting one-shot video inference

Use this matrix when a one-shot Wan2.1 T2V or Wan2.2 I2V command fails before or during generation. Route issues outside one-shot command construction to the owning sub-skill.

| Symptom | Likely cause | Fix or route |
| --- | --- | --- |
| Quantized checkpoint path contains `quant`, but load fails or state dict keys do not match. | `--quant_linear` was omitted, so the model was built with regular Linear layers before loading a quantized state dict. | Add `--quant_linear`. The bundled command builders catch this by default. |
| Unquantized checkpoint fails after adding `--quant_linear`. | Quantized Linear replacement was enabled for a non-quantized state dict. | Remove `--quant_linear` or use a quantized checkpoint. |
| I2V command reports a high/low model mismatch or produces poor switching behavior. | `--high_noise_model_path` and `--low_noise_model_path` may be swapped, or one path is from the wrong checkpoint family. | High path should contain the high-noise checkpoint; low path should contain the low-noise checkpoint. The I2V builder checks basename markers such as `high` and `low`. |
| I2V high checkpoint is quantized but low checkpoint is unquantized, or vice versa. | Mixed checkpoint families. | Use a matched high/low pair from the same quantized or unquantized release; only use `--allow-flag-mismatch` if filenames were customized and you have verified formats. |
| `--dit_path`, `--high_noise_model_path`, `--low_noise_model_path`, `--vae_path`, or `--text_encoder_path` missing. | Required model asset was not provisioned, or a script default points at a checkout path that does not exist in the user's environment. | Provide explicit paths. The runtime helpers require these values so missing assets stay visible and no download is attempted. |
| I2V fails opening the input image. | Missing `--image_path`, nonexistent file, unsupported suffix, or unreadable image. | Provide an existing `.jpg`, `.jpeg`, `.png`, or `.webp` file. Use the builder's `--check-files` for local existence checks before running the model. |
| Adaptive I2V output dimensions surprise the user. | `--adaptive_resolution` preserves the input image aspect ratio while matching the target area implied by `--resolution` and `--aspect_ratio`. | Disable `--adaptive_resolution` for fixed `VIDEO_RES_SIZE_INFO` dimensions, or explain that `720p 16:9` is used as an area budget rather than a fixed output shape in adaptive mode. |
| Checkpoint filename says `480P` but command uses `--resolution 720p`, or filename says `720P` but command uses `480p`. | Model catalog best-resolution and command resolution differ. The README says both resolutions are supported, but best quality is expected at the catalog resolution. | Prefer the catalog best resolution for quality. Treat a mismatch as a warning, not always a hard error, unless the user expects exact reproduction of README examples. |
| Output path has no suffix or an unsupported suffix. | `save_image_or_video` needs a filename extension to choose a writer. | Use `.mp4` for normal video output; `.gif` or `.webm` may be acceptable depending on installed video/imageio support. |
| `No module named imaginaire`, `No module named rcm`, `No module named modify_model`, or `No module named serve`. | Public source-layout scripts import helper packages from the inner source tree as top-level modules. | Add source-layout `PYTHONPATH=turbodiffusion` or use an equivalent installed/source layout where the helper packages are importable. |
| `attention_type=sagesla` fails during import or model creation. | Optional SpargeAttn/SageSLA dependencies are not installed or incompatible with the CUDA/PyTorch stack. | Try `--attention_type sla` or `--attention_type original` to isolate the issue; route installation/build debugging to `acceleration-backends`. |
| `attention_type=sla` or custom op path fails with CUDA/backend errors. | CUDA extension, custom ops, compiler, driver, or backend mismatch. | Route to `acceleration-backends`. One-shot command changes cannot repair a broken compiled backend. |
| CUDA out-of-memory during generation. | Model/checkpoint too large for the GPU or command uses high resolution, many samples, many frames, or unquantized weights. | Use quantized checkpoints with `--quant_linear`, lower `--resolution`, reduce `--num_samples`, reduce `--num_frames`, or move to a higher-memory GPU. Full generation cannot be validated by help-only checks. |
| Quality is poor for short or non-English prompts. | README notes current models were trained on long English prompts. | Expand the prompt in English with subject, scene, camera motion, lighting, temporal events, style, and constraints. |
| T2V 14B checkpoint load fails with `Wan2.1-1.3B`. | `--model` does not match the checkpoint family. | Use `--model Wan2.1-14B` for 14B T2V checkpoints and `--model Wan2.1-1.3B` for 1.3B checkpoints. |
| I2V command tries to use T2V checkpoint names. | Workflow mismatch. | I2V requires `TurboWan2.2-I2V-A14B` high and low checkpoints; T2V uses `TurboWan2.1-T2V` DiT checkpoints. |
| User asks to keep the model loaded for multiple prompts. | This is interactive serving, not one-shot inference. | Route to `interactive-serving`. |
| User asks to convert an rCM/SLA checkpoint into inference or quantized format. | This is checkpoint conversion/quantization, not one-shot inference. | Route to `training-and-checkpoints`; return here once an inference-ready checkpoint path exists. |

## Builder-specific escape hatches

The bundled builders use filename heuristics for safety. If checkpoint files were renamed and the heuristics are wrong, pass `--allow-flag-mismatch` after manually verifying the checkpoint format and model family.

Use `--check-files` only when rendering on the same machine where assets reside. Leave it off when preparing a command for another host or container.
