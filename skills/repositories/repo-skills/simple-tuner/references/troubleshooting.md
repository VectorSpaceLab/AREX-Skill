# Cross-cutting troubleshooting

Read this before diving into a workflow-specific troubleshooting file when the symptom could be install, command routing, backend, credential, or source-maintenance related.

## Install/import and CLI startup

| symptom | likely cause | next step |
|---|---|---|
| `ModuleNotFoundError: simpletuner` | The active Python environment does not have the package installed. | Install the public package variant for the target hardware, then run `python -c "import simpletuner"`. |
| `simpletuner: command not found` | Console scripts are not on `PATH` for the active environment. | Use the environment's Python module/import check first; reinstall or expose scripts for the intended shell. |
| CLI help prints a warning but exits 0 | Third-party package warning during import. | Treat help as usable if exit status is 0; capture warning only if it blocks a real command. |
| Import succeeds but training fails at model load | Import only proves package presence, not model weights, dataset, backend memory, or optional extras. | Route to `training-workflows` and validate config, backend, model access, and data layout. |

Use [scripts/check_simpletuner_environment.py](../scripts/check_simpletuner_environment.py) for read-only install checks.

## Backend and dependency mismatches

| symptom | likely cause | next step |
|---|---|---|
| CUDA requested but `torch.cuda.is_available()` is false | CPU torch wheel, driver/container passthrough issue, or wrong CUDA wheel family. | Reinstall with the documented CUDA/CUDA13 variant that matches the driver and Python version. |
| ROCm route fails to see AMD hardware | Missing ROCm build or AMD SMI support. | Use ROCm install variant and platform setup before claiming ROCm readiness. |
| Apple/MPS route behaves differently than CUDA | MPS has different precision and kernel support. | Use Apple install route and avoid CUDA-only attention/kernel assumptions. |
| Optional packages such as CaptionFlow, TransformerEngine, Kubernetes, Redis/Postgres/MySQL, JPEG XL are missing | Optional extras are not installed by default. | Install only the extra required by the selected workflow; do not install all extras just in case. |

## Configuration and data failures

| symptom | owner | next step |
|---|---|---|
| `CONFIG_BACKEND`, `CONFIG_PATH`, or environment name selects the wrong file | `training-workflows` and `data-and-config` | Resolve config backend before editing; use the training command builder for a non-running command preview. |
| Empty dataset, missing captions, filtered samples, duplicate default text cache, cache collisions | `data-and-config` | Read the dataloader schema/troubleshooting references and run the bundled dataloader validator. |
| Paired reference/ControlNet/conditioning data does not align | `data-and-config` | Check source dataset ids, `conditioning_data`, `conditioning_type`, filename stems, and strict/loose alignment assumptions. |

## Training runtime failures

| symptom | owner | next step |
|---|---|---|
| Out of memory | `training-workflows` | Lower resolution/batch size, use quantization/offload/checkpointing, or select distributed/memory planning. |
| DeepSpeed and FSDP both enabled | `training-workflows` | Choose exactly one; FSDP2 and DeepSpeed are mutually exclusive in SimpleTuner planning. |
| Context parallel requested without FSDP2 | `training-workflows` | Enable FSDP2 or reduce context parallel size to 1. |
| Resume after changing topology/dataset/batch settings behaves badly | `training-workflows` | Do not assume checkpoint resume supports those changes; prefer a clean run unless explicit support is verified. |

## Operations and credentials

| symptom | owner | next step |
|---|---|---|
| WebUI server starts but API auth fails | `webui-and-operations` | Check first-admin/API key setup and auth mode before retrying requests. |
| SSE/log stream hangs behind proxy | `webui-and-operations` | Review reverse proxy buffering/timeouts and stream endpoints. |
| Job stuck queued | `webui-and-operations` | Inspect queue stats, local GPU allocation, worker availability/labels, approval status, and concurrency limits. |
| Cloud upload or webhook fails | `webui-and-operations` | Verify provider credentials, upload target, consent/state, callback URL, and webhook secret. Do not publish secrets. |

## Contributor and public-text failures

| symptom | owner | next step |
|---|---|---|
| A plan lacks root cause or line/function targets | `repo-development` | Reject or revise the plan before editing. |
| `pytest` appears in validation | `repo-development` | Use `unittest` commands instead. |
| WebUI form/event bug has only Jest coverage | `repo-development` | Add Selenium E2E when event propagation, Alpine reactivity, or form dirty state is involved. |
| Public text contains local identity | `repo-development` | Stop and report only `Blocked: local machine identity was found in public text.` |
