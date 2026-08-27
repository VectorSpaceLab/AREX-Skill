# InternGPT Troubleshooting

This page collects cross-cutting failures that appear across more than one InternGPT workflow. For workflow-specific fixes, open the nearest sub-skill reference first.

## Install and environment issues

- **Python version mismatch**: the repository docs target Python 3.8+ and the runtime stack is old enough that Python 3.10 or 3.11 is usually safer than newer interpreters.
- **Broad requirements confusion**: the repository ships one large `requirements.txt` for many optional model families. Do not assume every dependency is needed for every workflow.
- **Missing packaging metadata**: the checkout is service-oriented rather than a normal installable package. Use the app entry point and bundled validators instead of expecting a clean import-only package install.
- **No model_zoo directory**: most useful app workflows need checkpoints under `model_zoo/`. A launch failure that mentions a missing checkpoint is usually an environment/setup issue, not a Python syntax bug.

## CUDA and memory issues

- **CUDA not available or wrong device**: many wrappers expect CUDA and move models between CPU and GPU depending on `e-mode`. A CPU import does not prove the model can run.
- **Out of memory**: use a narrower `--load` set, a smaller tab set, or `-e/--e-mode` when the wrapper supports offload. Do not treat `-e` as CPU-only mode.
- **Custom op / extension failure**: StyleGAN, detectron2, and similar extensions can fail if the wheel, compiler, or torch/CUDA ABI does not match the host.

## Checkpoint and model-zoo issues

- **Husky/LLaMA**: if the partial checkpoint folder exists but `params.json`, `config.json`, or other converted files are missing, the base LLaMA download or delta conversion likely stopped halfway. Remove the broken partial tree and rebuild from the documented helper path.
- **SAM / LaMa / Tag2Text / GRiT / StyleGAN / ImageBind**: these workflows depend on external checkpoints or caches. If the tool is unloaded or the file path is missing, the runtime cannot be verified from source alone.
- **Broken partial downloads**: if a model folder exists but the app still reports missing files, prefer deleting only the broken model artifact and re-downloading it instead of reinstalling the whole repository.

## Credential and service issues

- **OpenAI API key missing**: chat and clip-generation flows that rely on LangChain/OpenAI will fail early or fall back to login prompts. The skill should describe the prerequisite rather than pretending the model stack is self-contained.
- **`OPENAI_API_BASE` confusion**: the app can respect an alternate base URL. Make sure the user knows whether they are configuring the public API or a compatible proxy.
- **HTTPS certificates missing**: the voice-assistant path expects `certificate/cert.pem` and `certificate/key.pem` when `--https` is used.

## Docker and path issues

- **Placeholder volumes**: the shipped Docker examples use placeholder host paths. Replace them with real mounted directories for `model_zoo` and any certificate directory before launching.
- **Wrong working directory**: app-relative paths like `image/`, `model_zoo/`, and `certificate/` are resolved from the runtime working directory. Launch from the repository root or adapt the paths consistently.
- **Image/mask parent recovery failures**: when a mask filename no longer matches the source image anchor, the visual-dialogue workflow may not be able to reconstruct the correct parent path. Use the bundled mask validator before invoking removal or replacement.

## Validation guidance

- Use the per-sub-skill validators to catch static mistakes before a heavy launch:
  - `sub-skills/app-deployment/scripts/validate_load_plan.py`
  - `sub-skills/visual-dialogue-tools/scripts/validate_mask_inputs.py`
  - `sub-skills/cross-modal-generation/scripts/validate_multimodal_assets.py`
  - `sub-skills/video-understanding/scripts/validate_video_plan.py`
- If a static validator fails, fix the plan before asking the user to download models or start a service.
- If a live workflow still fails after validation, check the nearest sub-skill reference for the exact tool or checkpoint family instead of broadening to the full app.
