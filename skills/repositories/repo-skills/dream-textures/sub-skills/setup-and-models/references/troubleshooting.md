# Setup and Model Troubleshooting

Use this reference to recover from common Dream Textures installation, dependency, token, cache, DreamStudio, checkpoint, and model mismatch issues. Validate facts in this order: add-on layout, dependency target, backend variant, credentials, model availability, then task/model compatibility.

## Fast triage table

| Symptom | Likely cause | Validation | Recovery |
| --- | --- | --- | --- |
| Add-on cannot be enabled or cannot be found | Folder name/layout is wrong; user selected parent folder; source checkout named with hyphen | Run `scripts/check_addon_layout.py` on the folder; check for `__init__.py` directly inside the add-on folder; check package name hint | Rename/copy the add-on package folder to `dream_textures`, install the actual inner zip/folder, restart Blender |
| Preferences show **Dependencies Missing** | Source checkout installed by accident, release variant incomplete, or `.python_dependencies` empty | Check `.python_dependencies` exists and has more than placeholder files | Ordinary user: install the correct prebuilt release. Developer/source user: install one requirement variant into `.python_dependencies` with Blender's Python or the add-on Developer Tools |
| `ModuleNotFoundError` for `torch`, `diffusers`, `huggingface_hub`, `transformers`, `accelerate`, or `controlnet_aux` | Dependencies installed into the wrong Python or wrong target directory | Confirm packages exist under `.python_dependencies` and that Blender was restarted | Reinstall the matching requirement variant into `.python_dependencies`; avoid installing all variants or only a shell venv |
| CUDA/ROCm/MPS/DirectML not used | Wrong torch build or wrong requirement variant | Compare platform/backend to `backend-compatibility.md`; check torch variant from Blender Python if available | Reinstall the correct dependency variant; do not mix CUDA, ROCm, MPS, and DirectML packages in the same target |
| macOS dependency libraries blocked | Quarantine attribute on downloaded dependency binaries | On macOS, errors may only appear when launching Blender from Terminal | Remove quarantine from the add-on's `.python_dependencies` directory with `xattr -r -d com.apple.quarantine /path/to/dream_textures/.python_dependencies`, then restart Blender |
| No console output on macOS | Blender has no Toggle System Console menu on macOS | Launch Blender from Terminal and reproduce the issue | Use the Terminal-launched Blender output to capture import or dependency errors |
| Preferences warn about `wandb` or `k_diffusion` conflicts | Conflicting packages found in Blender-visible site-packages | Preferences list conflicting package locations | Use the preferences uninstall-conflicts action when appropriate, possibly with administrator rights; if it fails, remove only the reported conflicting package folders |
| Model search has no result or download fails | Query mismatch, network issue, missing Hugging Face token, gated terms not accepted, or repo is not Diffusers-compatible | Search exact repo id; check whether the model page is gated/private; verify token permissions | Enter a Hugging Face token, accept gated model terms, retry with resume enabled, or choose a Diffusers-compatible model |
| Download says model is not a pipeline or model | Hugging Face repo lacks `model_index.json` and usable `config.json`/weights | Inspect the model repository metadata/page | Choose a Diffusers pipeline repository or an individual model repository with compatible config and weights |
| Imported checkpoint conversion fails | Wrong checkpoint config, missing conversion dependencies, unsupported file, or corrupted checkpoint | Confirm extension is `.ckpt`, `.safetensors`, or `.pth`; compare checkpoint family to config matrix | Retry with explicit config (`v1`, v2, depth, inpainting, XL, ControlNet) and ensure source/developer dependencies include conversion packages |
| Linked checkpoint appears but wrong workflow fails | Link used the wrong model config or checkpoint basename collision hides expected config | Check linked checkpoint list; avoid duplicate basenames across linked folders | Unlink/relink the file with the correct model config, or import a converted Diffusers model with an unambiguous basename |
| Inpaint/outpaint rejects selected model | Prompt-to-image model selected for an inpainting task | Compare selected model type to task matrix | Download/import `stabilityai/stable-diffusion-2-inpainting` or another inpainting model |
| Texture projection or depth workflow rejects selected model | Prompt/inpaint/upscale model selected for depth-to-image | Compare selected model type to task matrix | Download/import `stabilityai/stable-diffusion-2-depth` or route scene setup to `scene-integration` after model selection |
| Upscaling workflow rejects selected model | Non-upscaler model selected | Compare selected model type to task matrix | Download/import `stabilityai/stable-diffusion-x4-upscaler` |
| DreamStudio setup does not work | Missing, revoked, or incorrectly copied API key; cloud dependency/release variant mismatch | Verify key in DreamStudio account settings and paste only into preferences | Regenerate key, paste it into **DreamStudio Key**, avoid logging it, and check release notes for the DreamStudio-only build used |
| Setup complete but local generation still cannot run | Setup completed due to DreamStudio key, while local model/dependencies are still absent | Check whether local model list and `.python_dependencies` are actually present | For cloud use, use DreamStudio-compatible workflows. For local use, install dependencies and model weights separately |

## Safe diagnostic script usage

Run the bundled checker from a normal terminal, pointing it at the add-on folder:

```sh
python scripts/check_addon_layout.py /path/to/dream_textures
```

Useful options:

```sh
python scripts/check_addon_layout.py /path/to/dream_textures --json
python scripts/check_addon_layout.py /path/to/downloads-folder
```

The script only reads files. It does not import Blender, import the add-on, install packages, download models, call Hugging Face, or validate credentials.

Interpretation:

- `ERROR` means the folder is probably not a usable add-on package layout.
- `WARN` means the layout may work only after additional setup, a release reinstall, or source/developer dependency installation.
- `INFO` records useful facts such as declared Blender version, add-on version, requirement files, and approximate dependency-target state.

## Install/import recovery steps

1. Restart Blender after changing the add-on folder name or `.python_dependencies` content.
2. If enabling fails, capture the exact console error before reinstalling. On Windows/Linux use Blender's system console; on macOS launch Blender from Terminal.
3. Use release install for ordinary users. Use source/developer dependency installation only when source setup is intentional.
4. Verify that the installed release/source folder contains the Dream Textures package directly; avoid parent folders such as `dream-textures-main/dream_textures` being one level too deep.
5. Confirm that `.python_dependencies` belongs to this add-on folder and is not shared with another project.
6. If a dependency install was interrupted, retry the same backend variant rather than switching variants mid-target.

## Model/cache/token recovery steps

1. Confirm the intended workflow's model type from `backend-compatibility.md`.
2. Search the exact Hugging Face repo id in preferences.
3. For private/gated models, add a Hugging Face token and accept the model terms in the browser.
4. Enable resume download for interrupted downloads.
5. If the model already appears as an installed path, use the open-folder action to inspect that cache entry rather than downloading again.
6. If cache state appears stale, restart Blender and refresh the model list by opening the preferences panel again.
7. Avoid logging access tokens, DreamStudio keys, or private model names unless the user explicitly consents.

## Checkpoint recovery steps

1. Validate the checkpoint extension: `.ckpt`, `.safetensors`, or `.pth`.
2. Identify the checkpoint family: SD v1, SD v2 512 epsilon, SD v2 768 v-prediction, depth, inpainting, SDXL base, SDXL refiner, or ControlNet.
3. Use **Link Checkpoint** when the user wants to keep the file in place; use **Import Checkpoint** when they want Diffusers conversion in the cache.
4. If import fails with shape, missing key, or pipeline errors, retry with the explicit config matching the family instead of auto-detect.
5. If a workflow mismatch happens after successful import/link, pick a model matching the task rather than retrying the same checkpoint config blindly.

## Backend variant recovery steps

- **CUDA/NVIDIA**: choose the CUDA requirements variant with the cu118 PyTorch index. If torch reports CPU-only, the wrong build was installed or Blender is not using the target directory.
- **ROCm/AMD Linux**: choose the ROCm requirements variant and verify the host ROCm runtime is compatible with the torch build.
- **Apple Silicon/MPS**: choose the macOS MPS/CPU variant. If binary libraries are blocked, clear quarantine on `.python_dependencies`.
- **Windows DirectML**: choose the DirectML variant with `torch-directml`. Do not combine it with CUDA/ROCm packages in the same target.
- **Unsupported hardware**: prefer DreamStudio cloud processing or use CPU only with clear performance expectations.

## Escalation and routing

- If dependency/model setup is correct but generation parameters fail, route to `generation-workflows`.
- If projection, render pass, compositor, or scene depth setup fails, route to `scene-integration`.
- If the issue is a backend API implementation, scheduler enum, generator subprocess, or custom backend, route to `backend-and-api`.
