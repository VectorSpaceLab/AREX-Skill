# Troubleshooting Interfaces and Backends

Use this reference to turn environment symptoms into bounded next actions. Avoid automatic repair: many fixes require heavy CUDA wheels, native compilation, Docker changes, model downloads, or long-running GPU jobs.

## CUDA and GPU visibility

| Symptom | Likely cause | Safe diagnostic | Next action |
| --- | --- | --- | --- |
| `nvidia-smi` not found | NVIDIA driver tools absent from host/container path, CPU-only host, or container not given GPU access | Run the bundled environment checker; it only searches for the executable and queries visible GPUs when available | Do not run DreamCraft3D training. Ask user whether this host should have an NVIDIA GPU or route to a CUDA-capable machine/container. |
| `nvidia-smi` works but PyTorch reports no CUDA | CPU PyTorch wheel, incompatible CUDA wheel/driver, hidden device via `CUDA_VISIBLE_DEVICES`, or container runtime mismatch | Check `CUDA_VISIBLE_DEVICES`; inspect installed PyTorch wheel family without importing heavy training code when possible | Align PyTorch CUDA wheel with driver/toolkit. Do not use CPU import success as proof of DreamCraft3D runtime readiness. |
| `--gpu` seems ignored | `CUDA_VISIBLE_DEVICES` was set before calling `launch.py` | Inspect environment variables | `launch.py` gives precedence to existing `CUDA_VISIBLE_DEVICES`; clear or set it deliberately before using `--gpu`. |
| Out of memory during setup or early training | Defaults are high resolution and documented on 40GB A100; README requires 20GB+ VRAM for default path | Query GPU memory; check config overrides | Reduce `data.height`, `data.width`, `data.random_camera.height`, and `data.random_camera.width`; run one stage at a time; close Gradio or other GPU processes; consider narrower scope. |

## PyTorch and dependency version failures

| Symptom | Likely cause | Safe diagnostic | Next action |
| --- | --- | --- | --- |
| Import error for `pytorch_lightning`, `omegaconf`, `diffusers`, `transformers`, or `gradio` | Partial `requirements.txt` install or wrong environment active | Use the checker's package discovery; it uses metadata/spec probes, not imports of heavy ML stacks | Activate the intended environment or prepare a new one with user approval. Keep environment paths out of public skill notes. |
| Diffusers/Transformers API mismatch | Dependency drift beyond the repo recipe, especially `diffusers` newer than the bounded version | Check package versions via metadata | Prefer the repo's constrained family (`diffusers<=0.23.0`) for this checkout unless the user is intentionally porting the code. |
| `torch` import works but CUDA extensions fail | `nerfacc`, `tiny-cuda-nn`, or nvdiffrast built against a different CUDA/PyTorch/GPU architecture | Check CUDA wheel, driver, extension presence, and GPU architecture | Rebuild extensions only with explicit approval. Narrow `TORCH_CUDA_ARCH_LIST` / `TCNN_CUDA_ARCHITECTURES` to the target GPU when building. |

## nvdiffrast rasterizer issues

| Symptom | Likely cause | Next action |
| --- | --- | --- |
| OpenGL context errors in Docker or headless server | nvdiffrast `RasterizeGLContext` requires an OpenGL context not available in the container/server | Use CUDA contexts: `system.renderer.context_type=cuda` for training and `system.exporter.context_type=cuda` for mesh export. |
| Geometry/texture training reaches nvdiffrast import/context failure | Missing or broken nvdiffrast install, or unsupported context type | Confirm the active config has `system.renderer.context_type=cuda`; inspect extension installation; do not start another full run until fixed. |
| Mesh export fails even though geometry/texture training used CUDA context | Mesh exporter default `context_type` is `gl` | Add `system.exporter.context_type=cuda` to export commands, especially in Docker/headless environments. |

## nerfacc and tiny-cuda-nn build/runtime issues

| Symptom | Likely cause | Next action |
| --- | --- | --- |
| `nerfacc` or `tinycudann` missing | Requirements installed without the CUDA extension steps, or extension build failed silently | Treat full DreamCraft3D training as blocked. These are central to volume rendering/network encodings. |
| Native extension compile takes a long time | Broad architecture list builds kernels for many GPUs | If building is approved, set architecture env vars for the actual GPU generation instead of the broad default list. |
| Unsupported architecture or compiler/CUDA errors | CUDA toolkit, compiler, PyTorch wheel, and GPU architecture mismatch | Align the CUDA stack rather than retrying the same install command repeatedly. Capture versions and stop for user approval before mutating the environment. |

## Docker and NVIDIA container issues

| Symptom | Likely cause | Safe diagnostic | Next action |
| --- | --- | --- | --- |
| `docker: permission denied` | User not in `docker` group or daemon inaccessible | `docker --version` and `docker compose version` may work even when daemon access later fails | Ask user whether to use local policy (`sudo docker`, group membership, or admin setup). Do not change groups automatically. |
| `docker compose` command not found | Compose plugin not installed or older standalone Compose expected | Checker probes `docker compose version` | Have user install/enable Compose according to their Docker setup. |
| Container starts but no GPU visible | NVIDIA Container Toolkit missing/misconfigured, runtime not selected, or host driver unavailable | Inside a user-approved container, verify `nvidia-smi`; outside, check host `nvidia-smi` and Docker component presence | Fix host NVIDIA container integration before running DreamCraft3D. |
| `nvidia-container-cli: requirement error` | Container runtime requirement check rejects host/driver combination | The compose recipe sets `NVIDIA_DISABLE_REQUIRE=1` | Even if the variable bypasses the error, verify CUDA inside the container before training. |
| WSL2 Docker service issues | systemd not enabled or Docker Engine integration incomplete | Check WSL/Docker status outside this skill's runtime files | Ask user to enable systemd or configure Docker Desktop/Engine according to local policy. |

## Gradio launch and monitoring issues

| Symptom | Likely cause | Next action |
| --- | --- | --- |
| `python gradio_app.py launch` fails before UI appears | Missing `gradio`, `psutil`, `numpy`, `trimesh`, `threestudio` dependencies, or missing `configs/gradio/*.yaml` files | Run the checker. If `configs/gradio/` is absent, route to direct DreamCraft3D stage commands instead of the generic UI. |
| Port already in use | Another process is bound to the default 7860 port | Use `--port <free-port>` after identifying a free port. |
| UI accessible from unintended hosts | `--listen` binds to `0.0.0.0` | Prefer localhost unless the user explicitly needs remote access and has network controls in place. |
| Status stays at `Setting up everything ...` | `progress` file not created yet, dependency/model initialization is slow, or training crashed before callback setup | Inspect `outputs-gradio/.../logs` and process status. Missing logs during early setup usually means initialization failed before file handlers attached. |
| Watcher kills a still-needed job | UI stopped refreshing `alive`, `alive-timeout` too low, browser disconnected, or wrong PID/trial directory | Increase timeout only when the user understands the job will continue after fewer UI refreshes. Never point watcher at unrelated PIDs. |
| Stop button leaves partial outputs | Stop sends `SIGKILL` to the training PID | Treat checkpoints/logs as potentially incomplete. Verify the latest checkpoint before resuming or passing it to later stages. |
| `outputs-gradio` grows unexpectedly | Every Gradio run creates a separate trial directory with logs, media, checkpoints, and possible exports | Summarize and clean only with user approval. Do not delete outputs automatically. |

## Model artifact triage at this interface layer

The environment checker can optionally verify local file artifacts that are referenced by configs or preprocessing scripts, such as Zero123 checkpoints/config and DMTet grids. It cannot prove Hugging Face model cache availability for DeepFloyd IF or Stable Diffusion without importing/downloading model stacks. If a run is blocked on model files, route to the model-artifact planning guidance rather than starting training again.
