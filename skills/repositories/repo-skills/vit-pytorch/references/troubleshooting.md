# vit-pytorch Troubleshooting

## Purpose

Use this cross-cutting guide for package installation, import failures, optional dependency gaps, backend expectations, and version-fragile workflows. For detailed model-family, shape, or wrapper issues, read the nearest sub-skill troubleshooting reference.

## Start with the bundled install check

```bash
python scripts/check_vit_pytorch_install.py --run-smoke
```

That helper verifies metadata, key imports, and tiny CPU forward checks without downloads.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'vit_pytorch'` | The package is not installed in the active Python environment. | Install `vit-pytorch` into the environment the user actually runs. Re-run the bundled install check. |
| `ModuleNotFoundError` for `torch` or `einops` | Base runtime dependency missing or mismatched. | Reinstall the package with its runtime dependencies. Avoid testing against a different interpreter than the one that will run the skill. |
| `No module named 'torchaudio'` when importing VAAT | Optional audio dependency missing. | Treat VAAT as optional until `torchaudio` is installed; see the pretraining/adaptation sub-skill for audio-specific notes. |
| `No module named 'torchvision'` in DINO, EsViT, LeJEPA, or dataset recipes | Optional vision dependency missing or incompatible. | Install a `torch`/`torchvision` pair that matches the runtime and retry the helper with identity augmentations before attempting full training. |
| `No module named 'nystrom_attention'` or `x_transformers` | External research-idea dependency is absent. | Keep the custom transformer contract test with a local token-preserving stub; install the external package only if the user explicitly needs it. |

## Backend and performance expectations

- The base package is fully usable on CPU for constructor, forward, wrapper, and tiny loss smoke checks.
- CUDA is available in the verified environment, but no selected capability in this skill requires a CUDA-only runtime to prove functional behavior.
- `simple_flash_attn_vit` and `simple_flash_attn_vit_3d` use PyTorch's scaled-dot-product attention path when flash mode is enabled. On CPU they validate functionally, but they do not prove GPU flash performance.
- If a user asks specifically about CUDA speedups, flash kernels, or other hardware performance behavior, direct them to the relevant sub-skill plus the user's own runtime/backend checks.

## Version-fragile wrapper warnings

The current installed snapshot exposes live pitfalls that future agents must not hide:

- `MAE` and `SimMIM` are sensitive to the current base ViT positional-embedding layout and currently fail tiny smoke checks with a tensor-size mismatch.
- `MPP` is sensitive to the current base ViT token/class-token expectations and currently fails a tiny smoke check around its repeat pattern.
- These are compatibility problems, not user input mistakes. If the helper reports them again, document the exact limitation instead of claiming verified support.

## General repair sequence

1. Confirm the target workflow and route to the right sub-skill.
2. Run the bundled install check or the nearest smoke helper.
3. Reduce the model to a tiny constructor and random tensor until the shape works.
4. Restore one dimension or one optional feature at a time.
5. If a wrapper is version-fragile, keep the limitation visible and avoid running long training recipes until the smoke passes.

## When to stop

Stop and ask for more information when the task needs pretrained checkpoints, network downloads, benchmark-scale data, or a missing hardware backend that the selected workflow truly requires. Do not convert those requirements into silent skips.
