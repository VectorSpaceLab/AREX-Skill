# Troubleshooting

Use this guide after the asset checker or one of the inference recipes fails.

## Quick triage order

1. Run [`../scripts/check_photo2cartoon_assets.py`](../scripts/check_photo2cartoon_assets.py).
2. Confirm the input is a portrait face crop, not a raw full-body image.
3. Confirm the device or provider matches the installed runtime.
4. Confirm the output image is being written to an explicit, writable path.

## Common failures

| Symptom | Likely cause | What to check | Fix |
| --- | --- | --- | --- |
| missing asset | checkpoint or segmentation file not present | run the asset checker and inspect the resolved path | pass explicit paths or place the required assets where the recipe expects them |
| `can not detect face!!!` | preprocessing could not find a usable face | image too small, off-angle, occluded, or not a portrait crop | use the preprocessing flow first; choose a larger, more frontal face, preferably with a face bigger than about 200x200 pixels |
| color shift or blue/red swap | BGR/RGB mismatch | inspect the decode and save path used by the caller | keep RGB for model input and only convert to BGR when using OpenCV save APIs |
| ONNX input mismatch | graph name does not match the expected contract | inspect `session.get_inputs()` and `session.get_outputs()` | use `input`/`output` or override the names explicitly |
| ONNX provider failure | requested provider not available | inspect `onnxruntime.get_available_providers()` | fall back to `CPUExecutionProvider` or install the matching runtime build |
| CUDA vs CPU checkpoint load issue | checkpoint loaded on the wrong device | inspect the device and `map_location` | use `torch.load(..., map_location=device)` and let `auto` choose CPU when needed |
| segmentation dependency failure | `seg_model_384.pb` missing or TensorFlow stack absent | confirm the file exists and the runtime can import TensorFlow | install the required preprocessing dependencies or use an environment that already has them |

## Specific notes

### No face detected

The inference recipes treat no-face detection as an upstream problem. The usual causes are:

- portrait is too small
- portrait is not frontal enough
- face is partially occluded
- preprocessing did not complete

Do not debug this by changing the generator weights. Start with the preprocessing flow and the sample-image constraints.

### OpenCV channel order mistakes

The historical source flow reads with `cv2.imread`, converts to RGB, and converts back only when saving through OpenCV. If you use a different image library, keep the same contract:

- model input: RGB
- model output: RGB before save
- OpenCV save: BGR array

### Segmentation graph failure

The segmentation graph is expected to expose `input_1:0` and `sigmoid/Sigmoid:0`.
If TensorFlow is missing, the graph may still be present on disk but cannot be loaded.
That is a runtime dependency problem, not a model-quality problem.

### Torch checkpoint on CPU

If the checkpoint was saved on GPU and you are loading on CPU, always map it to the current device. The source recipe uses `map_location=device` for this reason.
