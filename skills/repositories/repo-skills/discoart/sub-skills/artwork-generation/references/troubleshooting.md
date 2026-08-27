# Artwork Generation Troubleshooting

Use this reference for DiscoArt `create()` and `go_big()` failures: CUDA/runtime problems, model cache/download issues, OOM, missing output artifacts, DocArray recovery, W&B behavior, and skip/stop interruptions.

For prompt-schema and schedule validation errors, route to `../configuration-and-prompts/SKILL.md`. For CLI/service/Docker/Jupyter launch issues, route to `../cli-and-serving/SKILL.md`.

## First diagnostic: plan without generation

Before rerunning a failing generation, summarize the config safely:

```bash
# from this sub-skill directory
python scripts/plan_create_request.py --config failing.yml --check-cuda
```

This checks normalized settings, likely output name/path, risky parameters, and PyTorch CUDA visibility without calling `create()` or downloading models.

## Symptom → likely cause → fix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `CUDA is not available` warning | PyTorch cannot see a CUDA device; CPU fallback is active. | Install/use a CUDA-capable PyTorch environment, run on a GPU host, check driver/container GPU access, then verify with `torch.cuda.is_available()`. CPU generation is expected to be impractically slow. |
| Import error for `torch`, `docarray`, `clip`, `open_clip`, `guided_diffusion`, `lpips`, or `wandb` | Package environment is incomplete or incompatible. | Reinstall the DiscoArt runtime dependencies in the active environment. If `pkg_resources` is missing in newer setuptools, install a setuptools version that still provides it or use an environment known to support DiscoArt 0.12.2. |
| Model download hangs or fails | Network unavailable, remote model-list sync blocked, source URL unavailable, cache unwritable, or disk full. | Set `DISCOART_CACHE_DIR` to a writable cache, pre-populate model files, set `DISCOART_DISABLE_REMOTE_MODELS=1` for offline/reproducible runs, or point `DISCOART_MODELS_YAML` at a local catalog. |
| SHA/checksum mismatch | Corrupt partial download or custom mirror with different file. | Delete/replace the cached file and retry. Use `DISCOART_DISABLE_CHECK_MODEL_SHA=1` only for trusted local mirrors when you deliberately accept bypassing integrity checks. |
| `diffusion_model` not supported | Name/prefix does not match the model catalog and is not a local file. | Use a known prefix such as `512`, `256`, `watercolor`, `portrait`, or provide an existing local `.pt` path plus `diffusion_model_config` when required. |
| CUDA OOM during model load or sampling | Canvas too large, `batch_size` too high, too many/heavy CLIP models, secondary model disabled, or cut settings too memory-heavy. | Reduce `width_height`, set `batch_size=1`, reduce `clip_models`, avoid heavy `RN50x16/RN50x64/ViT-L` models, try `text_clip_on_cpu=True`, keep `use_secondary_model=True`, and tune cuts. |
| Very slow generation | CPU fallback, excessive `steps`, large canvas, many CLIP models, high `n_batches`, `go_big()` chunk explosion, or high `cutn_batches`. | Confirm CUDA, lower `steps`, reduce canvas/CLIP set, use `n_batches=1` while testing, and for `go_big()` increase `window_size`/`skip_rate` or decrease `upscale_factor`. |
| No PNG files | `image_output=False`, run did not reach a save/completion point, output dir/name mismatch, or interrupted before image save. | Check `<DISCOART_OUTPUT_DIR or .>/<name_docarray>/da.protobuf.lz4`; if protobuf exists, recover from it. Re-run with `image_output=True`, explicit `name_docarray`, and `save_rate>0` if intermediate PNGs are needed. |
| No progress GIF | `gif_fps <= 0`, `image_output=False`, no chunks saved, or GIF plotting failed for empty/invalid chunks. | Set `gif_fps` positive, `image_output=True`, and `save_rate>0`. Use protobuf/DocArray chunks as the recovery source if GIF creation failed. |
| `da.protobuf.lz4` missing | Wrong output root/name, local save thread never reached a save point, permissions issue, or the process crashed before persistence. | Verify `DISCOART_OUTPUT_DIR` was set before the run, inspect the exact `name_docarray`, ensure output root is writable, and use `DocumentArray.pull(name)` if cloud backup succeeded. |
| `DocumentArray.pull(name)` fails | Cloud backup was opted out, network/auth unavailable, wrong `name_docarray`, or push failed during generation. | Prefer local protobuf when available. Confirm `DISCOART_OPTOUT_CLOUD_BACKUP` was not set and the session id/name is exact. |
| Protobuf load fails | Incomplete/corrupt write, incompatible DocArray version, wrong path, or reading while a generation process is still writing. | Wait for the process/save threads to finish, copy the file before loading in another process, verify DocArray version compatibility, and fall back to cloud pull if available. |
| W&B prompts, auth errors, or network noise | `WANDB_MODE=online` without credentials/network. | Set `WANDB_MODE=disabled` or `offline` before import/run unless online tracking is intentional. |
| Notebook/IPython display errors in a headless job | IPython integration attempted in a non-notebook runtime. | Set `DISCOART_DISABLE_IPYTHON=1` and optionally `DISCOART_DISABLE_RESULT_SUMMARY=1` before import/run. |
| `skip_event`/`stop_event` appears ignored | Event set between polling points, wrong event object passed, or generation stuck in model loading before sampling loop. | Use `threading.Event`, `multiprocessing.Event`, or compatible object; expect events to take effect during sampling, not during initial model download/load. Recover partial outputs from protobuf/name. |
| `go_big()` takes much longer than expected | Too many sliding windows or low skip rate. | Increase `window_size`, increase `stride_size`, increase `skip_rate`, decrease `upscale_factor`, or run a smaller base image first. |

## CUDA and environment checks

Minimal check:

```python
import torch
print("torch", torch.__version__)
print("cuda available", torch.cuda.is_available())
if torch.cuda.is_available():
    print("device 0", torch.cuda.get_device_name(0))
```

Remember:

- CUDA visibility is necessary but not sufficient; model cache, VRAM headroom, compatible dependencies, and output permissions still matter.
- Containers need GPU runtime/device passthrough.
- On shared GPU machines, another process may consume most VRAM after your preflight check.

## Model-cache recovery procedure

1. Choose a stable cache directory and set it before import/run:

   ```python
   import os
   os.environ["DISCOART_CACHE_DIR"] = "/path/to/discoart-cache"
   os.environ["DISCOART_DISABLE_REMOTE_MODELS"] = "1"  # when using a fixed/local catalog
   ```

2. Verify the cache directory is writable and has enough disk space.
3. If a model file is partially downloaded or checksum fails, remove only that model file and retry.
4. For offline systems, mirror the model files and provide a local `DISCOART_MODELS_YAML` matching the filenames and SHA values.
5. Do not disable SHA checks unless the cache is trusted and you understand that integrity validation is being skipped.

## OOM reduction playbook

Apply these in order for a first successful run:

1. Use `width_height=[512, 512]` or a similarly modest multiple-of-64 size.
2. Set `batch_size=1`; keep `n_batches=1` while debugging.
3. Reduce `clip_models` to one or two default selectors, e.g. `ViT-B-32::openai` and `RN50::openai`.
4. Avoid memory-heavy CLIP variants such as `RN50x16`, `RN50x64`, `ViT-L-14`, and `ViT-L-14-336` until the baseline works.
5. Try `text_clip_on_cpu=True`.
6. Keep `use_secondary_model=True` unless you are deliberately testing the higher-VRAM path.
7. Avoid `visualize_cuts=True` and huge progress GIFs during debugging.
8. For `go_big()`, increase `skip_rate`, reduce `upscale_factor`, and reduce the number of chunks.

## Missing output/protobuf recovery

Use the exact `name_docarray` and output root. If the run used `name_docarray="lighthouse-512-demo"` and `DISCOART_OUTPUT_DIR="./discoart-outputs"`, the local protobuf should be:

```text
./discoart-outputs/lighthouse-512-demo/da.protobuf.lz4
```

Load it:

```python
from docarray import DocumentArray

da = DocumentArray.load_binary("./discoart-outputs/lighthouse-512-demo/da.protobuf.lz4")
da[0].save_uri_to_file("recovered-final.png")
```

If local protobuf is missing but cloud backup was enabled:

```python
from docarray import DocumentArray

da = DocumentArray.pull("lighthouse-512-demo")
da[0].save_uri_to_file("pulled-final.png")
```

If neither works, collect these facts before retrying:

- Exact `name_docarray` after config formatting.
- Value of `DISCOART_OUTPUT_DIR` in the process that ran generation.
- Whether `DISCOART_OPTOUT_CLOUD_BACKUP` was set.
- Whether the process ended cleanly, received `KeyboardInterrupt`, or was killed.
- Values of `image_output`, `save_rate`, `gif_fps`, `n_batches`, and `batch_size`.

## Interruption and partial results

- `KeyboardInterrupt`: `create()` may not return a `DocumentArray`, but local/cloud persistence can still have partial data if a save happened.
- `skip_event`: current batch is skipped and the event is cleared; subsequent batches continue.
- `stop_event`: remaining batches are skipped and the event is cleared; `create()` returns what was collected so far when possible.
- For robust long runs, choose a stable `name_docarray`, set `DISCOART_OUTPUT_DIR`, keep cloud backup enabled unless policy forbids it, and use a positive `save_rate`.

## Unknown-argument and scheduling errors

`create()` normalizes through the same argument schema as `load_config`. If a user sees `AttributeError: unknown argument ...`, a misspelled kwarg or stale config key is likely. If a schedule string fails or prompt activation looks wrong, route to `configuration-and-prompts` for validation rather than debugging generation runtime.

## When to rerun

Rerun only after narrowing the failure class:

- If planning fails: fix config keys/schema first.
- If CUDA check fails: fix environment/GPU before generation.
- If cache/download fails: fix cache/network/model catalog before generation.
- If OOM occurs: reduce memory levers before retrying.
- If output is missing after a completed run: recover by exact `name_docarray`/protobuf/cloud pull before launching another expensive run.
