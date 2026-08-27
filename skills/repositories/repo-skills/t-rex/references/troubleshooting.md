# T-Rex2 Cross-cutting Troubleshooting

Use this root reference for installation, import, dependency, credential, and environment-level issues. Use sub-skill troubleshooting for cloud API payloads or visualization/UI behavior.

## Install and import issues

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: No module named 'trex'` | T-Rex2 package is not installed in the active Python environment. | Install the package from the official source/package location, then run `python scripts/check_trex_install.py` from the generated skill directory. |
| Source install fails with `ModuleNotFoundError: No module named 'torch'` while building metadata | `setup.py` imports `torch.utils.cpp_extension` even though the runtime cloud wrapper does not use local torch inference. PEP 517 build isolation hides target-environment torch from setup. | Install a compatible CPU torch in the target env and retry source install with `--no-build-isolation`, or use a prebuilt package/wheel if available. Do not treat this as a required CUDA backend. |
| `pip check` reports missing `pydantic==2.10.6` or `gradio==4.44.1` | The package metadata declares exact runtime/UI pins. | Install the pinned dependencies in the environment that will run T-Rex2 workflows. |
| `ImportError: cannot import name 'HfFolder' from 'huggingface_hub'` when importing Gradio | `gradio==4.44.1` expects an older Hugging Face Hub API. | Install a compatible Hub version such as `huggingface_hub<1.0` for the Gradio demo environment. |
| `ModuleNotFoundError: gradio_image_prompter` | The local Gradio demo uses an optional prompt widget package. | Install `gradio-image-prompter` only when running or inspecting the UI workflow. Core cloud API scripts do not need it. |
| `ImportError` for `requests`, `PIL`, or `numpy` | The source imports these packages but not all are declared directly in `requirements.txt`. | Install `requests`, `Pillow`, and `numpy` in the workflow environment. |

## Credential and network boundary

T-Rex2 detections are served by the DeepDataSpace cloud API. Local imports, payload conversion, postprocess, and rendering can be checked offline; live detection requires:

- a valid DeepDataSpace T-Rex2 API token,
- network access to the API service,
- sufficient account quota,
- images and prompt coordinates that the service accepts.

If a workflow fails during live API calls, first rerun the bundled cloud script with `--dry-run` to separate local schema/file problems from credential or service problems. Never paste real tokens into prompt JSON, output JSON, shared logs, or generated skill files.

## Backend boundary

The selected skill scope has no required local CUDA/ROCm/MPS backend. A visible GPU does not make T-Rex2 faster locally because inference happens through a remote service. Install local accelerator packages only for unrelated user code, not for this repo skill's cloud API wrapper.

## Offline smoke check

From the generated `t-rex` skill directory, run:

```bash
python scripts/check_trex_install.py --json
```

Expected result: imports succeed, payload conversion and postprocess pass, and visualization succeeds on a synthetic image. If visualization fails with `score.item`, use the visualization sub-skill's renderer or convert scores to NumPy arrays before drawing.

## Where to route next

- Token, payload, API status, embedding file, and live cloud call issues: [../sub-skills/cloud-api-workflows/references/troubleshooting.md](../sub-skills/cloud-api-workflows/references/troubleshooting.md)
- Detection JSON, drawing, threshold, `score.item`, color, and Gradio UI issues: [../sub-skills/visualization-and-demo/references/troubleshooting.md](../sub-skills/visualization-and-demo/references/troubleshooting.md)
- Current checkout differs from the provenance snapshot: refresh the repo skill before relying on stale guidance.
