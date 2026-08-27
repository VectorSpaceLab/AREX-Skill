# Model and LoRA Formats

## LightX2V weight-preparation helpers

The bundled helpers cover the most common lightweight conversion tasks:

- `export_dummy_meta.py` for metadata-only safetensors files
- `extract_lora.py` for LoRA or diff-style extraction from a source / target pair
- `merge_lora.py` for applying LoRA or diff weights back into a base checkpoint

## Supported source formats in the bundled helpers

- `safetensors`
- `pytorch` (`.pt` / `.pth`)

The bundled scripts load weights into fp32 for the arithmetic step, then cast to the requested output dtype when saving.

## LoRA naming conventions

The conversion helpers understand the most common LoRA suffix patterns:

- standard: `.lora_up.weight` / `.lora_down.weight`
- diffusers: `_lora.up.weight` / `_lora.down.weight`
- diffusers v2: `.lora_B.weight` / `.lora_A.weight`
- diffusers v3: `.lora.up.weight` / `.lora.down.weight`
- Mochi: `.lora_B` / `.lora_A`
- transformers: `.lora_linear_layer.up.weight` / `.lora_linear_layer.down.weight`
- Qwen: `.lora_B.default.weight` / `.lora_A.default.weight`
- diff deltas: `.diff`, `.diff_b`, `.diff_m`

## Output dtypes

The bundled scripts accept these output dtypes:
- `float32` / `fp32`
- `float16` / `fp16`
- `bfloat16` / `bf16`

## Quantization and the full converter

LightX2V's broader conversion stack also handles architecture conversion and more elaborate quantization modes. That full tool is documented here for reference, but it is not bundled in the runtime skill because it depends on a heavier optional CUDA extension build path and family-specific branches.

Use the bundled helpers when you only need:
- metadata-only export
- LoRA extraction
- LoRA merging

Use the reference-only full converter when you need:
- architecture remapping
- per-family quantization preparation
- block/chunk save layouts
- transformer / encoder / decoder family conversion beyond the lightweight helpers

## Common file-layout reminders

- A single-file checkpoint can be given directly.
- A directory of safetensors files is valid for the bundled LoRA helpers.
- The merge helper looks for matching source keys by stripping or restoring the expected suffixes.
- Shape mismatches usually mean the source and target checkpoints are not the same model family or not the same precision branch.
