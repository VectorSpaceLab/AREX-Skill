# Setup troubleshooting

## Build failures

### FaceBoxes NMS fails in Cython

- Symptom: the build stops in `FaceBoxes/utils/nms/cpu_nms.pyx`.
- Likely cause: the active Cython version is too new for the legacy NMS source.
- Recovery: use the bundled build helper from the prepared CPU environment and
  keep the Cython version in the legacy-compatible range noted by the root
  troubleshooting guide.

### Sim3DR or render build fails

- Symptom: `Sim3DR_Cython` or `render.so` is missing after the build.
- Likely cause: the native build never completed, or the command ran from the
  wrong directory.
- Recovery: rerun the bundled native-build helper from the checkout root and
  confirm the expected artifact names appear in the target directories.

## Import failures

### `np.long` / alias errors

- Symptom: `TDDFA` or `bfm.bfm` fails at import time on modern NumPy.
- Likely cause: the repo still uses removed scalar aliases.
- Recovery: use the bundled bootstrap helper or a dedicated wrapper before
  importing the repo modules.

### Missing checkpoints or configs

- Symptom: `FaceBoxes` or `TDDFA` raises `FileNotFoundError` during
  construction.
- Likely cause: the checkout is missing a binary asset, or the current working
  directory is not the checkout root.
- Recovery: run the asset checker, confirm the config file you selected points
  to the expected checkpoint, and keep the repo root as the working directory.

## Optional dependency issues

### ONNX conversion paths fail

- Symptom: `FaceBoxes_ONNX` or `TDDFA_ONNX` cannot find a `.onnx` file.
- Likely cause: the generated ONNX file is absent or the conversion happens in
  a directory without write permission.
- Recovery: let the ONNX helper auto-convert inside the checkout, or create the
  ONNX files ahead of time in a writable checkout.

## Environment notes

- The repo's setup path is CPU-first and works without CUDA.
- Headless plotting is the default for the generated helpers.
- If the root helper reports `No face detected` during smoke tests, switch to a
  sample image with a clear frontal face before blaming the environment.
