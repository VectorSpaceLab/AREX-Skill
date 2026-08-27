# DiscoArt Cross-Cutting Troubleshooting

## Purpose

Use this reference before or alongside the focused sub-skills when DiscoArt fails at install/import, CUDA/backend discovery, model cache/download, config loading, output persistence, or service setup.

For workflow-specific failures, continue to:

- `../sub-skills/artwork-generation/references/troubleshooting.md` for generation, model, output, DocArray, and `go_big()` failures.
- `../sub-skills/configuration-and-prompts/references/troubleshooting.md` for config keys, schedule strings, prompt schema, and CLIP guidance errors.
- `../sub-skills/cli-and-serving/references/troubleshooting.md` for CLI, Jina Flow, endpoint, Docker, and server issues.

## Start with the bundled environment check

```bash
python scripts/check_discoart_environment.py --check-cuda
```

Useful variants:

```bash
python scripts/check_discoart_environment.py --json
python scripts/check_discoart_environment.py --check-cuda --allocate-cuda
```

This does not run diffusion, launch services, download models, or create output images.

## Install/import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'discoart'` | Package is not installed in the active Python. | Install `discoart` into the runtime environment, then rerun `python -c "import discoart; print(discoart.__version__)"`. |
| `ModuleNotFoundError: No module named 'docarray'`, `jina`, `clip`, `open_clip`, `lpips`, or `guided_diffusion` | Runtime dependencies are missing or a partial install was used. | Reinstall the package with dependencies instead of copying the source package only. |
| `ModuleNotFoundError: No module named 'pkg_resources'` | Very new `setuptools` no longer provides the legacy `pkg_resources` import used by DiscoArt. | Pin/set `setuptools<81` or use a package environment where `pkg_resources` is still available. |
| Import logs an error about latest version or remote model list | DiscoArt starts short network checks for PyPI/model-list updates unless disabled. | Set `DISCOART_DISABLE_REMOTE_MODELS=1` to disable remote model-list lookup. A transient version-check timeout is usually non-fatal. |
| Dependency resolver wants very old torch pins from test extras | The `test` extra contains historical torch/torchvision pins for old CI. | For user/runtime skill tasks, install base runtime dependencies and a CUDA-compatible torch stack instead of all test extras. |

## CUDA and backend failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `torch.cuda.is_available()` is false | CPU-only torch, no visible NVIDIA device, driver/container passthrough issue, or incompatible wheel. | Verify `nvidia-smi`, install a CUDA-capable PyTorch build compatible with the driver, and ensure `CUDA_VISIBLE_DEVICES` allows at least one GPU. |
| CPU warning says DiscoArt is running on CPU | `get_device()` fell back to CPU. | Treat this as config/inspection only unless the user accepts extremely slow generation; use a GPU runtime for real artwork generation. |
| CUDA OOM or abrupt process exit | Large `width_height`, too many CLIP models, high `batch_size`, high `n_batches`, many cuts, or multiple concurrent runs. | Start with `n_batches=1`, `batch_size=1`, smaller multiples-of-64 dimensions, fewer `clip_models`, lower `cutn_batches`, and avoid floating service overload. |
| GPU works in Python but not Docker | Container lacks GPU runtime or correct mounts/env. | Run containers with GPU access (`--gpus all` or platform equivalent), mount output/cache dirs, and pass `DISCOART_CACHE_DIR`/`DISCOART_OUTPUT_DIR`. |

## Model cache and download failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| First generation stalls before denoising | Downloading diffusion, secondary, or CLIP weights. | Confirm network/cache permissions, set `DISCOART_CACHE_DIR` to persistent storage, and expect first-run latency. |
| Repeated model download despite cache | Cache path changes between runs/containers or file SHA check fails. | Use a stable `DISCOART_CACHE_DIR`; if using Docker, bind-mount the cache. Only disable SHA checks for trusted cache files. |
| Remote model-list fetch fails | Network blocked or remote URL unavailable. | Set `DISCOART_DISABLE_REMOTE_MODELS=1` to use the packaged model list. |
| Custom diffusion model path fails | File path is wrong or `diffusion_model_config` does not match the checkpoint. | Use an absolute or runtime-valid path and provide a matching `diffusion_model_config`; otherwise use a packaged model prefix. |

## Output and recovery failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Cannot find output images | Unknown `name_docarray`, current directory changed, or `DISCOART_OUTPUT_DIR` differs. | Use explicit `name_docarray`; inspect `<DISCOART_OUTPUT_DIR or .>/<name_docarray>/`. |
| `da.protobuf.lz4` missing | Run failed before first persistence, output disabled/misplaced, or process was killed. | Check logs and output dir; lower runtime risk settings; rerun with `image_output=True` and stable output/cache dirs. |
| `DocumentArray.pull(name)` fails | Cloud backup disabled, no network, incorrect name, or remote data expired/unavailable. | Prefer local `da.protobuf.lz4` when available; use cloud pull only as best-effort recovery. |
| No final result summary appears | Headless mode or `DISCOART_DISABLE_RESULT_SUMMARY`/`DISCOART_DISABLE_IPYTHON` was set. | This is often intentional for CLI/service environments; inspect returned `DocumentArray` or output files directly. |

## Config and prompt failures that look like runtime failures

- `AttributeError: unknown argument` means the config key is not in the default schema and does not start with `_`; use the configuration sub-skill validator.
- Invalid schedule strings are rejected unless they match the safe limited grammar and expand to exactly 1000 steps.
- `clip_guidance` entries must be a subset of the selected `clip_models`.
- Prompt schema version should be provided as the string `"1"`; unquoted numeric YAML can become an integer and fail schema dispatch.

## Service setup failures

- `python -m discoart serve` blocks by design; run it in a controlled process/session and stop it explicitly.
- The `/create` endpoint is synchronous unless the flow executor uses `floating: true`; enabling floating can start too many concurrent generation jobs and cause OOM.
- `/skip` and `/stop` act on executor events, not a single named request. Be careful with replicas and concurrent requests.
- Polling `/result` requires the same `name_docarray` that `/create` uses and the same output/storage location.

## When to stop and ask for more runtime budget

Stop instead of guessing when:

- the task requires real generation but no GPU is visible;
- model downloads are blocked by network policy;
- Docker/container GPU access requires host-level changes;
- a persistent public service, open ports, TLS, credentials, or external storage is needed;
- the requested generation size/steps/replicas exceed available VRAM or time budget.
