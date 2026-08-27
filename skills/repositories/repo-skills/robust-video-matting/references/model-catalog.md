# Model Catalog and Runtime Support

## When to read

Read this for a compact overview of RobustVideoMatting model variants, official
artifact formats, backend expectations, and speed caveats shared across
sub-skills.

## Model variants

| Variant | Typical use | Notes |
| --- | --- | --- |
| `mobilenetv3` | Recommended default for most inference and smoke checks. | Smaller, faster, official docs recommend it for most use cases. |
| `resnet50` | Larger model when the user accepts extra compute for modest quality improvement. | Use matching ResNet50 checkpoints/artifacts. |

Both variants use the `MattingNetwork` API and return foreground, alpha, and
four recurrent states in PyTorch matting mode.

## Official artifact families

RVM release artifacts include:

- PyTorch `.pth` state dictionaries for MobileNetV3 and ResNet50.
- TorchHub model factories and converter function.
- TorchScript FP32/FP16 artifacts.
- ONNX FP32/FP16 artifacts, tested by the project with ONNX Runtime CPU and
  CUDA backends.
- TensorFlow 2 SavedModel ZIPs.
- TensorFlow.js int8 artifact for web use.
- CoreML fixed-resolution FP16/int8 MobileNetV3 artifacts.

Generated helper scripts in this skill avoid downloads. Use explicit local
artifact paths in automation, or call TorchHub only when network/cache behavior
is acceptable.

## Backend expectations

- CPU is sufficient for API import, shape validation, tiny image-sequence
  conversion, dataset layout validation, and tiny LR metric checks.
- CUDA is important for realistic high-resolution throughput, HR evaluator use,
  and full training. Do not infer GPU speed from CPU checks.
- PyAV/PIMS/FFmpeg-like media support matters for video file IO. PNG sequence
  workflows are simpler to validate.
- CoreML and TensorFlow.js workflows require their respective runtime stacks and
  deployment-specific input handling.

## Speed notes

The README speed table reports tensor throughput, not full end-to-end video
conversion. It uses synthetic tensors, CUDA, specific dtypes, and documented
resolution/downsample settings. The Python converter also performs media IO and
will usually be slower.

When reporting speed, include:

- variant (`mobilenetv3` or `resnet50`),
- device and dtype,
- resolution and downsample ratio,
- whether the measurement includes media decode/encode,
- sequence chunk/batch behavior,
- warmup and iteration count.
