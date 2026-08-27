# Installation and Inspection Environment

Use the smallest environment that can still verify the selected workflow family.

## Recommended install shape

- Python 3.11.
- The bundled `references/source-requirements.txt` with the PyTorch cu128 index.
- `qwen-vl-utils` for multimodal preprocessing.
- `gradio` only when you need the serving route.
- `av` + `ffmpeg` for video support when the wheel path is unreliable.

## Common install paths

### Conda-style workflow

```bash
conda env create -f references/source-environment.yaml
conda activate train
pip install qwen-vl-utils
# Optional: pip install gradio
```

### Requirements-file workflow

```bash
pip install -r references/source-requirements.txt -f https://download.pytorch.org/whl/cu128
pip install qwen-vl-utils
# Optional: pip install gradio
```

## What to verify

- `torch` imports and reports CUDA availability when a GPU workflow is selected.
- `transformers`, `trl`, `peft`, `deepspeed`, and `liger_kernel` import cleanly.
- `qwen_vl_utils` imports for multimodal preprocessing.
- `gradio` imports only when the serving path is needed.
- `pip check` is clean after any platform-specific video-package adjustment.

## Notes

- The original repository dependency files are bundled as `references/source-requirements.txt` and `references/source-environment.yaml`; prefer the requirements file because it reflects `liger_kernel==0.8.0` while the source environment file still records an older Liger pin.
- The repository’s video path relies on PyAV/FFmpeg in the multimodal utilities. If a `decord` wheel is unavailable or unsupported on the current platform, do not treat that as a blocker for the rest of the skill; verify the PyAV/FFmpeg path instead.
- Flash Attention 2 is optional in this repo. The documented fallback is SDPA via `--disable_flash_attn2 True`.
- DeepSpeed training and multimodal generation need a real CUDA runtime. CPU-only import checks are only for parser, schema, and utility validation.

## Safe diagnostic

Use `scripts/check_environment.py` before any heavyweight task.
