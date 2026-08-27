# Deployment troubleshooting

Use this reference to turn common launch failures into concrete checks. Prefer the smallest failing surface: validate the static `--load` plan, then check local files, then dependencies, then credentials, then CUDA/runtime.

## `model_zoo` missing or incomplete

Symptoms:

- `FileNotFoundError` under `model_zoo/...`.
- First launch starts a large download or hangs in an offline environment.
- A tab renders, but first model call fails when weights are needed.

Actions:

1. Identify which direct `--load` class needs the missing asset using `references/model-zoo.md`.
2. Confirm the app is started from a working directory where `model_zoo/` is visible.
3. Pre-stage the required weights rather than relying on first-run downloads in production.
4. For Docker, confirm the host model directory is mounted to the container's expected `model_zoo/` path and is not still a placeholder volume.

## Husky/LLaMA conversion is partial or bad

Symptoms:

- `model_zoo/llama_7B_hf does not appear to have a file named config.json`.
- `No such file or directory: model_zoo/llama/7B/params.json`.
- `HuskyVQA` load fails after a previous interrupted download or conversion.

Actions:

1. Treat `model_zoo/husky-7b-delta-v0_01` as a delta, not the final Husky model.
2. Confirm a licensed LLaMA 7B base exists under `model_zoo/llama/7B` and includes `params.json` and the expected shard/tokenizer files.
3. Confirm `model_zoo/llama_7B_hf` is a completed converted directory with `config.json`.
4. If conversion was interrupted, remove only the incomplete generated directories after preserving any valid licensed base files, then rerun conversion with a valid LLaMA source.
5. Do not publish or embed presigned URLs, copied LLaMA weights, or private credential values.

## No OpenAI key or rejected key

Symptoms:

- UI keeps the login controls visible and reports an incorrect key.
- Chat/tool orchestration fails even though visual models loaded.
- TikTok-style generation fails while video caption/action pieces work.

Actions:

1. For normal use, supply a valid key via the UI password field or a secure runtime secret.
2. Use `--debug` only for local debugging of the UI gate; it is not proof that OpenAI-backed calls will work.
3. Verify the key can reach the configured API endpoint from the same environment.
4. Avoid putting real keys in command lines, compose files, committed configuration, or skill files.

## `OPENAI_API_BASE` problems

Symptoms:

- API connection errors, proxy errors, or unexpected endpoint behavior.
- Works in one shell but not under Docker/system service.

Actions:

1. Set `OPENAI_API_BASE` before starting the Python process; the app reads it during import.
2. Keep the value available inside containers or service managers through their environment/secret mechanism.
3. If a proxy or compatible endpoint is used, test a minimal API request outside the app before blaming model tools.
4. Unset `OPENAI_API_BASE` to return to the default OpenAI endpoint behavior.

## HTTPS certificate missing

Symptoms:

- `--https` launch fails with missing `certificate/cert.pem` or `certificate/key.pem`.
- Browser microphone or voice input is unavailable on a remote service.

Actions:

1. Create `certificate/cert.pem` and `certificate/key.pem` under the application working directory.
2. Use the certificate command in `references/deployment-recipes.md` for a self-signed local certificate.
3. For Docker, mount the host certificate directory into the container at the expected `certificate/` location.
4. Warn users that browsers may show self-signed certificate warnings.

## CUDA, device, or VRAM mismatch

Symptoms:

- `torch.cuda.is_available()` is false, `cuda:0` cannot be opened, or CUDA kernels fail.
- Startup succeeds for small plans but fails for Husky/SAM/full multimodal plans.
- `-e` was used but out-of-memory still occurs.

Actions:

1. Match every `--load` device to an actual visible GPU, usually `cuda:0`.
2. Use `-e` to reduce memory residency, especially for full-feature or DragGAN-only recipes, but do not call it CPU mode.
3. Remember that the app initializes a speech model on `cuda:0` at startup, independent of the chosen `--load` list.
4. Start with the smallest load list, then add classes incrementally after the previous set initializes.
5. For Docker, check host driver, NVIDIA container toolkit, and whether the container can see the GPU.

## Docker placeholder volumes

Symptoms:

- Compose starts but the container cannot find `model_zoo/` or `certificate/`.
- Compose file contains placeholder strings such as `<host-model-zoo>` or old `/path/to/...` values.
- HTTPS or checkpoint failures appear only inside the container.

Actions:

1. Replace every placeholder host volume with a real host directory.
2. Mount model and certificate directories read-only when possible.
3. Confirm container paths match the app's relative expectations.
4. Keep secrets out of the image and compose file; inject them at runtime.

## detectron2 and GRiT pitfalls

Symptoms:

- Dense captioning fails with detectron2 import/build errors.
- Build logs mention missing CUDA compiler, unsupported GCC/G++, or CPU-only detectron2.
- `DenseCaption` works on one machine but not another.

Actions:

1. Only require detectron2/GRiT when loading `DenseCaption` or workflows that depend on dense captions.
2. Match PyTorch, CUDA toolkit, compiler, and detectron2 build expectations.
3. If errors mention missing CUDA compiler support, inspect CUDA visibility and compiler availability before reinstalling the whole environment.
4. Avoid treating a basic DragGAN or Husky/SAM launch as proof that GRiT/detectron2 is ready.

## OpenCV dependency conflicts

Symptoms:

- Import errors involving `cv2`, GUI libraries, or headless display dependencies.
- Docker image has multiple OpenCV packages installed and conflicting.
- Image/video preprocessing fails before model inference.

Actions:

1. Use one coherent OpenCV variant for the deployment environment.
2. Prefer a headless variant for server/container use unless GUI features are explicitly needed.
3. If broad requirement installation pulled conflicting OpenCV packages, remove duplicates and reinstall the selected variant intentionally.
4. Retest the smallest affected capability after fixing OpenCV; do not rerun full multimodal launch first.

## `-e` / e-mode expectations

Symptoms:

- User expects `-e` to run everything on CPU.
- Startup or first call still allocates CUDA memory.
- Model transfer overhead makes first calls slower.

Actions:

1. Explain that e-mode is memory-saving/offload behavior for wrappers that implement it.
2. It does not remove checkpoint requirements, CUDA requirements, model-cache requirements, or OpenAI requirements.
3. It can reduce peak persistent VRAM but may increase latency because models move between CPU and GPU around calls.
4. If e-mode is insufficient, reduce the `--load` list and `--tab` set before adding more memory-heavy models.
