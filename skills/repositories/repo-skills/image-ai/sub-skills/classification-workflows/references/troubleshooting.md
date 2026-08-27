# Classification Troubleshooting

Use this matrix for ImageAI 3.x classification inference failures.

## Quick triage order

1. Confirm the active Python environment imports `imageai`, `torch`, `torchvision`, `PIL`, and `numpy`.
2. Confirm the model file exists and ends in `.pt` or `.pth`.
3. Confirm the chosen model type matches the weights.
4. In custom mode, confirm `setJsonPath(...)` points to the matching class mapping JSON.
5. Confirm `loadModel()` completed before `classifyImage(...)`.
6. Confirm the image input is a valid file, numpy array, or PIL image.

## Symptoms, causes, and recovery

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: No module named 'torch'` or `No module named 'torchvision'` | ImageAI runtime dependencies are missing from the active environment. | Install ImageAI with its PyTorch/torchvision dependencies in the environment that runs the script. Run a small import check before loading model weights. |
| Torch/torchvision import works in one terminal but helper fails elsewhere | The command is using a different Python interpreter/environment. | Use `python -c "import sys; print(sys.executable)"` in the same shell as the helper command and activate the intended environment. Do not hard-code private environment paths into reusable instructions. |
| RuntimeError says TensorFlow model / ImageAI now uses PyTorch / install ImageAI 2.1.6 or earlier | A `.h5` model was supplied to ImageAI 3.x. | Do not try to force-load `.h5` files. Use `.pt`/`.pth` PyTorch weights for ImageAI 3.x, or recreate the legacy TensorFlow environment with ImageAI 2.1.6 or earlier if the user must use the `.h5` artifact. |
| `Invalid model file ... Please parse in a '.pt' and '.pth' model file.` | Model path has an unsupported extension. | Supply a local `.pt` or `.pth` file. If the file is compressed or renamed, unpack or locate the actual PyTorch weights. |
| `The path '...' isn't a valid file` from `setModelPath(...)` | The model path does not exist from the running process. | Use an absolute path or a path relative to the actual shell working directory. The bundled helper validates paths and does not assume cwd. |
| `parameter path should be a valid path to the json mapping file` | Custom mode JSON path is missing or wrong. | Provide the JSON mapping generated with the custom model. If it has not been created, route to the training/data sub-skill. |
| JSON decode error in custom mode | The class mapping file is not valid JSON. | Replace it with the original ImageAI training output or a valid mapping object such as `{"0":"class_a","1":"class_b"}`. Keep class order aligned with training. |
| `Weight loading failed...` in custom mode | Architecture/model type does not match weights, JSON class count does not match final layer, state dict is corrupt/wrong framework, or file path points to the wrong artifact. | Check model type first. Then check that the JSON mapping is from the same training run and has the same number/order of classes. Use `.pt`/`.pth` PyTorch state dicts. |
| Missing keys, unexpected keys, or size mismatch while loading | Model type or class-count mismatch. | Select the architecture used during training/export. For custom classifiers, use the matching JSON mapping. For ImageNet release weights, use the corresponding ImageNet model type. |
| `RuntimeError: Model not yet loaded...` from `classifyImage(...)` | `loadModel()` was not called or failed before inference. | Follow the required order: model type setter, `setModelPath`, custom `setJsonPath`, optional `useCPU`, `loadModel`, then `classifyImage`. Check earlier logs if `loadModel()` swallowed an exception. |
| `image path '...' is not found or a valid file` | File input string does not point to an existing file. | Validate the path and permissions. Prefer absolute paths in user-facing commands. |
| `Invalid image input format` | Input is not a path string, numpy array, or PIL image. | Convert bytes/streams to a PIL image or numpy array before calling the API. The helper only supports image file paths. |
| Pillow cannot identify/open image | File exists but is not a supported or uncorrupted image. | Test with `PIL.Image.open(path).verify()` or convert the asset to a common RGB JPEG/PNG. |
| `result_count` error from torch top-k or too many requested results | `result_count` is less than 1 or greater than available classes. | Use 1-1000 for ImageNet; for custom mode, use no more than the number of entries in the JSON mapping. |
| Predictions are nonsensical for custom model | Wrong model type, wrong JSON mapping, different preprocessing expectation, or poor/incorrect training data. | Confirm the model and JSON came from the same ImageAI training run and selected architecture. If the model is not ImageAI-trained, inspect whether its final layer and preprocessing match ImageAI. |
| Predictions have color-sensitive errors from OpenCV arrays | OpenCV loads images as BGR, while ImageAI wraps numpy arrays as RGB without channel swapping. | Convert `cv2.imread` output with `cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)` before passing the numpy array. |
| CPU inference is slow | `useCPU()` was requested or no usable CUDA device is available. DenseNet121/InceptionV3 are slower than MobileNetV2/ResNet50. | Prefer GPU where available, reduce request volume, batch at the application level if appropriate, or choose MobileNetV2 for low-latency CPU use. |
| GPU exists but CPU is still used | CUDA is unavailable to PyTorch, wrong torch build is installed, or `useCPU()` was called. | Check `torch.cuda.is_available()` in the same environment. Remove `useCPU()` if GPU inference is desired. |
| Repeated torchvision warnings about `pretrained` deprecation | ImageAI source constructs torchvision models with the older `pretrained=False` argument. | Treat these warnings as noise if imports and loading succeed. Suppress warnings at the application boundary only if they hide important logs. |
| Older sample uses `loadModel(num_objects=10)` and fails | Current ImageAI 3.0.3 `CustomImageClassification.loadModel()` takes no `num_objects` argument. | Remove the argument. Class count comes from the JSON mapping set by `setJsonPath(...)`. |

## Handling `.h5` custom classification requests

When a user asks for custom classification with a `.h5` model:

1. Explain that ImageAI 3.x uses PyTorch and rejects TensorFlow/Keras `.h5` files through its extension checker.
2. Offer the supported paths:
   - Use an ImageAI 3.x `.pt` or `.pth` model plus JSON mapping.
   - Or run a legacy ImageAI 2.1.6-or-earlier TensorFlow environment if the `.h5` artifact must be used.
3. Do not generate a PyTorch `ImageClassification` or `CustomImageClassification` command that points at the `.h5` file.

## Verification without external weights

When model assets are not available, still verify safe parts:

- `python scripts/classify_image.py --help`
- Import checks for `ImageClassification` and `CustomImageClassification`.
- Signature checks for `classifyImage` and `loadModel`.
- Path validation and extension-error cases using tiny temporary files.

Do not claim full inference correctness unless compatible weights and representative images were actually loaded and run.
