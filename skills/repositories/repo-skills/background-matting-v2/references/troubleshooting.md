# Troubleshooting

## Purpose

This is the cross-cutting troubleshooting page for install, import, backend,
and data issues that affect multiple workflows.

## Common failures

### Import fails for `model`, `dataset`, or `inference_utils`
**Symptoms**
- `ModuleNotFoundError`
- the smoke helper cannot import the repo modules

**Likely causes**
- the checkout root is not on `sys.path`
- required runtime packages are missing
- the environment has the wrong PyTorch / torchvision combination

**Recovery**
- use the bundled `scripts/check_env.py`
- confirm the checkout root you passed is correct
- install the runtime stack from the root skill guidance, and add `onnx` when you want ONNX export smoke coverage

### `torch.cuda.is_available()` is false on a GPU host
**Symptoms**
- CUDA import works, but the model only runs on CPU
- the GPU smoke helper says CUDA is unavailable

**Likely causes**
- CPU-only PyTorch wheel
- incompatible CUDA wheel or driver
- container GPU passthrough not exposed

**Recovery**
- install a CUDA-matching torch/torchvision wheel set
- re-run the environment smoke helper with `--device cuda`
- if the host has no usable GPU, stay on CPU and do not claim CUDA coverage

### `MattingRefine` shape assertion errors
**Symptoms**
- `src and bgr must have the same shape`
- `src and bgr must have width and height that are divisible by 4`
- `backbone_scale should not be greater than 1/2`

**Likely causes**
- mismatched image sizes
- a video or webcam frame was resized inconsistently
- the chosen model parameters violate the model constraints

**Recovery**
- resize or align the inputs before inference
- keep both inputs on the same resolution
- use the recommended scale values from `references/backend-compatibility.md`

### OpenCV / alignment issues
**Symptoms**
- alignment helper fails to find a homography
- OpenCV video or webcam errors
- GUI windows do not open

**Likely causes**
- too few feature matches
- no camera or display device
- headless runtime

**Recovery**
- disable preprocess alignment when the scene is sparse
- run image/video inference instead of webcam mode in headless sessions
- check that OpenCV and GUI support are available if you need the webcam demo

### Output directory overwrite or path issues
**Symptoms**
- the CLI asks to override an existing output directory
- files appear in a different output tree than expected

**Likely causes**
- the chosen output directory already exists
- the wrong `--output-types` were selected

**Recovery**
- use a fresh output path
- add `-y` only when you intentionally want overwrite behavior
- verify the requested output types first with the relevant CLI help

### Missing optional packages
**Symptoms**
- `ImportError` for `kornia`, `onnx`, `onnxruntime`, `tensorboard`, or `cv2`

**Likely causes**
- the runtime stack is incomplete
- an older environment still has the historical pins from `requirements.txt`

**Recovery**
- install the supported runtime packages listed in the root skill
- re-run the environment smoke helper after installing the missing package

## When to stop and ask for more data

- webcam demo needs a camera and display
- training needs real datasets and checkpoint storage
- export needs a real checkpoint if you want the repo's exact conversion path
- ONNX or TorchScript issues that stem from unsupported runtime ops may require
  a different backend or patch method
