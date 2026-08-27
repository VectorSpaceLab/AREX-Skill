# Web demo workflows

The DreamOmni2 browser workflows are thin Gradio wrappers around the same model stack used by the CLI scripts.

## Editing demo

```bash
python sub-skills/web-demo/scripts/web_edit.py \
  --vlm-path models/vlm-model \
  --edit-lora-path models/edit_lora \
  --server_name 0.0.0.0 \
  --server_port 7860
```

Behavior:

- Launches a two-image editing UI.
- Upload the source image first and the reference image second.
- The demo writes the result to a temporary file and returns that file path to Gradio.

## Generation demo

```bash
python sub-skills/web-demo/scripts/web_generate.py \
  --vlm-path models/vlm-model \
  --gen-lora-path models/gen_lora \
  --server_name 0.0.0.0 \
  --server_port 7861 \
  --height 1024 \
  --width 1024
```

Behavior:

- Launches a two-image generation UI.
- Upload two reference images and describe the scene you want.
- The demo writes the result to a temporary file and returns that file path to Gradio.

## Shared launch expectations

- Both launchers use the same DreamOmni2 base model and the same VLM prompt stage.
- Both launchers assume the model directories from `../../references/model-setup.md` unless you override them.
- Both launchers are long-running processes; run them from a terminal and stop them with `Ctrl+C` when you are done.

## UI behavior

- The UIs are intentionally minimal and do not rely on the source checkout's bundled sample images.
- The result panel updates after the underlying workflow saves a temporary image file.
- If you want to change the server binding or port, pass the launcher flags rather than editing the script.

## Validation checks

- `python sub-skills/web-demo/scripts/web_edit.py --help`
- `python sub-skills/web-demo/scripts/web_generate.py --help`
- `scripts/check_models.py` before the first full launch
