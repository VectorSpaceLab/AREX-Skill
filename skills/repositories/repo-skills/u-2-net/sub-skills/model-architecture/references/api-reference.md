# Model Architecture API Reference

## Purpose

Use this reference for verified constructor names, forward-output shapes, and checkpoint-loading decisions. It distills the repository's model files into runtime guidance so future agents do not need to inspect source files for ordinary tasks.

## Original architecture module

The root `model` package exposes two original classes:

| API | Constructor | Typical use | Forward result |
| --- | --- | --- | --- |
| `model.U2NET` | `U2NET(in_ch=3, out_ch=1)` | Full saliency model, human segmentation, portrait generation. | Tuple of seven sigmoid tensors. |
| `model.U2NETP` | `U2NETP(in_ch=3, out_ch=1)` | Lightweight saliency model and fast CPU smoke tests. | Tuple of seven sigmoid tensors. |

For an input tensor shaped `(N, 3, H, W)` and `out_ch=1`, both original classes return `(d0, d1, d2, d3, d4, d5, d6)` where every tensor is shaped `(N, 1, H, W)`. `d0` is the fused output and the remaining outputs are side predictions. The official inference scripts use `d0[:, 0, :, :]`, normalize it, resize it to the original image size, and save a PNG mask.

## Refactored architecture module

`model.u2net_refactor` defines:

| API | Constructor | Notes |
| --- | --- | --- |
| `U2NET_full()` | no arguments | Builds a full-size refactored architecture. |
| `U2NET_lite()` | no arguments | Builds a lightweight refactored architecture. |

The refactored builders return a list of seven sigmoid maps. Their module names and internal registration order differ from the original implementation; do not assume an original checkpoint can be loaded into the refactored model without checking state-dict keys.

## Safe checkpoint-loading pattern

For normal operations, prefer the bundled helpers because they already select the correct model and load checkpoints with CPU-safe `map_location`. When adapting code in a user-supplied U-2-Net checkout, preserve these rules:

- instantiate the architecture that matches the checkpoint (`U2NET(3,1)` or `U2NETP(3,1)`);
- load checkpoints with `map_location="cpu"` before moving to CUDA;
- unwrap `state_dict` or `model_state_dict` containers when present;
- strip a leading `module.` prefix from DataParallel checkpoints;
- call `eval()` before inference.

Move to CUDA only after load succeeds and only when `torch.cuda.is_available()` is true.

## Bundled smoke script contract

`scripts/smoke_architecture.py` accepts:

- `--model {u2net,u2netp,refactor-full,refactor-lite}`
- `--height INT` and `--width INT`
- `--device {auto,cpu,cuda}`

It uses bundled original or refactored model implementations and does not load weights. A successful result should report `output_count: 7`; each output shape should match the input height and width for arbitrary positive dimensions.

## What this reference deliberately excludes

- Image-folder inference commands live in `salient-object-inference`.
- Portrait face-crop and composite commands live in `portrait-workflows`.
- Dataset transforms and training-loop APIs live in `data-and-training`.
