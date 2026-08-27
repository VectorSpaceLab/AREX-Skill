---
name: nas-search
description: "Routes AutoFormer, AutoFormerV2/S3, Cream, and CDARTS
  architecture-search, retrain, test, and sampled-ImageNet workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# NAS Search

Use this sub-skill when the user wants to search, retrain, evaluate, or debug one of the monorepo's architecture-search families:
AutoFormer, AutoFormerV2/S3, Cream, or CDARTS.

## What this route owns

- AutoFormer supernet training, evolution search, and evaluation.
- AutoFormerV2 / S3 evaluation from searched-space configs.
- Cream search, retrain, test, and subImageNet generation.
- CDARTS search, retrain, test, and the more advanced benchmark201 / detection / segmentation branches.

## When to use it

Choose this route for prompts like:

- "search an AutoFormer architecture"
- "run Cream retraining"
- "evaluate S3 / AutoFormerV2"
- "fix CDARTS search config"
- "generate subImageNet"
- "compare NAS commands for these repos"

## What to read next

- `references/workflows.md` for command shapes, config-file ownership, and which project uses which launcher.
- `references/troubleshooting.md` for legacy-torch, Apex, dataset-layout, and distributed-launch failures.
- `scripts/build_nas_command.py` to print safe command templates instead of launching a training job.
- `../../scripts/check_legacy_imports.py` for the modern-torch compatibility shim used by legacy search code.
- `../../scripts/check_dataset_layout.py` when the failure looks like a missing ImageNet, subImageNet, or COCO layout.

## Important boundaries

- Do not route EfficientViT, MiniViT, TinyCLIP, TinyViT, or iRPE here.
- Treat `Cream/tools/generate_subImageNet.py` and `AutoFormer/lib/subImageNet.py` as reference evidence only; they mutate data and copy files, so the bundled skill uses read-only layout checks plus command templates instead.
- Treat CDARTS benchmark201 as an advanced optional path because it expects extra historical dependencies such as Apex and the NAS-Bench-201 API.

## Working pattern

1. Identify the project family and the exact mode: train, search, retrain, test, or eval.
2. Read the workflow reference for the canonical command shape and the required config/data/checkpoint fields.
3. Run the bundled layout or compatibility checker if the error involves dataset paths, old torch imports, or legacy optional dependencies.
4. Use the command-builder script to produce the exact launcher string and then adapt it to the user's environment.

## Common signals

- `torch._six` errors usually mean the legacy NAS code is being imported under modern torch.
- `apex` errors usually mean the request is trying to use the optional CDARTS benchmark201 path.
- `FileNotFoundError` on `imagenet/train`, `imagenet/val`, `subImageNet`, or `coco` usually means the data layout is wrong.
- Import-time parser errors usually mean the user tried to call the project script without the required mode/config arguments.
