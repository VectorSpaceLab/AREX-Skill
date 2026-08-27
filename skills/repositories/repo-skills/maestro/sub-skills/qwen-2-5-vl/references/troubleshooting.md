# Qwen2.5-VL troubleshooting

The table below focuses on Qwen-specific failure modes. Dataset and metric validation issues that are not Qwen-specific belong in the sibling dataset skill.

## Compatibility note

The current source expects `qwen-vl-utils` `0.0.8`-style `smart_resize(...)` behavior. Newer releases can change that API and produce `TypeError` or missing-argument failures when `detections_to_suffix_formatter(...)` runs. If that happens, pin `qwen-vl-utils==0.0.8` and retry.

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `smart_resize(...)` complains about a missing `factor` or other signature mismatch | `qwen-vl-utils` version drift | Pin `qwen-vl-utils==0.0.8` so the current source call signature matches the installed helper. |
| `transformers` import or model-class errors around `Qwen2_5_VLProcessor` / `Qwen2_5_VLForConditionalGeneration` | Experimental support or stale install | Install a Transformers build that exposes the Qwen2.5-VL processor/model classes, then re-run the smoke checks. |
| `bitsandbytes` or 4-bit quantization errors during QLoRA setup | CUDA / BitsAndBytes mismatch or CPU-only environment | Use a CUDA-capable environment with a compatible `bitsandbytes` build, or switch to `lora` / `none` if you only need inspection. |
| `ValueError: Requested device '...' is not available.` | The selected device is not visible to the current runtime | Use `auto`, `cpu`, or a visible CUDA device name before constructing `Qwen25VLConfiguration`. |
| Generated text includes extra prose instead of a JSON object or JSON list | The system message is too weak or inconsistent with training | Make the `system_message` explicit, keep it the same in training and inference, and let `predict(...)` add the generation prompt. |
| JSON parses but detection labels or boxes are wrong | Prefix, suffix, and pixel-size settings are out of sync | Keep `min_pixels`, `max_pixels`, the prefix labels, and the suffix formatter aligned across training, loading, inference, and parsing. |
| Detection parsing fails with `sv.Detections.from_vlm(...)` | The suffix is not a fenced JSON array with `bbox_2d` and `label` | Regenerate the suffix with `detections_to_suffix_formatter(...)` and validate the output with the bundled smoke script. |
| `--peft_advanced_params` fails to parse | CLI received something other than a JSON object string | Pass a valid JSON mapping, for example `'{"r": 16, "lora_alpha": 32}'`. |
| QLoRA is too slow or runs out of memory | The model is too large for the selected batch size or pixel bounds | Lower `batch_size`, raise `accumulate_grad_batches`, reduce `max_pixels`, or switch from `qlora` to `lora`. |
| Training or inference appears to ignore the image | The conversation was built manually and missed the image turn | Use `format_conversation(...)` and the provided collators so the image and text turn order stays correct. |

## How to recover quickly

1. Run `python scripts/smoke_qwen_detection_format.py` to verify the formatter path.
2. Run `python scripts/build_qwen_config.py --help` to confirm the config builder still parses.
3. Re-check the model ID, revision, pixel bounds, and optimization strategy.
4. If the issue is still present, fall back to `none` or `lora` before retrying QLoRA.

## When to hand off elsewhere

- Dataset missing splits, bad Roboflow IDs, or malformed JSONL / COCO annotations: use the sibling dataset skill.
- Model download, token, or hub access problems: treat those as environment or installation issues first.
- Problems in Florence-2 or PaliGemma 2 workflows: route to the sibling model skill instead of trying to force a Qwen fix.
