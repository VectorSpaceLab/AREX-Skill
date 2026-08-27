# Serving Troubleshooting

Use this reference when controller, worker, Gradio, or endpoint checks fail.

## Known checkout import defects

### `ModuleNotFoundError: No module named 'pipeline.constants'`

Observed during serving help checks. Several serving modules import `pipeline.constants`, but this checkout does not contain that module. Equivalent constants exist in `pipeline.serve.serving_utils`:

- `CONTROLLER_HEART_BEAT_EXPIRATION = 2 * 60`
- `WORKER_HEART_BEAT_INTERVAL = 30`
- `LOGDIR = "./logs"`

Recovery options:

1. If the user is maintaining an Otter checkout, add or patch a `pipeline/constants.py` compatibility module that re-exports those values from `pipeline.serve.serving_utils`.
2. If the user only needs command planning, use `scripts/build_serving_commands.py` and do not import the serving modules.
3. If deploying, run `scripts/check_serving_imports.py --repo-root <target-checkout>` after the patch to confirm the import path is clean.

Do not ignore this error and start services anyway; controller/worker/Gradio modules import constants before parsing CLI flags.

### `ModuleNotFoundError: No module named 'flamingo'`

`model_worker.py` imports `from flamingo import FlamingoForConditionalGeneration`, while the installable package exposes Flamingo as `otter_ai.models.flamingo` and root `otter_ai.FlamingoForConditionalGeneration`. Recovery options:

- Prefer Otter checkpoints whose worker path imports `OtterForConditionalGeneration` from `otter_ai`.
- Patch the worker import in a target checkout to `from otter_ai import FlamingoForConditionalGeneration` if serving Flamingo through this worker.
- Do not create a fake `flamingo` package unless the deployment explicitly owns that compatibility layer.

### `xformers_model` and optional xformers

The model-inference sub-skill covers this in more depth. If `xformers` is installed, Otter model code may try to import a top-level `xformers_model` package. The installable package layout only includes modules under `src`, so a deployment may need a target-checkout path or packaging patch for that optional acceleration path. If `xformers` is absent, the model code falls back to Transformers CLIP/LLaMA classes.

## Gradio version errors

Symptoms:

- `AttributeError` around `gr.Button.update`, `Dropdown.update`, or component `.update()`.
- UI builds but queue or launch arguments differ from installed Gradio.

Likely cause: serving docs warn that newer `gradio` and `gradio_client` can break the demo. Pin near the documented serving stack (`gradio==4.7.1`) before changing UI logic. Check FastAPI/Uvicorn compatibility at the same time.

## Worker registration fails

Symptoms:

- Worker logs show repeated heartbeat errors.
- Controller `/list_models` returns an empty list.
- Gradio dropdown never shows the expected model.

Checks:

1. Controller URL in worker `--controller_address` must match controller host/port.
2. Worker URL in `--worker_address` must be reachable from the controller.
3. Controller `/register_worker` expects worker status with `model_names`, `speed`, and `queue_length`.
4. If the controller runs on a remote host, do not use `localhost` in `--worker_address` unless controller and worker are on the same host.
5. Confirm firewall/security group rules for controller and worker ports.

## `no worker` or `error_code: 2`

The controller returns the generic server error when no registered worker advertises the requested `model`. Check:

- Request payload `model` matches worker `--model_name` exactly.
- Worker has not expired due to missed heartbeats.
- Worker did not crash after model load.
- Dispatch method is valid (`shortest_queue` or `lottery`).

## CUDA or model load failures

Symptoms:

- CUDA out-of-memory during worker startup.
- `torch.cuda.CudaError` during streaming.
- Quantized load failures with `int8` or `int4`.

Recovery:

- Choose `bf16` on A100/Hopper-class GPUs when the checkpoint supports it; choose `fp16` for broad CUDA compatibility.
- Increase `--num_gpus` or use a smaller checkpoint/model.
- Lower `--limit_model_concurrency` before debugging memory leaks.
- Avoid `int8`/`int4` unless the environment has matching quantization dependencies and the model class supports them.
- Test package/API inference first through [model-inference](../../model-inference/SKILL.md) before adding controller/Gradio layers.

## Image/video payload problems

Symptoms:

- PIL fails to decode images.
- Assertion fails on video frame shape.
- Generated output ignores the image.

Checks:

- `images` should be URL-safe base64 strings, not file paths.
- For video, pass a nested list of frame strings so the worker sets `is_video=True`.
- Use a prompt that includes the `<image>` marker for visual context.
- Ensure image preprocessing uses RGB images and CLIP-sized tensor expectations.

## Moderation or credential failures

Gradio `--moderate` sends text to the OpenAI moderation API and requires `OPENAI_API_KEY`. If the user has not explicitly requested moderation, keep it disabled. If enabled and requests fail, decide whether to disable moderation for a private deployment or configure the key/service before exposing the UI.

## When to route elsewhere

- The user only wants to run a one-off prompt or validate an inference YAML: [model-inference](../../model-inference/SKILL.md).
- The user is preparing training data or debugging MIMIC-IT paths: [data-preparation](../../data-preparation/SKILL.md).
- The user is tuning or pretraining models: [training](../../training/SKILL.md).
- The user is configuring benchmark evaluation: [benchmark-evaluation](../../benchmark-evaluation/SKILL.md).
