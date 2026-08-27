---
name: min-dalle
description: "Use the min(DALL·E) Python package for text-to-image generation,
  model asset/runtime setup, CLI-style requests, notebook/UI workflows, and
  Replicate/Cog deployment troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# min(DALL·E)

Use this repo skill when a task names `min-dalle`, `min_dalle`, min(DALL·E), DALL·E Mini/Mega inference in PyTorch, or asks for lightweight text-to-image generation code with `MinDalle`. This skill is for operating the package as a library or interface; it is not a training, model-conversion, or upstream Flax/JAX maintenance guide.

## Start safely

Install the public package and verify importability before running any generation that might download weights:

```bash
python -m pip install min-dalle
python - <<'PY'
from min_dalle import MinDalle
print(MinDalle)
PY
```

For a no-download API/backend inspection, run the bundled helper:

```bash
python scripts/inspect_min_dalle_api.py
```

Read [references/troubleshooting.md](references/troubleshooting.md) when installation, imports, PyTorch, Pillow, `emoji`, or model-cache setup fails. Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is stale for a newer checkout.

## Route by task

- Use [sub-skills/text-to-image-generation/SKILL.md](sub-skills/text-to-image-generation/SKILL.md) to write or debug Python `MinDalle` generation calls: `generate_image`, `generate_images`, stream APIs, tensor/PIL conversion, seeds, `grid_size`, `temperature`, `top_k`, `supercondition_factor`, seamless mode, `is_mega`, `is_reusable`, `device`, and `dtype`.
- Use [sub-skills/model-assets-and-runtime/SKILL.md](sub-skills/model-assets-and-runtime/SKILL.md) to plan or troubleshoot `models_root`, tokenizer/weight downloads, cache layout, Mega versus Mini constants, CPU/CUDA/dtype choices, tokenizer normalization, and internal tensor shapes without unnecessary downloads.
- Use [sub-skills/deployment-and-interfaces/SKILL.md](sub-skills/deployment-and-interfaces/SKILL.md) for command-line style requests, the safe CLI template, notebook/Colab progressive display, Tkinter UI behavior, Replicate/Cog predictor inputs, and deployment-specific failures.

## Common choices

- Start with `device="cpu"`, `dtype=torch.float32`, `is_mega=False`, and `grid_size=1` only for the smallest compatibility check; full generation can still be slow and may download model assets.
- Use CUDA for practical Mega generation when available and verified. `dtype=torch.float16` can reduce GPU memory; `torch.bfloat16` is only appropriate on capable hardware such as Ampere-class CUDA.
- Use `is_reusable=True` for repeated prompts when memory permits. Use `is_reusable=False` for one-shot runs under memory pressure.
- Pass `grid_size` as a keyword argument for tensor batch APIs because the implementation reads `kwargs["grid_size"]` while reshaping.

## Bundled scripts

- [scripts/inspect_min_dalle_api.py](scripts/inspect_min_dalle_api.py) prints installed distribution/dependency versions, `MinDalle` signatures, and optional CUDA visibility without constructing a model.
- [sub-skills/text-to-image-generation/scripts/generation_request_template.py](sub-skills/text-to-image-generation/scripts/generation_request_template.py) plans Python API generation calls and requires `--run` before model construction or downloads.
- [sub-skills/model-assets-and-runtime/scripts/tokenizer_smoke.py](sub-skills/model-assets-and-runtime/scripts/tokenizer_smoke.py) checks tokenizer normalization with a synthetic vocabulary and no network.
- [sub-skills/deployment-and-interfaces/scripts/min_dalle_cli_template.py](sub-skills/deployment-and-interfaces/scripts/min_dalle_cli_template.py) is a safe replacement for the repo's CLI-style behavior, defaulting to dry run.
- [sub-skills/deployment-and-interfaces/scripts/replicate_filename_sanitize.py](sub-skills/deployment-and-interfaces/scripts/replicate_filename_sanitize.py) previews Replicate-style output basenames without Cog or model loading.

## Boundaries

This skill intentionally does not bundle model weights, example images, notebooks, or deployment images. Full image generation may require network access to model assets, significant disk space, substantial CPU/GPU memory, and runtime approval. Use the dry-run and inspection helpers before any side-effectful call.
