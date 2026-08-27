---
name: model-assets-and-runtime
description: "Set up and inspect min(DALL·E) model assets, tokenizer, model
  variants, runtime device/dtype decisions, and internal shapes without
  unnecessary downloads."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# model-assets-and-runtime

Use this sub-skill when the task is about min(DALL·E) model weight caches, tokenizer assets, model variant sizing, device/dtype choices, memory/runtime setup, or internal tensor shapes. The goal is to inspect and prepare safely before running expensive generation.

## Fast routing

- For cache layout, download side effects, Hugging Face asset names, `is_mega` constants, dtype/device choices, and no-download preflight checks, read [references/runtime-and-assets.md](references/runtime-and-assets.md).
- For tokenizer normalization, BPE behavior, special tokens, 64-token text limit, 256 image-token loop, decoder sampling, and VQGAN detokenizer shapes, read [references/tokenizer-and-model-internals.md](references/tokenizer-and-model-internals.md).
- For failed downloads, corrupt cache files, CUDA/CPU dtype surprises, OOM, SSL/proxy problems, and tokenizer surprises, read [references/troubleshooting.md](references/troubleshooting.md).
- For a deterministic no-network tokenizer check, run [scripts/tokenizer_smoke.py](scripts/tokenizer_smoke.py). It uses a synthetic vocabulary and does not instantiate `MinDalle` or load model weights.

## Route out of this sub-skill

- User-facing text-to-image generation recipes, `MinDalle.generate_image*` usage, stream consumption, seed/top-k/temperature recipe choices, and saving generated PIL/tensor outputs belong in `../text-to-image-generation/SKILL.md`.
- Command-line usage, Replicate/Cog, Tkinter, Colab/notebook, and public interface behavior belong in `../deployment-and-interfaces/SKILL.md`.
- Architecture modification, training, conversion from upstream Flax/JAX weights, and benchmarking beyond lightweight preflight are out of scope for this generated repo skill.

## Operating rules

1. Prefer no-download inspection first: examine the chosen `models_root` layout and run the tokenizer smoke script before constructing a full `MinDalle` object.
2. Treat `MinDalle(...)` construction as potentially network- and memory-active. Even tokenizer initialization can contact the Hugging Face asset endpoint; `is_reusable=True` can download and load all major `.pt` weights.
3. Do not load `.pt` files just to prove that a cache path exists. Check existence, non-zero size, and obvious partial-download symptoms first; only load weights when the user approved full runtime setup.
4. Choose `device`, `dtype`, `is_mega`, and `is_reusable` from the user's hardware and budget rather than from examples copied blindly.
5. Keep runtime instructions self-contained in this sub-skill; the original repository checkout is not required for routine setup or debugging.
