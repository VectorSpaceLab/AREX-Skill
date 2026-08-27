# U-2-Net Model Overview

## When to read

Read this when deciding which U-2-Net architecture to use or when explaining model outputs and checkpoint compatibility.

## Architecture summary

U-2-Net builds a nested U-structure for salient object detection. The main implementation stacks Residual U-blocks (RSU blocks) in an encoder/decoder topology and emits multi-scale side outputs plus one fused output.

Key terms:

- `REBNCONV`: convolution + batch normalization + ReLU building block.
- `RSU7`, `RSU6`, `RSU5`, `RSU4`, `RSU4F`: residual U-blocks with different depths or dilated behavior.
- `U2NET`: full architecture, documented around a 173.6 MB checkpoint.
- `U2NETP`: lightweight architecture, documented around a 4.7 MB checkpoint.
- Side outputs: six intermediate predictions that are upsampled to the first side-output resolution.
- Fused output: a 1x1 convolution over concatenated side outputs, returned first.

## Choosing a model variant

| User goal | Prefer | Reason |
| --- | --- | --- |
| Fast dependency and shape smoke test | `U2NETP(3, 1)` | Smaller model, quick CPU forward. |
| Official full saliency checkpoint `u2net.pth` | `U2NET(3, 1)` | Matches the full-size checkpoint. |
| Official small saliency checkpoint `u2netp.pth` | `U2NETP(3, 1)` | Matches the lightweight checkpoint. |
| Human segmentation checkpoint `u2net_human_seg.pth` | `U2NET(3, 1)` | The repository human script constructs full `U2NET`. |
| Portrait checkpoint `u2net_portrait.pth` | `U2NET(3, 1)` | The portrait scripts construct full `U2NET`. |
| Refactored code exploration | `U2NET_full()` or `U2NET_lite()` | Compact implementation, but checkpoint-key order/names should be verified. |

## Output handling

All official task scripts use the fused first output. For saliency and human segmentation, they save `d0[:, 0, :, :]` after min/max normalization. For portrait generation, they save `1.0 - d0[:, 0, :, :]` after min/max normalization.

Do not average side outputs unless the user explicitly asks for a custom experiment. The repo's normal operating behavior uses the fused output.

## Device behavior

The original scripts use CUDA when available. For portable future-agent guidance:

- Prefer `--device cpu` or `--device auto` in bundled helpers.
- Use `map_location="cpu"` when loading weights on CPU.
- Move the model and input tensors to CUDA only after confirming `torch.cuda.is_available()`.
- Treat CUDA as an optional accelerator for this skill's selected workflows; CPU can validate the model/data plumbing when weights are present.

## Deprecation note

The original `model/u2net.py` uses `torch.nn.functional.upsample`, which modern PyTorch warns is deprecated in favor of `torch.nn.functional.interpolate`. The warning does not by itself mean the model is broken. If a future edit modernizes the code, verify output shapes before changing checkpoint compatibility.
