# Model inference troubleshooting

## Import and package-surface issues

### `from otter_ai import OtterConfig` fails

`OtterConfig` is not exported at the package top level in the inspected package. Import it from:

```python
from otter_ai.models.otter.configuration_otter import OtterConfig
```

The top-level package exports `OtterForConditionalGeneration` and `FlamingoForConditionalGeneration`.

### Dependency repair after import errors

Known compatible inspection stack included `transformers==4.35.1`, `tokenizers==0.14.1`, and compatible older `accelerate`, `peft`, and `huggingface_hub` versions. If imports fail after a resolver upgrade, check for mismatched `accelerate`, `peft`, or `huggingface_hub` before changing model code.

### xformers and `xformers_model` risk

Otter model code optionally tries to use xformers. The optional path imports a top-level `xformers_model` package, but the installed package layout only packages modules under the `src` package tree. Consequences:

- If `xformers` is not installed, the model falls back to standard Transformers CLIP/Llama classes.
- If `xformers` is installed but `xformers_model` is unavailable, the optional xformers acceleration path is not usable and fallback behavior should be verified.
- Do not assume installing `xformers` alone enables Otter's xformers path. Use the non-xformers path unless the installed distribution explicitly provides the needed top-level package.

## Loading and device placement

### Out-of-memory during `from_pretrained`

Try, in order:

1. Use `device_map="auto"`.
2. Use `torch_dtype=torch.bfloat16` on Ampere/newer GPUs or `torch.float16` when bf16 is unsupported.
3. Reduce generation settings such as `max_new_tokens`, beams, and batch size.
4. Confirm the checkpoint is intended for the selected class (`OtterForConditionalGeneration` vs `FlamingoForConditionalGeneration` vs Fuyu/OtterHD).
5. If multi-GPU sharding is expected, confirm all visible GPUs have enough free memory and compatible CUDA/PyTorch builds.

CPU-only loading is useful for small smoke tests and import debugging, but 9B-class generation is usually impractical on CPU.

### `device_map="auto"` and input device errors

When a model is sharded, tensors must be placed consistently with the model's execution hooks. The package generation code adds an Accelerate hook when needed, but callers should still move `vision_x`, `lang_x`, and `attention_mask` to the model/device expected by the loaded object and keep dtype aligned with `next(model.parameters()).dtype`.

## Tensor and prompt errors

### `vision_x should be of shape (b, T_img, F, C, H, W)`

The vision tensor must be 6-D. For one image:

```python
vision_x = image_processor.preprocess([image], return_tensors="pt")["pixel_values"]
vision_x = vision_x.unsqueeze(1).unsqueeze(0)
```

This produces `(1, 1, 1, 3, 224, 224)`. Do not pass a raw `(1, 3, 224, 224)` CLIP tensor directly to Otter/Flamingo.

### No-image prompts still assert for `vision_x`

No-image mode still supplies a placeholder tensor. Use prompt `User:{question} GPT:<answer>` and a zero tensor with shape `(1, 1, 1, 3, 224, 224)` unless using a deliberately cached vision context.

### Empty or badly split answers

For Otter prompts, include `<answer>` in the prompt and decode using text after `<answer>`, then remove `<|endofchunk|>`. If the decoded output does not contain `<answer>`, verify the prompt template and that the tokenizer is `model.text_tokenizer` from the same checkpoint.

### Beam search shape mismatch

`generate` repeats `vision_x` when `num_beams > 1`. Keep batch size in `vision_x`, `lang_x`, and `attention_mask` aligned before generation.

## YAML batch issues

### YAML loads but no answer is produced

Validate first:

```bash
python scripts/validate_inference_yaml.py prompts.yaml --check-local-images
```

Common problems:

- Top-level YAML is a mapping instead of a list.
- `question` is missing, `null`, or blank.
- `image_path` points to a non-image file.
- A remote URL is supplied but the calling project did not explicitly allow network fetches.
- No-image rows are intended but `image_path` contains whitespace instead of an empty string.

### Extra fields are present

The generation workflow only uses `question` and `image_path`. Keep `answer`, `expected_answer`, or `id` for project-side evaluation if useful; otherwise ignore extra metadata or validate with `--strict` to catch typos.

## Conversion issues

### Converter starts loading a model when only help or planning was intended

Use the bundled inspector instead of importing a converter module during planning:

```bash
python scripts/inspect_checkpoint_conversion_args.py --script fp32-to-fp16 --checkpoint-path CHECKPOINT --emit-command
```

The inspector is static and safe; converter modules load checkpoints when executed.

### Output path omitted

Always pass explicit output paths for `flamingo-to-otter`, `otter-to-lora`, and PT-to-HF conversion. Some source parsers accepted defaults or `None`, but those defaults are not safe reusable behavior.

### `pt-to-hf` packaged entry fails before parsing arguments

The inspected packaged entry for PT-to-HF conversion used a non-package relative import and failed before `--help`. Treat this route as a known-risk converter: verify a fixed installed build or use a project-owned patched conversion workflow before relying on it.

## Boundary mistakes

- If the error arises from data YAML groups, image JSON/parquet schemas, or Syphus/Convert-It inputs, switch to [data-preparation](../../data-preparation/SKILL.md).
- If the error is in an Accelerate/DeepSpeed command, optimizer, W&B, or training checkpoint schedule, switch to [training](../../training/SKILL.md).
- If the error involves controller/worker registration, Gradio, ports, or streaming endpoints, switch to [serving](../../serving/SKILL.md).
- If the error involves benchmark dataset names, GPT API judging, or benchmark config keys, switch to [benchmark-evaluation](../../benchmark-evaluation/SKILL.md).
