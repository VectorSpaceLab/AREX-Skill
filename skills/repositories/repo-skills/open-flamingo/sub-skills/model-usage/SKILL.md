---
name: model-usage
description: "Initialize OpenFlamingo models, load checkpoints, prepare
  multimodal prompts, run forward/generate, and debug media caching
  constraints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# OpenFlamingo Model Usage

Use this sub-skill when a task requires OpenFlamingo model construction, checkpoint loading, prompt/media preprocessing, generation, log-likelihood style `forward()` calls, media caching, or architecture debugging.

Do not start full model downloads, benchmark datasets, training, or evaluation unless the caller explicitly provides the required local files, network permission, hardware budget, and time budget. The safe default is to validate inputs and prepare code that works with a caller-supplied local cache or checkpoint.

## Route by task

- **Need API signatures or object relationships:** read [references/api-reference.md](references/api-reference.md).
- **Need an offline/local-cache generation recipe:** read [references/generation-workflows.md](references/generation-workflows.md).
- **Need to fix token, tensor, checkpoint, cache, decoder-layer, or import errors:** read [references/troubleshooting.md](references/troubleshooting.md).
- **Need a deterministic preflight check without downloads:** run [`scripts/validate_generation_inputs.py`](scripts/validate_generation_inputs.py).

## Critical invariants

- Public imports are `from open_flamingo import create_model_and_transforms, Flamingo`.
- The package/distribution identity is `open_flamingo` 2.0.1.
- `vision_x` for `Flamingo.forward()` and `Flamingo.generate()` is `B x T_img x F x C x H x W`; current OpenFlamingo supports **`F=1` only**.
- Text prompts must use the exact special tokens `<image>` and `<|endofchunk|>`. Each image/media item should have a matching `<image>` token in the prompt for the same example.
- For generation, set `tokenizer.padding_side = "left"` before tokenization and pass `attention_mask`.
- `generate(num_beams=N)` internally repeats `vision_x` along batch dimension when `N > 1`; do not pre-repeat the media batch for beam search.
- `cache_media()` is for repeated `forward()`/classification-style scoring, not for `generate()`. After cached calls, call `uncache_media()`.

## Safe input validation

From this sub-skill directory, validate a three-image captioning prompt without importing OpenFlamingo or downloading anything:

```bash
python scripts/validate_generation_inputs.py \
  --batch-size 1 \
  --num-media 3 \
  --num-frames 1 \
  --channels 3 \
  --height 224 \
  --width 224 \
  --prompt '<image>An image of two cats.<|endofchunk|><image>An image of a sink.<|endofchunk|><image>An image of'
```

If the script exits nonzero, correct the reported shape/token issue before attempting model execution.
