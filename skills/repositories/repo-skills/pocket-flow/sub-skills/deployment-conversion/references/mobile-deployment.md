# Mobile Deployment Notes

Read this after a PocketFlow checkpoint has been exported to a `.tflite` file.

## Output expectations

A successful export typically leaves generated files in the chosen model directory, including a frozen PB and a `.tflite` model. The exact filename depends on the conversion utility and flags, but the tutorial flow uses a transformed TFLite file for deployment.

## Android adaptation steps

PocketFlow's tutorial describes adapting a TensorFlow Lite camera demo:

1. Put the generated `.tflite` model in the Android app assets.
2. Provide the matching label file.
3. Create or adapt an image classifier class for the model's input size, channel normalization, byte depth, and output shape.
4. Replace the app's classifier construction to use the new class.

For ResNet-style float models, the tutorial uses ImageNet channel means roughly:

- Red: `123.58`
- Green: `116.779`
- Blue: `103.939`

For quantized models, use the quantized model's expected input dtype and scale assumptions instead of float preprocessing.

## What to verify before mobile handoff

- TFLite interpreter can load the model on the target platform.
- Input tensor shape and dtype match the Android preprocessing code.
- Output label count matches the label file.
- Any quantization parameters expected by the model are respected.
- The deployment app is using the converted compressed/quantized artifact, not an old baseline model.

## Common mobile-specific pitfalls

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| App crashes on model load | TFLite ops unsupported by device/runtime. | Try a newer TFLite runtime, simplify/export graph differently, or avoid unsupported ops. |
| Predictions are nonsensical | Preprocessing mean/std, input dtype, or label order mismatch. | Compare a known image through the PB/TFLite model and Android preprocessing. |
| Quantized model slower than expected | Model not fully quantized, device lacks optimized kernels, or batch/input shape differs. | Inspect quantization flags and benchmark on the actual device. |
| Output dimension mismatch | Wrong label file or final classifier class count. | Match `nb_classes`, labels, and model output tensor. |

Mobile app building, device connection, and Java/Kotlin project changes are outside the bundled scripts. Treat them as downstream application work once the model artifact is validated.
