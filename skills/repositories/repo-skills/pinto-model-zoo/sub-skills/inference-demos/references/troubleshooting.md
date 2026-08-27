# Inference Demo Troubleshooting

Use this reference for failure modes owned by the inference/demo sub-skill.
Do not claim native backend verification unless the concrete selected runtime
and artifacts were actually exercised.

| Symptom | Likely cause | What to do | Route |
| --- | --- | --- | --- |
| `FileNotFoundError` for `.onnx`, `.tflite`, `.xml`, `.bin`, `saved_model`, or `.pb` | Model artifact was not downloaded, path is relative to a different directory, or the script default points at a variant not present locally | Run the classifier, inspect referenced files, then either pass an explicit existing `--model` path or acquire the expected artifact | `../model-acquisition/` for downloads; stay here for run planning |
| Missing `test.png`, `dog.jpg`, `image01.jpg`, labels, anchors, CSV, or masks | Demo assumes sibling fixture/metadata files | Supply a local fixture, update the script argument, or acquire the folder artifacts; keep deterministic fixture files small | `../model-acquisition/` if artifact provenance/download matters |
| `ModuleNotFoundError` or `ImportError` for `tensorflow`, `tflite_runtime`, `onnxruntime`, `openvino`, `cv2`, `PIL`, or `mediapipe` | Optional runtime for the chosen family is absent | Prepare only the selected backend family and shared image/video deps; do not install every framework in the zoo | Stay here for dependency plan; concrete runtime setup happens outside Creator verification |
| `cv2.VideoCapture(0)` returns no frames | Camera device, permission, driver, or CI environment is unavailable | Replace the live source with a fixed image, a pinned short clip, or a saved frame set; only use live camera when the user asks for device proof | Stay here |
| `cv2.imshow`, Qt, X11, Wayland, or display errors | Interactive GUI in headless environment | Use `opencv-python-headless`, remove/guard `imshow`/`waitKey`, and save output images or video files instead | Stay here |
| ONNX Runtime falls back from CUDA/TensorRT to CPU or provider creation fails | GPU/TensorRT provider is unavailable or incompatible | Decide whether CPU smoke testing is acceptable; if GPU is required, prepare the concrete CUDA/TensorRT stack before claiming results | Stay here for plan; hardware proof requires target runtime |
| OpenVINO fails to load `.xml`/`.bin` or complains about device plugin | XML/BIN pair mismatch, wrong working directory, or requested device such as MYRIAD/OpenCL is unavailable | Validate both IR files together and use CPU only if allowed; conversion or pair regeneration is not owned here | `../conversion-and-deployment/` for regeneration |
| TFJS sample cannot be started with Python | It is a browser/WebGL or Node sample, not a Python runtime | Keep `model.json` with all shards, use a static server/browser fixture, and use screenshot or DOM checks instead of Python execution | Stay here for browser inference plan |
| EdgeTPU, Coral, Myriad, Raspberry Pi, or camera-library error | Platform-specific runtime/hardware is absent | Stop, name the missing device/runtime, and ask for a concrete edge environment or choose a CPU/backend substitute | Stay here for stop-gate explanation |
| Script contains `download`, `gdown`, `curl`, `wget`, Google Drive, cookies, or network URLs | The file or prerequisite is doing acquisition work | Do not run it as an inference demo; dry-run and approve acquisition first | `../model-acquisition/` |
| Script contains `TFLiteConverter`, `onnxsim`, `coremltools`, `edgetpu_compiler`, quantization, or export code | The file is conversion/deployment, not a demo run | Stop and classify it as conversion/export before proposing commands | `../conversion-and-deployment/` |
| Output shapes, classes, or boxes are nonsensical | Wrong model variant, wrong pre/postprocessing assumptions, or wrong input layout/color order | Compare script defaults, model filename, input size, color order, and output names; do not call it a backend failure until assets and preprocessing match | Stay here; conversion if artifact mismatch must be rebuilt |

## Minimum safe answer when blocked

When a concrete runtime is missing, say what is known from static inspection and
what must be prepared next. Example: "The script looks like ONNX Runtime with
OpenCV camera/display support, but the model file and provider runtime are not
available here. Acquire the artifact and prepare ONNX Runtime before claiming a
native run."
