# Deployment troubleshooting

This reference covers deployment-specific failures for the Streamlit, Gradio,
Docker/Gitpod, and Cog surfaces. For generation/API-level issues, use the sibling
[`generation` sub-skill](../../generation/SKILL.md).

## Fast triage checklist

1. Confirm CUDA is available and the runtime is using a GPU build of PyTorch.
2. Confirm the required model/checkpoint cache exists or downloads are approved.
3. Confirm the demo surface you are launching matches the command you are using.
4. Check whether the failure is due to source-demo side effects at import/startup.
5. If background removal is enabled, confirm `rembg`, `segment_anything`, and the
   SAM checkpoint are present.

## Common failures and responses

### 1) `app.py` import side effects or accidental model downloads

**Symptom:** Simply importing or executing the Streamlit app causes dependency
checks, pipeline loading, SAM initialization, or network access.

**Cause:** The source Streamlit file is an application script, not a clean module.
It performs work at top level.

**Response:**
- Do not use `import app` as a smoke test.
- Launch the app with the intended Streamlit command instead.
- Prefer the bundled launcher templates when you need a safe, importable entry
  point.
- If you only need to inspect UI behavior, read the bundled references instead of
  executing the source file.

### 2) SAM checkpoint missing

**Symptom:** Background removal fails, or the demo hangs while trying to locate
`sam_vit_h_4b8939.pth`.

**Cause:** The source demos expect the SAM ViT-H checkpoint to be present in a
local temporary cache path or downloaded at setup time.

**Response:**
- Use the build/setup path that explicitly fetches the checkpoint when network
  access is allowed.
- If network is unavailable, pre-stage the checkpoint before launch.
- If background removal is not required, disable the input/output background
  options and skip the SAM-dependent path.

### 3) `rembg` or ONNX runtime errors

**Symptom:** Import errors, `onnxruntime` complaints, or failures only when
background removal is enabled.

**Cause:** `rembg` pulls in ONNX runtime and model files on first use.

**Response:**
- Install the pinned demo dependencies from the repo requirements.
- Confirm the runtime can create the rembg session and download/cache its model.
- If the deployment does not need alpha matting or background removal, turn those
  options off and keep the demo on the core generation path.

### 4) Streamlit launch confusion

**Symptom:** `python app.py` does not present the expected web UI, or the port is
not reachable.

**Cause:** The source Streamlit file is meant to be run by Streamlit, not as a
plain Python script. The Gitpod evidence also uses a lightweight bootstrap rather
than a polished launch command.

**Response:**
- Use `streamlit run` for the source-style app.
- Pass explicit host/port flags in containerized environments.
- Remember that the source app loads the model at startup, so a slow or blocked
  start may actually be a cache/download issue rather than a port issue.

### 5) Gradio share, queue, or port problems

**Symptom:** The Gradio demo launches but the share tunnel never appears, the app
is stuck in queue, or the chosen port is busy.

**Cause:** The source Gradio app launches with sharing and queuing enabled.
Single-GPU execution serializes requests, and the first run may take time to load
weights.

**Response:**
- Re-run with a known-free port.
- Disable sharing if the environment is offline or if public tunnels are blocked.
- Expect a long first request if the pipeline is loading from cache or fetching
  artifacts.
- For controlled environments, use the bundled launcher template with explicit
  `--host`, `--port`, and `--share` settings.

### 6) Cog weights path mismatch

**Symptom:** The predictor cannot find weights even though the archive was
extracted.

**Cause:** The source predictor assumed a fixed container-local cache path and a
specific archive layout.

**Response:**
- Use the bundled Cog template, which makes the weights directory configurable.
- Set the weights path through environment variables rather than relying on a
  hard-coded absolute path.
- Verify the extracted directory contains the Diffusers model files that the
  predictor expects.

### 7) `pget` missing or archive download fails

**Symptom:** Cog setup errors before the model is ready, or the download step
fails with a missing command.

**Cause:** The source Cog build depends on `pget` for the weight archive.

**Response:**
- Install `pget` in the build image when downloads are approved.
- If downloads are disallowed, pre-populate the weights directory instead.
- In the bundled template, disable automatic download and point the predictor at
  a prepared local weights directory.

### 8) CUDA or VRAM problems

**Symptom:** The demo crashes on `cuda:0`, hangs during generation, or runs out of
memory.

**Cause:** The source demos move the diffusion pipeline to CUDA. The README notes
roughly 5 GB VRAM for the base flow and around 5.7 GB for the depth flow.
Background-removal extras increase overhead.

**Response:**
- Confirm a CUDA-enabled PyTorch build and a visible GPU.
- Reduce concurrent requests in the serving layer.
- Lower the workload by disabling background removal, or stop and use a larger
  GPU if the deployment target cannot meet the memory requirement.
- Treat CPU-only execution as a non-goal for the production demo path.

### 9) Missing `segment_anything`

**Symptom:** The demo crashes only when input or output background removal is
enabled.

**Cause:** The full source demos depend on SAM for mask refinement.

**Response:**
- Install `segment_anything` and ensure the SAM checkpoint is present.
- If the deployment only needs the core multiview generator, disable background
  removal and keep the UI minimal.
- The bundled Gradio launcher deliberately omits this dependency by default.

### 10) `download_checkpoints.py` or `util/download_weights.py` confusion

**Symptom:** A future agent tries to use one of the repository helper scripts as a
runtime launcher.

**Cause:** These files model cache preparation, not the actual deployable UI/API
entry points.

**Response:**
- Treat `download_checkpoints.py` as build-time/reference-only.
- Treat `util/download_weights.py` as excluded/buggy until repaired and
  validated.
- Use the bundled launcher/predictor templates for future deployment work.

## Helpful environment messages to surface in code or docs

- "CUDA is required for the deployment path and is not available in this runtime."
- "The requested model is not in local cache; downloads are disabled."
- "SAM background removal is enabled but the checkpoint is missing."
- "rembg/onnxruntime is missing; disable background removal or install the
  dependency set."
- "pget is unavailable; pre-stage the Cog weights archive or install pget in the
  build image."
- "The source app should be launched with Streamlit/Gradio, not via plain import."

## When to stop and ask the user

Stop instead of guessing when:

- the runtime has no CUDA GPU and the task is a real deployment;
- the user has not approved downloads for Hugging Face, SAM, rembg, or Cog
  weight archives;
- the deployment target is a commercial product and the user has not addressed
  the CC-BY-NC model-weight license.
