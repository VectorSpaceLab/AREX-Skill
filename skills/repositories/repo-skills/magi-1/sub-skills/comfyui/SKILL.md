---
name: comfyui
description: "Install and operate the MAGI-1 ComfyUI custom node and bundled workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# MAGI-1 ComfyUI operating skill

Use this sub-skill when a user wants to install, recognize, run, adapt, or troubleshoot the MAGI-1 ComfyUI custom node and its example workflows.

Do **not** use this sub-skill for source-code CLI inference commands or direct `MagiPipeline` API usage; route those questions to the MAGI-1 inference sub-skill. ComfyUI itself is an external host application dependency; this skill captures MAGI node behavior and workflow adaptation, not a verified ComfyUI host import.

## Fast operating path

1. Install ComfyUI, then install the MAGI-1 node by one of these choices:
   - Registry install from inside the ComfyUI directory: `comfy node registry-install MAGI-1`.
   - Source install by placing the MAGI-1 source tree under `ComfyUI/custom_nodes/MAGI-1` and installing MAGI-1 runtime dependencies into the same Python environment used by ComfyUI.
2. After either install method, ensure ComfyUI sees a plugin-root `__init__.py`: move or copy the repository's `comfyui/__init__.py` to the MAGI-1 plugin root if it is not already there. The plugin root must still contain the `comfyui/`, `inference/`, and `example/assets/` subtrees expected by that initializer.
3. Download model weights and edit the selected MAGI JSON config so checkpoint paths are absolute for `load`, `t5_pretrained`, and `vae_pretrained`. Use absolute paths for the ComfyUI node's `config_path`, T5 path, input media, and save path fields.
4. Launch ComfyUI with `comfy launch` or `python main.py` from the ComfyUI directory.
5. Add nodes from **Add Node → Magi** or import one of the bundled workflows, then replace every placeholder path before queueing the graph:
   - [Text to video workflow](references/workflows/magi_text_to_video_example.json)
   - [Image to video workflow](references/workflows/magi_image_to_video_example.json)
   - [Video continuation workflow](references/workflows/magi_video_continuation_example.json)

## Detailed references

- Node roles, inputs, outputs, task-mode behavior, installation notes, and workflow adaptation: [references/comfyui-nodes-and-workflows.md](references/comfyui-nodes-and-workflows.md)
- Troubleshooting path, import failures, absolute-path errors, GPU/memory issues, and output-saving issues: [references/troubleshooting.md](references/troubleshooting.md)
- Offline workflow inspection helper: [scripts/inspect_workflow_nodes.py](scripts/inspect_workflow_nodes.py)

## Guardrails for future agents

- State that imported workflow JSONs contain placeholders and must be reassigned inside the user's ComfyUI runtime.
- State that MAGI's ComfyUI `MagiProcess` node sets single-node/single-GPU distributed environment variables internally before inference.
- Do not claim ComfyUI host imports were verified unless the user has actually run ComfyUI with the MAGI node in their environment.
- Keep all workflow links generated-skill-relative; do not link to source checkout files.
