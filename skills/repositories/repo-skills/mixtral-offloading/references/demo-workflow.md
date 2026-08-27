# Demo workflow overview

The public demo demonstrates Mixtral-8x7B-Instruct inference on a CUDA GPU with
mixed HQQ quantization and per-expert offloading. The workflow is useful
evidence, but the generated skill distills it into scripts and references so a
future agent does not need to reopen the original notebook.

## What the demo does

1. Installs runtime requirements and downloads a quantized Mixtral offloading
   state directory.
2. Imports PyTorch, HQQ, Transformers, the repo's `src.build_model` APIs, and
   notebook display helpers.
3. Loads a config for the quantized state.
4. Chooses CUDA device `cuda:0`.
5. Builds an `OffloadConfig` from layer/expert counts and `offload_per_layer`.
6. Creates separate HQQ configs for attention and FFN expert weights.
7. Calls `build_model` with the quantized state path.
8. Runs an interactive chat loop using a tokenizer, `TextStreamer`, sampling,
   and cached `past_key_values`.

## Resource notes preserved from the demo

- The notebook says approximately 16 GB GPU VRAM and 11 GB RAM are needed for
  somewhat long generations.
- `offload_per_layer=4` is the normal Colab setting.
- `offload_per_layer=5` is suggested for lower-VRAM runs around 12 GB, with a
  speed trade-off.

## Differences from a production script

The notebook uses Colab shell commands, clones the repo, installs requirements,
downloads model artifacts, and enters an infinite interactive loop. A safer
script should separate these phases:

- Environment setup and dependency verification.
- Explicit model artifact acquisition or validation.
- Offload/quantization configuration.
- Model construction.
- One bounded generation call or a controlled application loop.

Use the inference sub-skill's skeleton renderer as the starting point for a
bounded script.
