# Model setup

DreamOmni2 uses a small model stack plus two LoRA adapters. The bundled wrappers assume local model paths by default, but they can also point at Hugging Face model IDs if your environment can download them at runtime.

## Expected layout

| Component | Default path used by the bundled helpers | Purpose |
| --- | --- | --- |
| VLM checkpoint | `models/vlm-model` | The Qwen2.5-VL model used to turn image+instruction inputs into a diffusion prompt |
| Editing LoRA | `models/edit_lora` | Adapter used by the editing workflow |
| Generation LoRA | `models/gen_lora` | Adapter used by the generation workflow |
| Base diffusion model | `black-forest-labs/FLUX.1-Kontext-dev` | Base DreamOmni2 diffusion model used by both workflows |

## How the workflows use the models

- `sub-skills/inference/` loads the VLM first, asks it to rewrite the instruction into a prompt, then runs the DreamOmni2 pipeline with the editing or generation adapter.
- `sub-skills/web-demo/` uses the same stack but keeps the process alive as a Gradio app.

## Quick checks

Use `scripts/check_models.py` to confirm that the local directories you intend to use exist before launching a workflow.

## Downloading the assets

The repository README shows the upstream Hugging Face download pattern. The skill wrappers do not hardcode the source repository's example image paths, so you need to provide your own images or point the scripts at a local copy of the assets.

A typical setup is:

1. Choose a writable `models/` directory.
2. Download or point to the VLM checkpoint.
3. Download or point to the editing and generation LoRA directories.
4. Confirm that the base model identifier is reachable from your environment if you are not using a cached local copy.

## Notes

- The repo does not ship the model weights.
- If the VLM or base model download fails with a permission or license error, accept the upstream model terms or authenticate with the provider before retrying.
- The public skill content should refer to the model layout above, not to the source checkout's `example_input/` fixtures.
