# Conversion Workflows

## Dummy-meta export

Use the bundled `export_dummy_meta.py` helper when you need a tiny safetensors file that keeps only tensor metadata in the header.

Typical flow:
1. Point the script at one `.safetensors` file or at a directory of files.
2. Let it write a `_dummy_meta.safetensors` file or a separate output directory.
3. Use the dummy-meta file wherever a config expects metadata but not the original tensor payload.

## LoRA extraction

Use the bundled `extract_lora.py` helper when you have a base checkpoint and a fine-tuned checkpoint and want a LoRA-style delta.

Typical flow:
1. Choose the source and target checkpoint formats (`safetensors` or `pytorch`).
2. Pick whether you want direct diffs or rank decomposition.
3. Choose the output format and dtype.
4. Review the printed summary for skipped or mismatched keys.

## LoRA merging

Use the bundled `merge_lora.py` helper when you want to apply a LoRA checkpoint or a diff-style checkpoint back into a base model.

Typical flow:
1. Load the base weights and the LoRA weights.
2. Select the output dtype and alpha strength.
3. Save the merged checkpoint in safetensors or pytorch format.
4. Verify that the source-key mapping covered the expected layers.

## Full converter as reference-only

The broader `converter.py` workflow is documented for completeness, but it stays reference-only in this skill graph.

Use the reference path when you need:
- architecture conversion between LightX2V and other layouts
- quantization modes beyond the lightweight helpers
- block/chunk save strategies
- family-specific converter behavior

If you only need LoRA extraction, LoRA merging, or metadata-only export, the bundled helpers are the better choice.

## Good response structure

When answering conversion questions, tell the user:
- which script to use
- which source and target paths to supply
- which format or dtype to pick
- what kind of key-mapping or shape mismatch to expect
- whether the full converter is necessary or not
