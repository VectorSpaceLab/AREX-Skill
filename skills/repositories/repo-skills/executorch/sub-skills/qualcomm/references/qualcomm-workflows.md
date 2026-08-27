# Qualcomm QNN Workflows

## Build and Environment

Required inputs for most QNN workflows:

- `QNN_SDK_ROOT`: Qualcomm AI Engine Direct / QNN SDK root.
- `ANDROID_NDK_ROOT` or `ANDROID_NDK`: Android NDK for Android arm64 builds.
- Target SoC model, such as `SM8750` or another supported value from the user's device context.
- Build directory for Android runner artifacts, commonly a `build-android` style output.
- Optional device serial and host forwarding parameters when running tests on Android.

Common build modes:

| Mode | Use |
| --- | --- |
| Full x86 + Android | Build host Python/interface pieces and Android runner artifacts. |
| x86 only | Faster local compile/export validation when device execution is not needed. |
| Android only | Device runner path when host artifacts are already prepared. |
| Direct/Hexagon/OE Linux | Specialized modes requiring additional SDK/toolchain variables. |

## Export, Lowering, and Quantization

The QNN path uses QNN partitioning/compile specs after a PyTorch export/EXIR lowering setup. Quantization is usually backend-specific; confirm the quantization recipe and dtype before lowering. If a model uses custom ops or unsupported nodes, identify fallback regions before blaming runtime execution.

## Testing

A typical QNN native test needs QNN SDK libraries, an Android build dir, SoC model, and optionally device serial/host. Use compile-only or x86 modes to separate export/compile failures from device runtime failures when possible.

## Model Enablement Checklist

1. Prove model exports without QNN.
2. Add QNN partitioning and inspect unsupported/fallback nodes.
3. Quantize with QNN-compatible settings if required.
4. Compile in the least device-dependent mode first.
5. Run on target device only after SDK, ABI, build artifacts, and input fixtures are known.
6. For LLMs, route through `llm-workflows` first to ensure tokenizer, weights, KV cache, and runner assumptions are explicit.

