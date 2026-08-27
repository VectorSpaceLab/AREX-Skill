# Local Inference Troubleshooting

## Purpose

Use this guide when a local InfiniteYou-FLUX generation command or API call fails. Start with `scripts/run_infinite_you_flux.py --check-only` so you can separate setup problems from model execution problems.

## `No face detected in the input ID image`

Likely causes:

- The identity image has no visible face, the face is too small, heavily occluded, blurred, or profile-only.
- Multiple people are present and the largest face is not the intended identity.
- The image file did not load as RGB or is corrupted.

Recovery:

1. Use a clearer crop with one large face.
2. Confirm the file path with `--check-only`.
3. If multiple faces are unavoidable, crop the intended face because the pipeline selects the largest detected face.
4. If the same image fails repeatedly, check InsightFace support model layout in the demo/model setup route.

## `No face detected in the control image`

Likely causes:

- A control image was supplied but it does not contain a detectable face.
- The user expected pose control from a non-face pose image; this pipeline extracts five facial keypoints, not general body pose.

Recovery:

1. Distinguish identity and control images in the command.
2. Use a face-visible control image.
3. Omit `--control-image` if no face-pose guidance is required; the pipeline will use a black control image.

## CUDA unavailable

Symptoms:

- `torch.cuda.is_available()` is false.
- Errors mention missing CUDA runtime, no CUDA-capable device, or invalid device ordinal.

Likely causes:

- CPU-only torch or missing GPU passthrough.
- Driver/runtime mismatch.
- Wrong `--cuda-device` index.
- Attempting CPU-only generation; the repository code hard-codes CUDA for generation.

Recovery:

1. Run `--check-only` and inspect the CUDA section.
2. Verify the selected environment installed a CUDA-capable torch build.
3. Use a visible device index.
4. Do not expect `--cpu-offload` to work without CUDA; it only reduces peak VRAM.

## CUDA out of memory

The README reports about 43 GB peak VRAM for full bf16 inference, 30 GB with `--cpu-offload`, 24 GB with `--quantize-8bit`, and 16 GB with both.

Recovery order:

1. Add both `--cpu-offload` and `--quantize-8bit`.
2. Use a freer or larger GPU with `--cuda-device`.
3. Reduce `--width`, `--height`, or `--num-steps` if acceptable.
4. Avoid enabling optional LoRAs while diagnosing memory.
5. If model switching in a long process leaks memory, restart the process to release CUDA allocations.

## Missing or inaccessible model files

Symptoms:

- Errors mention `FLUX.1-dev`, `from_pretrained`, missing `InfuseNetModel`, missing `image_proj_model.bin`, 401/403, or Hugging Face authentication.

Likely causes:

- `--base-model-path` points to gated `black-forest-labs/FLUX.1-dev` without accepted license/authentication.
- `--model-dir` does not contain the InfiniteYou release layout.
- The upstream code tried to download weights into a default local cache but network/authentication failed.

Recovery:

1. Use the demo/model setup route's `check_model_layout.py` before a heavy run.
2. For gated FLUX, accept the license and authenticate, or point `--base-model-path` to a local FLUX directory.
3. For InfiniteYou, ensure the selected variant contains both `InfuseNetModel` and `image_proj_model.bin`.
4. Do not embed tokens in commands, scripts, or skill files.

## Invalid model version or version mismatch

Symptoms:

- Assertion or value error says only `aes_stage2` or `sim_stage1` is supported.
- Model path exists for one variant but the command asks for the other.

Recovery:

- Use `--model-version aes_stage2` for default alignment/aesthetics.
- Use `--model-version sim_stage1` for higher identity similarity.
- Keep `--infu-flux-version v1.0`; this repository snapshot does not expose other versions.

## LoRA file missing

Symptoms:

- Errors occur after enabling Realism or Anti-blur LoRA.
- Paths under `supports/optional_loras` are missing.

Recovery:

1. Retry without LoRA flags to confirm base generation works.
2. Validate optional LoRA files with the model-layout checker and `--require-optional-loras`.
3. Use Realism alone first; optional LoRAs are not required for paper-style generation.

## Prompt alignment or identity quality is poor

Likely causes:

- `aes_stage2` favors aesthetics/alignment while `sim_stage1` favors identity similarity.
- InfuseNet starts too early/strongly or the prompt lacks explicit person descriptors.

Recovery:

- If identity similarity is too low, try `--model-version sim_stage1`.
- If `sim_stage1` over-constrains the face, try `--infusenet-guidance-start 0.1`.
- If still too identity-dominant, try `--infusenet-conditioning-scale 0.9`.
- Keep the seed fixed while comparing settings.

## Output path or filename problems

Symptoms:

- No PNG appears.
- Output directory parent is missing or unwritable.
- Prompt text creates awkward filenames.

Recovery:

1. Run `--check-only` and inspect the output directory parent.
2. Use a short `--out-results-dir` path with write permission.
3. Keep prompt text reasonable; the helper truncates and sanitizes the prompt in the filename.

## Flag typo: `guideance_scale`

The README explanation contains a typo (`guideance_scale`). The actual parser flag is `--guidance-scale` in the bundled helper and `--guidance_scale` in the original CLI surface. Use `guidance_scale` in Python API calls.
