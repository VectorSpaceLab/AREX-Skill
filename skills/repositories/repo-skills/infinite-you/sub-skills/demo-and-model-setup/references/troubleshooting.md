# Troubleshooting

Use this guide when the self-contained demo launcher or the model-layout validator reports setup problems.

## Quick first step

Run the bundled validators before launching a server or changing code:

```bash
python scripts/check_model_layout.py --model-dir models/InfiniteYou --base-model-path models/FLUX.1-dev
python scripts/launch_infinite_you_gradio.py --check-only --model-dir models/InfiniteYou --base-model-path models/FLUX.1-dev
```

Both commands avoid model downloads and server launch.

## HF access for FLUX.1-dev

**Symptom**: full launch fails while resolving `black-forest-labs/FLUX.1-dev`, or a download attempt reports that the model cannot be accessed.

**Likely cause**: the model agreement has not been accepted, the Hugging Face token is missing, or network access is unavailable.

**Fix**:

- accept the FLUX model agreement if you plan to use the hosted repo id
- authenticate with a valid Hugging Face token outside generated skill files
- or point the runtime at a local FLUX directory instead of the gated repo id
- use `--allow-downloads` only after the user approves network/model-license consequences

The bundled validators do not download the base model. They only warn when a gated repo id is used.

## Failed or blocked model download

**Symptom**: the launcher refuses to start because paths are non-local or missing, or an explicitly allowed download fails.

**Likely cause**: missing local model tree, authentication, connectivity, or an incorrect destination path.

**Fix**:

- prefer seeding local model files first
- validate local paths with `check_model_layout.py`
- pass `--allow-downloads` only if remote/fallback downloads are intended
- verify that any download destination is writable

## Wrong `model_dir` or `base_model_path`

**Symptom**: the demo cannot find `InfuseNetModel`, `image_proj_model.bin`, InsightFace support files, or the FLUX base-model subfolders.

**Likely cause**: the runtime is pointed at the wrong directory.

**Fix**:

- confirm that `model_dir` contains `infu_flux_v1.0/aes_stage2`, `infu_flux_v1.0/sim_stage1`, and `supports/insightface`
- confirm that the base model path is a valid local FLUX directory unless downloads are explicitly allowed
- use the bundled validator with the exact paths passed to the launcher

## Missing `supports/insightface`

**Symptom**: face analysis setup fails before generation starts.

**Likely cause**: the InsightFace support tree is absent or incomplete.

**Fix**: restore the `supports/insightface` directory under the InfiniteYou model root before launching the demo.

## Missing optional LoRAs

**Symptom**: enabling realism or anti-blur raises a file-not-found error.

**Likely cause**: the optional LoRA files are not present.

**Fix**:

- leave both LoRA toggles off, or
- place `flux_realism_lora.safetensors` and `flux_anti_blur_lora.safetensors` under `supports/optional_loras`

If you want the validator to treat those files as required, pass `--require-optional-loras` to `check_model_layout.py`.

## Gradio server binding

**Symptom**: the UI starts but you cannot reach it, or launch fails because the port is busy.

**Likely cause**: the process is bound to localhost, the port is already occupied, or the environment blocks the chosen bind.

**Fix**:

- keep the default localhost bind for private local use
- choose a different host or port only when you intentionally want external access
- use `--share` only after explicit approval
- stop the process that already owns the port

## Model loading and startup GPU work

**Symptom**: startup is slow, or GPU memory is used before the first manual request.

**Likely cause**: full launch constructs a CUDA model pipeline before generation can occur. The generated launcher avoids example caching, but it still loads large models.

**Fix**:

- expect model-load GPU memory pressure at first generation/model switch
- free other GPU jobs before launching
- use one model version per session on tight VRAM
- prefer the CLI wrapper with `--cpu-offload --quantize-8bit` if the demo is too memory-heavy

## Model switching memory pressure

**Symptom**: switching between `aes_stage2` and `sim_stage1` is slow or causes an out-of-memory error.

**Likely cause**: the launcher clears adapters and CUDA cache, but the GPU still needs enough free memory to rebuild the new pipeline.

**Fix**:

- use a single model version per session when VRAM is tight
- close other GPU jobs before switching
- keep output size near the default 864x1152 when debugging memory issues

## Width and height defaults

**Symptom**: larger image sizes make the demo unstable or unexpectedly slow.

**Likely cause**: higher canvas sizes increase memory use quickly.

**Fix**:

- start with the default width and height
- raise them gradually only after the default run is stable
- if the machine is small, prefer reducing size before changing other settings
