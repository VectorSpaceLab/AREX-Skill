# ICEdit Gradio workflows

## When to choose this route
Use the Gradio route when the user wants an interactive browser loop: upload or webcam input, sample presets, live LoRA-scale changes, or a shareable link for quick review. Use the root ICEdit CLI inference route when the user wants a single shell command or batch automation. Use the root training route when the user wants to create or refresh LoRA weights.

## Bundled entry point
Set the skill root once so these commands work from any cwd:

```bash
export ICEDIT_SKILL=/path/to/ic-edit-skill
export GRADIO_SCRIPT="$ICEDIT_SKILL/sub-skills/gradio/scripts/run_icedit_gradio.py"
```

`$GRADIO_SCRIPT` is the single launcher for the normal and MoE demo paths. It accepts:
- `--mode normal|moe`
- `--server-name` / `--server_name`
- `--port`, `--share`, `--no-browser`, and `--dry-run`
- `--output-dir`, `--repo-root`, `--flux-path`, and `--lora-path`
- `--transformer` and `--text-encoder-2` / `--text_encoder_2`
- `--enable-model-cpu-offload`

The helper uses the bundled GGUF config at `$ICEDIT_SKILL/sub-skills/gradio/scripts/config.json` and preset images under `$ICEDIT_SKILL/sub-skills/gradio/references/examples/`.
## Launch recipes

### Local-only dry run on a busy machine
```bash
python "$GRADIO_SCRIPT" \
  --mode normal \
  --server-name 127.0.0.1 \
  --port 7861 \
  --no-browser \
  --dry-run
```
This prints the resolved launch plan and exits before loading the model.

### Normal Gradio demo
```bash
python "$GRADIO_SCRIPT" --mode normal --port 7860
```
Add local weights when you do not want Hub downloads:
```bash
python "$GRADIO_SCRIPT" \
  --mode normal \
  --flux-path /path/to/flux.1-fill-dev \
  --lora-path /path/to/ICEdit-normal-LoRA
```

### MoE Gradio demo
```bash
python "$GRADIO_SCRIPT" --mode moe --repo-root /path/to/ICEdit --port 7860
```
MoE is checkout-dependent: `/path/to/ICEdit` must contain the vendored `icedit/` package. Normal mode is standalone apart from installed packages and external Hub/local weights.

### GGUF low-VRAM recipe
```bash
python "$GRADIO_SCRIPT" \
  --mode normal \
  --port 7861 \
  --flux-path /path/to/flux.1-fill-dev \
  --lora-path /path/to/ICEdit-normal-LoRA \
  --transformer /path/to/flux1-fill-dev-Q4_0.gguf \
  --text-encoder-2 /path/to/t5-v1_1-xxl-encoder-Q8_0.gguf \
  --enable-model-cpu-offload
```
`--transformer` and `--text-encoder-2` are optional external files and are checked before model loading. Keep `--flux-path` and `--lora-path` available even when you quantize the transformer or text encoder.

## UI flow
1. Upload an image or pick one of the bundled presets.
2. Enter a natural-language edit prompt.
3. Keep the image width at 512 if you want to avoid automatic resizing.
4. Set seed or randomize it.
5. Adjust guidance scale, inference steps, and LoRA scale.
6. Run the demo or press Enter in the prompt box.
7. Review the edited image and, if needed, try a different seed.

The helper injects the diptych-style edit instruction internally, so users only need to type the edit request itself.

## Output behavior
- The result is saved under `--output-dir` as `result_N.png`.
- The LoRA adapter is reloaded only when the slider value changes.
- Uploaded images with a width other than 512 are resized to width 512 and their height is rounded down to a multiple of 8 before inference.

## Bundled presets
See `references/examples/index.md` for the default preset prompts and seeds that mirror the source demo.
