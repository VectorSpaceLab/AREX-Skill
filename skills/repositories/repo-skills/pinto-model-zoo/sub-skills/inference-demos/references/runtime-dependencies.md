# Runtime Dependencies

Use this sheet to explain which concrete runtime a PINTO_model_zoo demo is
asking for. Treat package names as family-level guidance only; exact versions
belong to the selected model folder, script, and target machine.

## Shared preflight

Most Python demos combine one inference backend with `numpy` and an image/video
wrapper such as OpenCV or Pillow. For CI, prefer a file-output or headless plan
before installing GUI stacks or touching a camera.

## Backend and support families

| Family | Common clues | Typical runtime pieces | Preflight before execution | Stop when |
| --- | --- | --- | --- | --- |
| TensorFlow / TFLite | `tensorflow`, `tf.lite.Interpreter`, `tflite_runtime`, `.tflite`, `saved_model`, `.pb`, `.h5` | `tensorflow` when the script uses TensorFlow ops; `tflite-runtime` only when the script just loads `.tflite`; often `numpy`, OpenCV, Pillow | Model path exists, input dtype/shape is known, delegate/hardware flags are intentional | Model missing, import missing, or EdgeTPU/delegate hardware is not available |
| ONNX Runtime | `onnxruntime`, `InferenceSession`, `.onnx`, provider names such as `CPUExecutionProvider`, `CUDAExecutionProvider`, `TensorrtExecutionProvider` | `onnxruntime` for CPU; `onnxruntime-gpu` only when GPU providers are required; usually `numpy` and OpenCV/Pillow | Model path exists, provider list matches the target host, output names/shapes are understood | Script asks for CUDA/TensorRT but the machine only has CPU, or the model path is absent |
| OpenVINO | `openvino.runtime`, `openvino.inference_engine`, `IECore`, `.xml`/`.bin`, `readNetFromModelOptimizer`, `DNN_BACKEND_INFERENCE_ENGINE` | `openvino` runtime or an OpenCV build with Inference Engine support; `numpy`, OpenCV | XML and BIN are a matching pair, device string is valid, MYRIAD/OpenCL targets are intentional | `.xml` and `.bin` mismatch, device plugin is absent, or OpenVINO is not installed |
| TFJS / browser | `tfjs`, `model.json`, shard `.bin` files, `browser`, `webgl`, canvas or DOM terms | Browser plus a static file server; Node or `tfjs-node` only if the sample is written for it | `model.json` and all shard files stay together, CORS/static paths work, camera permissions are allowed if needed | Trying to execute browser samples as Python, or model shards are missing |
| Camera / OpenCV | `cv2`, `VideoCapture`, `imshow`, `waitKey`, `VideoWriter`, `imread`, `imwrite` | `opencv-python` for interactive GUI; `opencv-python-headless` for CI file-output plans | Input source exists: camera device, image, or clip; display availability is known | Headless CI lacks GUI, camera is absent, or script has no file-input path |
| Raspberry Pi / edge | `Raspberry Pi`, `aarch64`, `armv7l`, `libcamera`, `picamera`, `libedgetpu`, `EdgeTPU`, `Coral`, `MYRIAD` | The selected backend plus platform packages such as camera libraries, EdgeTPU runtime, or OpenVINO/Myriad support | OS architecture, device permissions, USB accelerator, and camera are concrete | User expects proof without the physical device or matching OS/runtime |
| MediaPipe wrapper | `mediapipe`, model names from MediaPipe face/hand/pose/objectron families | Usually TFLite, OpenCV/camera, or browser layers around a MediaPipe-style graph | Decide whether this is a Python, C++/OpenGL, or browser sample | The selected sample is not Python-runnable in the current host |

## Other format variants

CoreML, TF-TRT, and EdgeTPU artifacts also appear in the zoo. Treat them as
backend-specific deployment variants: they require the matching platform,
compiler/runtime, and hardware before any execution claim. If the user asks to
create or convert such an artifact, hand off to `../conversion-and-deployment/`.

## Dependency planning rules

- Install only the selected backend family, not the whole zoo's dependency set.
- If a script uses `cv2.dnn.readNetFromONNX` or similar without importing `onnxruntime`, plan for OpenCV DNN rather than ONNX Runtime.
- An import failure is a missing runtime clue, not evidence that the model is bad.
- A catalog flag means the format exists in the zoo, not that a shallow checkout
  already contains the file.
- A successful helper classification is not native backend verification.
- If the script uses a camera or display, prefer a fixture plan before live I/O.
