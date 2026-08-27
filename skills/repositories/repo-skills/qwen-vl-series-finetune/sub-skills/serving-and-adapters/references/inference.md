# Inference

## Gradio launch pattern

The bundled web demo is launched with the copied module entry point from the skill root:

```bash
cd <this-skill-root>
PYTHONPATH=src${PYTHONPATH:+:$PYTHONPATH} python -m src.serve.app --model-path <checkpoint>
```

Prefer the helper so the working directory and `PYTHONPATH` are set correctly:

```bash
python scripts/adapter_command.py gradio --model-path <checkpoint> --device cuda
# add --run only when a network-facing Gradio process should start
```

## Useful flags

- `--model-base` for adapter-backed checkpoints
- `--device` to control the serving device
- `--load-8bit` / `--load-4bit` for quantized loading
- `--disable_flash_attention` when the user wants the stable SDPA path
- `--temperature`, `--repetition-penalty`, `--max-new-tokens` for generation control

## Behavior notes

- The demo accepts image and video uploads.
- The prompt builder uses the repo’s multimodal processor and vision utilities.
- Serving is network-facing, so a dry-run command print is the safest first step.
