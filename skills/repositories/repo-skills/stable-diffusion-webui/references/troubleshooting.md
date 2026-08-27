# Cross-Cutting Troubleshooting

Use this reference when the symptom spans multiple WebUI surfaces. For workflow-specific errors, follow the nearest sub-skill troubleshooting reference.

## Install Or Import Failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Python version rejected | WebUI expects a compatible Python family and launcher checks it early | Use the launcher-supported Python version or only bypass with `--skip-python-version-check` after confirming dependency compatibility. |
| Torch or CUDA import/runtime error | Wheel/backend mismatch, unsupported GPU, wrong driver, or CPU-only install | Check torch/CUDA versions before WebUI launch; avoid `--skip-torch-cuda-test` unless intentionally running CPU or diagnosing. |
| xformers fails or slows startup | Optional wheel mismatch or unsupported platform | Remove `--xformers` or use `--reinstall-xformers` only when the wheel is known compatible. |
| Packages install unexpectedly at launch | Launcher environment preparation is active | Use `--skip-install` or `--skip-prepare-environment` only when dependencies are already installed and the user accepts missing-install risk. |

## Backend And Model State

| Symptom | Likely cause | Action |
| --- | --- | --- |
| No checkpoint found | Empty checkpoint directory, wrong `--data-dir`/`--models-dir`/`--ckpt-dir`, or startup download disabled | Use `assets-and-models` to validate layout, then pass an explicit `--ckpt` or correct directory flags. |
| Model loads but generation fails | VAE/config mismatch, unsupported precision, insufficient VRAM, or incompatible sampler/backend | Try `--no-half`, `--no-half-vae`, `--upcast-sampling`, lower resolution/batch, or route model layout checks to `assets-and-models`. |
| Lora or embedding not visible | Wrong asset directory, unsupported suffix, stale extra-network cache, or incompatible network type | Refresh the relevant asset list and inspect extra-network guidance in `assets-and-models`. |
| Upscaler or face restoration unavailable | Optional model weights/dependencies absent | Use Extras/postprocessing guidance and avoid triggering downloads unless approved. |

## Server, API, And Security

| Symptom | Likely cause | Action |
| --- | --- | --- |
| API route 404 | Server not launched with `--api`/`--nowebui`, wrong base URL, or reverse-proxy subpath omitted | Confirm launch mode in `launch-and-config`, then probe `/sdapi/v1/cmd-flags`. |
| API 401 | `--api-auth` enabled or auth header missing | Add HTTP Basic auth for API calls; `--gradio-auth` and `--api-auth` are separate. |
| Browser/API blocked by CORS | Origin not included or regex wrong | Use narrow `--cors-allow-origins` or `--cors-allow-origins-regex`; avoid wildcard exposure on trusted networks. |
| Server exposed unexpectedly | `--listen`, `--server-name 0.0.0.0`, `--share`, or `--ngrok` enabled | Add auth/TLS/network controls or bind locally. |
| Stop/restart routes missing | Server was not launched with stop endpoints enabled | Do not assume `/server-stop`, `/server-restart`, or `/server-kill` exist; enable only for trusted automation. |

## Extension And Script Failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Script missing from UI/API | File not under `scripts/`, class does not inherit expected base, bad `show()`, import error, or extension disabled | Use `extension-scripting` troubleshooting and temporarily disable user extensions to isolate. |
| Always-on API args fail | Script title or argument order does not match live `/script-info` | Fetch `/sdapi/v1/script-info` and adjust `alwayson_scripts` payload shape. |
| Callback runs in wrong order | `metadata.ini` ordering or extension load order conflict | Inspect callback ordering guidance and add explicit before/after constraints. |
| Arbitrary code risk | `--allow-code` or custom-code script enabled | Disable unless the environment is trusted and the user explicitly wants code execution. |

## Long-Running Workflows

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Training appears stuck | Long step count, slow backend, missing preview/log path, or model state issue | Validate the training plan, reduce steps, confirm output/log directories, and monitor progress endpoints. |
| Preprocessing overwrites or duplicates files | Output directory equals source, operation order unclear, or flipped/cropped outputs collide | Validate a preprocessing plan with the bundled training/postprocessing validator first. |
| Extras request times out | Large images, slow upscaler, face-restorer model load, or batch size too high | Start with one small image and one upscaler; add face restoration and secondary upscaler only after baseline success. |
