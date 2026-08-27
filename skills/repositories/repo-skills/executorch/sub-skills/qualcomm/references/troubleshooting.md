# Qualcomm Troubleshooting

## SDK and Build Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `QNN_SDK_ROOT` not found | SDK not installed or env var missing | Ask user for SDK location; do not download or accept SDK terms silently. |
| Android build cannot find NDK | `ANDROID_NDK_ROOT`/`ANDROID_NDK` missing or wrong version | Point to the installed NDK and rebuild only the selected QNN target. |
| Python imports fail for QNN manager/adaptor | x86 host QNN pieces were not built/copied or library path is missing | Build x86 interface and set runtime library path for SDK/build libs. |
| Device test cannot connect | Wrong serial/host/ADB state | Verify `adb devices`, host forwarding, and device authorization outside model logic. |

## Intermediate-Output Debugging

Use QNN-specific intermediate-output debugging when the final QNN output diverges from CPU/eager output. The goal is to identify the first problematic partition/layer, not to tune tolerances blindly.

Suggested triage:

1. Reproduce with fixed seeds and a tiny representative input.
2. Save CPU/eager output and QNN output at the same logical stage.
3. Enable QNN intermediate-output capture or generate a debug script from the existing export example.
4. Compare per-layer outputs with a QNN numerical comparator.
5. If divergence starts before delegation, route back to `export-runtime`; if it starts inside QNN partition, inspect compile specs, quantization, op support, and input layout.

## Accuracy and Fallback

- FP16 and quantized QNN paths have different tolerance expectations.
- Fallback nodes can hide unsupported ops and produce mixed CPU/QNN execution; inspect fallback markers before profiling.
- For LLMs, verify tokenizer/model-asset identity before attributing text differences to the backend.

