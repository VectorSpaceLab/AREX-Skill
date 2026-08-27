# Model Overview

MambaVision is a hybrid Mamba/Transformer hierarchical vision backbone with four feature stages. The classification package exposes factory functions that build an ImageNet-style classifier head by default. All registered factories have pretrained URL metadata; downloads occur only when `pretrained=True` and the requested `model_path` file is absent.

## Model family quick map

| Factory name | Public model family | Default input | Crop pct/mode | Default feature dim | Published top-1 | Published top-5 | Params | FLOPs | Throughput |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `mamba_vision_T` | MambaVision-T-1K | 3x224x224 | 1.00 center | 640 | 82.3 | 96.2 | 31.8M | 4.4G | 6298 img/s |
| `mamba_vision_T2` | MambaVision-T2-1K | 3x224x224 | 0.98 center | 640 | 82.7 | 96.3 | 35.1M | 5.1G | 5990 img/s |
| `mamba_vision_S` | MambaVision-S-1K | 3x224x224 | 0.93 center | 768 | 83.3 | 96.5 | 50.1M | 7.5G | 4700 img/s |
| `mamba_vision_B` | MambaVision-B-1K | 3x224x224 | 1.00 center | 1024 | 84.2 | 96.9 | 97.7M | 15.0G | 3670 img/s |
| `mamba_vision_L` | MambaVision-L-1K | 3x224x224 | 1.00 center | 1568 | 85.0 | 97.1 | 227.9M | 34.9G | 2190 img/s |
| `mamba_vision_L2` | MambaVision-L2-1K | 3x224x224 | 1.00 center | 1568 | 85.3 | 97.2 | 241.5M | 37.5G | 1021 img/s |
| `mamba_vision_B_21k` | MambaVision-B-21K | 3x224x224 | 1.00 center | 1024 | 84.9 | 97.5 | 97.7M | 15.0G | not listed |
| `mamba_vision_L_21k` | MambaVision-L-21K | 3x224x224 | 1.00 center | 1568 | 86.1 | 97.9 | 227.9M | 34.9G | not listed |
| `mamba_vision_L2_512_21k` | MambaVision-L2-512-21K | 3x512x512 | 0.93 squash | 1568 | 87.3 | 98.4 | 241.5M | 196.3G | not listed |
| `mamba_vision_L3_256_21k` | MambaVision-L3-256-21K | 3x256x256 | 1.00 center | 2048 | 87.3 | 98.3 | 739.6M | 122.3G | not listed |
| `mamba_vision_L3_512_21k` | MambaVision-L3-512-21K | 3x512x512 | 0.93 squash | 2048 | 88.1 | 98.6 | 739.6M | 489.1G | not listed |

Notes:

- Published top-1/top-5, params, FLOPs, and throughput are README result-table values and are not revalidated by the bundled helpers.
- Throughput depends strongly on GPU model, batch size, resolution, precision, channels-last layout, and CUDA stack. Use the bundled benchmark helper for local measurement.
- `L3` variants are very large; prefer `T` for smoke tests and debugging.

## Factory architecture defaults

These defaults are taken from the factory functions. Override only when you understand checkpoint compatibility implications.

| Factory | Depths | Heads | Window sizes | Base dim | In dim | Factory resolution | Drop path | Layer scale |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `mamba_vision_T` | `[1, 3, 8, 4]` | `[2, 4, 8, 16]` | `[8, 8, 14, 7]` | 80 | 32 | 224 | 0.2 | default |
| `mamba_vision_T2` | `[1, 3, 11, 4]` | `[2, 4, 8, 16]` | `[8, 8, 14, 7]` | 80 | 32 | 224 | 0.2 | default |
| `mamba_vision_S` | `[3, 3, 7, 5]` | `[2, 4, 8, 16]` | `[8, 8, 14, 7]` | 96 | 64 | 224 | 0.2 | default |
| `mamba_vision_B` | `[3, 3, 10, 5]` | `[2, 4, 8, 16]` | `[8, 8, 14, 7]` | 128 | 64 | 224 | 0.3 | `1e-5` |
| `mamba_vision_B_21k` | `[3, 3, 10, 5]` | `[2, 4, 8, 16]` | `[8, 8, 14, 7]` | 128 | 64 | 224 | 0.3 | `1e-5` |
| `mamba_vision_L` | `[3, 3, 10, 5]` | `[4, 8, 16, 32]` | `[8, 8, 14, 7]` | 196 | 64 | 224 | 0.3 | `1e-5` |
| `mamba_vision_L_21k` | `[3, 3, 10, 5]` | `[4, 8, 16, 32]` | `[8, 8, 14, 7]` | 196 | 64 | 224 | 0.3 | `1e-5` |
| `mamba_vision_L2` | `[3, 3, 12, 5]` | `[4, 8, 16, 32]` | `[8, 8, 14, 7]` | 196 | 64 | 224 | 0.3 | `1e-5` |
| `mamba_vision_L2_512_21k` | `[3, 3, 12, 5]` | `[4, 8, 16, 32]` | `[8, 8, 32, 16]` | 196 | 64 | 512 | 0.3 | `1e-5` |
| `mamba_vision_L3_256_21k` | `[3, 3, 20, 10]` | `[4, 8, 16, 32]` | `[8, 8, 16, 8]` | 256 | 64 | 256 | 0.5 | `1e-5` |
| `mamba_vision_L3_512_21k` | `[3, 3, 20, 10]` | `[4, 8, 16, 32]` | `[8, 8, 32, 16]` | 256 | 64 | 512 | 0.5 | `1e-5` |

The final classifier feature dimension is `base dim * 8` because the hierarchy doubles channels over four stages.

## Checkpoint families and model IDs

Use these model IDs when using the Hugging Face Transformers recipe, or when mapping a factory to the pretrained checkpoint family:

| Factory | Hugging Face model ID | Expected checkpoint filename family |
| --- | --- | --- |
| `mamba_vision_T` | `nvidia/MambaVision-T-1K` | `mambavision_tiny_1k.pth.tar` |
| `mamba_vision_T2` | `nvidia/MambaVision-T2-1K` | `mambavision_tiny2_1k.pth.tar` |
| `mamba_vision_S` | `nvidia/MambaVision-S-1K` | `mambavision_small_1k.pth.tar` |
| `mamba_vision_B` | `nvidia/MambaVision-B-1K` | `mambavision_base_1k.pth.tar` |
| `mamba_vision_B_21k` | `nvidia/MambaVision-B-21K` | `mambavision_base_21k.pth.tar` |
| `mamba_vision_L` | `nvidia/MambaVision-L-1K` | `mambavision_large_1k.pth.tar` |
| `mamba_vision_L_21k` | `nvidia/MambaVision-L-21K` | `mambavision_large_21k.pth.tar` |
| `mamba_vision_L2` | `nvidia/MambaVision-L2-1K` | `mambavision_large2_1k.pth.tar` |
| `mamba_vision_L2_512_21k` | `nvidia/MambaVision-L2-512-21K` | `mambavision_L2_21k_240m_512.pth.tar` |
| `mamba_vision_L3_256_21k` | `nvidia/MambaVision-L3-256-21K` | `mambavision_L3_21k_740m_256.pth.tar` |
| `mamba_vision_L3_512_21k` | `nvidia/MambaVision-L3-512-21K` | `mambavision_L3_21k_740m_512.pth.tar` |

For package API downloads, pass an explicit relative `model_path`, for example:

```python
model = create_model(
    "mamba_vision_T",
    pretrained=True,
    model_path="./checkpoints/mambavision_tiny_1k.pth.tar",
)
```

If the file already exists, it is loaded. If it is missing, `torch.hub.download_url_to_file` attempts to download the factory default URL.

## Input size and arbitrary resolution

Default configs specify model-preprocessing recommendations, not a hard input-size limit. Inference accepts arbitrary height and width because transformer-window stages pad to a multiple of their window size and crop the padded output back after attention.

Practical guidance:

- Use 3-channel RGB tensors shaped `[B, 3, H, W]`.
- Use `create_transform` from `timm` for real image classification so mean/std/crop behavior follows the model config.
- For no-download finite-output tests, random tensors are sufficient.
- For meaningful accuracy, use the model's published resolution and preprocessing; arbitrary-resolution support does not imply the published top-1 number applies at every size.
- Non-3-channel inputs require `in_chans` overrides and usually cannot use pretrained weights without adapting the first layer.

## When to pick each family

- Use `mamba_vision_T` for import checks, smoke tests, small examples, and initial debugging.
- Use `mamba_vision_T2` or `mamba_vision_S` when the user wants a moderately stronger 1K model without the larger memory footprint of B/L families.
- Use `mamba_vision_B`, `mamba_vision_L`, or `mamba_vision_L2` when the user asks for the published higher-accuracy 1K checkpoints and has adequate GPU memory.
- Use `*_21k` variants when the user explicitly asks for the 21K-pretrained families or the corresponding published result table. They are not a substitute for detection or segmentation adapters; route those downstream workflows to their sibling sub-skills.
- Avoid L3 as a default recommendation for smoke tests because it has hundreds of millions of parameters.
