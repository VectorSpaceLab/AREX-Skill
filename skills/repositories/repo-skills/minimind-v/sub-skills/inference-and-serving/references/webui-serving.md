# MiniMind-V WebUI and Serving Workflow

## When to use

Use the WebUI only when the user explicitly wants an interactive browser UI or local service for a Transformers-format MiniMind-V checkpoint. Prefer CLI/static checks for smoke tests and automation.

Do not start the WebUI when host/port exposure has not been accepted, the checkpoint is untrusted, resources are missing, Gradio is unavailable, or device memory is uncertain.

## Scanner behavior

The WebUI scans only immediate child directories under `--load_from`. It ignores non-directories and names starting with `.` or `_`. A child is a candidate if it directly contains `.bin`, `.safetensors`, or `model.safetensors.index.json`. It does not scan recursively and does not treat the base directory itself as a model.

Use the bundled scanner first:

```bash
python path/to/scan_transformers_models.py scripts
```

## Launch planning

A typical user-approved launch from a MiniMind-V checkout has this shape:

```bash
cd scripts
python web_demo_vlm.py --load_from . --vision_model ../model/siglip2-base-p32-256-ve --temperature 0.7 --top_p 0.95 --device cpu --max_seq_len 8192
```

Use CUDA only after confirming memory. The script attaches SigLIP2, loads tokenizer/model with `trust_remote_code=True`, and launches Gradio using host/port values configured in the script source.

## Prompt/image handling

When an image is uploaded, the WebUI opens it as RGB, converts it with SigLIP2, prepends `image_special_token * image_token_len` plus a newline, and streams generation. Without an image, it performs text-only generation.

## Safe checklist

- User explicitly asked to launch a UI/service.
- `--load_from` has immediate child model directories.
- Model directories are trusted for custom code.
- SigLIP2 is present.
- Device memory is sufficient.
- The listener exposure is acceptable.
