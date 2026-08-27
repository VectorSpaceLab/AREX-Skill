# InfiniteYou Troubleshooting

## Purpose

Use this root guide for cross-cutting failures that can affect CLI inference, the self-contained Gradio demo, or pipeline customization. For workflow-specific failures, continue into the nearest sub-skill troubleshooting guide.

## Fast triage

1. Run the safe bundled-runtime environment checker:
   ```bash
   python scripts/check_infinite_you_environment.py --require-cuda
   ```
2. If model paths are involved, run the model-layout checker:
   ```bash
   python sub-skills/demo-and-model-setup/scripts/check_model_layout.py --model-dir models/InfiniteYou --base-model-path models/FLUX.1-dev
   ```
3. If a generation command is involved, run local-inference preflight:
   ```bash
   python sub-skills/local-inference/scripts/run_infinite_you_flux.py --check-only --id-image path/to/id.jpg --model-dir models/InfiniteYou --base-model-path models/FLUX.1-dev
   ```
4. If implementation APIs drifted, run the bundled pipeline signature helper:
   ```bash
   python sub-skills/pipeline-internals/scripts/inspect_pipeline_signatures.py
   ```

## Install/import failures

Symptoms:

- Import errors for `diffusers`, `transformers`, `insightface`, `facexlib`, `onnxruntime`, `optimum.quanto`, `cv2`, `pillow_heif`, or `pillow_avif`.
- `pip check` reports incompatible pins.
- The checker says the bundled runtime is incomplete.

Likely causes and recovery:

- Install the dependency pins from `runtime/requirements.txt` in an isolated environment.
- Confirm `runtime/pipelines/pipeline_infu_flux.py`, `runtime/pipelines/pipeline_flux_infusenet.py`, and `runtime/pipelines/resampler.py` exist in the generated skill directory.
- Avoid mixing unrelated torch/diffusers/transformers versions unless you are intentionally porting the code.
- For API drift, use the signature helper before editing code.
- Use `--implementation-root` only when intentionally comparing a refreshed source tree; it is not needed for normal generated-skill operation.

## CUDA/backend failures

Symptoms:

- `torch.cuda.is_available()` is false.
- Invalid CUDA device ordinal.
- `.cuda()` or `device='cuda'` errors.
- CUDA out of memory.

Recovery:

- Use a CUDA-capable torch build and visible NVIDIA GPU.
- Select a valid `--cuda-device`.
- Start with `--cpu-offload --quantize-8bit` for lower VRAM.
- Remember that CPU offload still requires CUDA.
- For true CPU-only execution, plan source-code changes in the pipeline-internals route.

## Model access and layout failures

Symptoms:

- Missing `InfuseNetModel` or `image_proj_model.bin`.
- Missing `supports/insightface`.
- Errors mention `black-forest-labs/FLUX.1-dev`, 401, 403, license agreement, or authentication.
- The runtime refuses to start because `--allow-downloads` was not provided.

Recovery:

- Validate local InfiniteYou and FLUX model paths before launching heavy workflows.
- Keep local `models/InfiniteYou` and `models/FLUX.1-dev` paths as the default no-download path.
- Accept/authenticate gated models only when the user's policy allows it, then pass `--allow-downloads` if relying on remote model ids or fallback downloads.
- Keep InfiniteYou weights, InsightFace support files, base FLUX weights, and optional LoRAs conceptually separate.

## Optional dependency and LoRA failures

Symptoms:

- Enabling Realism or Anti-blur fails with a missing file.
- Adapter APIs such as `delete_adapters`, `load_lora_weights`, or `set_adapters` fail.

Recovery:

- First verify base generation without LoRA flags.
- Check optional LoRA paths only when the user requests them.
- Pin Diffusers to the repository version before diagnosing adapter API drift.
- Route adapter-code changes to the pipeline-internals sub-skill.

## Gradio demo failures

Symptoms:

- The self-contained launcher preflight fails.
- The server is unreachable.
- Model loading consumes GPU memory before the first manual request.
- Switching model variants causes slow reloads or OOM.

Recovery:

- Run `sub-skills/demo-and-model-setup/scripts/launch_infinite_you_gradio.py --check-only` before launching.
- Validate model layout first.
- Keep the default localhost bind unless external access is intended.
- Use a single model version per session on tight VRAM.
- Prefer the local-inference CLI wrapper with `--cpu-offload --quantize-8bit` when the demo UI is too memory-heavy.

## Safety and policy stops

Stop and ask for explicit user approval before:

- Downloading gated, licensed, or non-commercial-use model artifacts.
- Passing `--allow-downloads` to a generation/demo command that may fetch model files.
- Exposing a local Gradio server beyond localhost or enabling `--share`.
- Running a heavy generation job on shared GPUs when resource policy is unclear.
- Using identity images without confirming consent and responsible-use constraints.

See [safety-and-licenses.md](safety-and-licenses.md) for the public license and responsible-use baseline.
