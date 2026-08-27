# Cross-Cutting Troubleshooting

## Purpose

Read this first when a Cream-family workflow fails before you know which project-specific subskill owns the issue.

## Common failure patterns

### `ModuleNotFoundError: torch._six`

- **Seen in:** AutoFormer, Cream, and CDARTS legacy code under modern torch.
- **Likely cause:** The original scripts target older torch releases where `torch._six` existed.
- **Next step:** Use `../scripts/check_legacy_imports.py` to confirm the compatibility shim path, or move the workflow to a historical torch environment if you need the exact original training path.
- **Stop when:** The workflow requires a strict historical runtime and the user has not authorized a compatibility shim or legacy environment.

### `ModuleNotFoundError: apex`

- **Seen in:** CDARTS benchmark201 and some optional mixed-precision paths.
- **Likely cause:** The repo expects NVIDIA Apex for a faster or older distributed path.
- **Next step:** Treat Apex as optional unless the specific workflow says otherwise. If the command path is benchmark201 or another Apex-only route, install the missing dependency in a matching CUDA environment or use the non-Apex branch if documented.

### `FileNotFoundError` for ImageNet or COCO paths

- **Seen in:** AutoFormer, Cream, EfficientViT, MiniViT, TinyCLIP, TinyViT, and iRPE.
- **Likely cause:** The dataset layout does not match the expected folder, tar, or sampled-subset structure.
- **Next step:** Run `../scripts/check_dataset_layout.py` against the intended dataset root before retrying.

### `rpe_ops` warning or missing compiled extension

- **Seen in:** MiniViT and iRPE.
- **Likely cause:** The optional C++/CUDA extension has not been built.
- **Next step:** Continue with the Python fallback for inspection, or build the extension only if you need the accelerated path.

### `dist_*` / `torch.distributed.launch` failures

- **Seen in:** Most training and evaluation scripts.
- **Likely cause:** Missing distributed backend setup, wrong GPU count, or a command that was copied without its config and data paths.
- **Next step:** Verify the command with the bundled reference for the relevant subskill, then run a smaller import or help check before scaling up.

### Missing checkpoints or model-zoo files

- **Seen in:** TinyCLIP, TinyViT, EfficientViT, MiniViT, iRPE, and some NAS evaluation paths.
- **Likely cause:** The workflow assumes a public checkpoint or a downloaded model zoo artifact.
- **Next step:** Confirm the checkpoint name in the subskill reference and keep the repo skill self-contained by pointing to the user-provided path, not the original checkout.

## Use the bundled helpers

- `../scripts/check_environment.py` for importability and CUDA visibility.
- `../scripts/check_dataset_layout.py` for data root validation.
- `../scripts/check_custom_ops.py` for optional compiled extension status.
- `../scripts/check_legacy_imports.py` for the legacy NAS import path under modern torch.
