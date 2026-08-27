# Troubleshooting

## Build and import failures

### `Invalid type` or `np.int_t` during FaceBoxes Cython build

- Symptom: `FaceBoxes/utils/nms/cpu_nms.pyx` fails during `build.py` with an
  invalid NumPy/Cython type error.
- Likely cause: Cython 3.x is too strict for the legacy FaceBoxes extension.
- Recovery: use the bundled build helper in the prepared inspection environment
  with a legacy-compatible Cython release, then rebuild the native extensions.

### `AttributeError: module 'numpy' has no attribute 'long'`

- Symptom: importing `TDDFA` or `bfm.bfm` fails on modern NumPy.
- Likely cause: the repo still uses deprecated NumPy scalar aliases.
- Recovery: use the bundled runtime helper or another pre-import compatibility
  shim before importing the pipeline. Do not edit the public repo skill to rely
  on a private site-packages path.

### Missing `cpu_nms`, `Sim3DR_Cython`, or `render.so`

- Symptom: `ImportError` from `FaceBoxes` or `utils.render`.
- Likely cause: the native build steps have not been run, or they were run in a
  different checkout or environment.
- Recovery: rerun the bundled native-build helper from the repo root and confirm
  the expected build artifacts exist in `FaceBoxes/utils/nms/`, `Sim3DR/`, and
  `utils/asset/`.

### `FileNotFoundError` for `configs/bfm_noneck_v3.pkl` or checkpoints

- Symptom: `FaceBoxes`, `TDDFA`, or `TDDFA_ONNX` fails during construction.
- Likely cause: the config points at a missing asset or the current working
  directory is wrong.
- Recovery: verify the asset map, keep the repo root as the working directory,
  and use the bundled asset checker before running demos.

## Demo and workflow failures

### `No face detected`

- Symptom: `demo.py` exits with `No face detected, exit`.
- Likely cause: the image has no visible face, the face is too small/oblique, or
  the detector assets are missing.
- Recovery: test with one of the bundled sample images, confirm the detector
  checkpoint exists, and check that the chosen config matches the weight file.

### `uv_tex` errors

- Symptom: UV texture generation fails with SciPy or matrix-loading errors.
- Likely cause: `scipy` is missing, or the UV assets in `configs/` are absent.
- Recovery: install the SciPy dependency set and verify `BFM_UV.mat` and
  `indices.npy` exist.

### Video reader or codec failures

- Symptom: the video demos cannot open `214.avi` or another clip.
- Likely cause: `imageio-ffmpeg` is missing, the codec is unsupported, or the
  path is wrong.
- Recovery: install the video IO dependencies, confirm the file path, and try
  the bundled sample video first.

### Webcam or display failures

- Symptom: the webcam demo blocks or opens no window.
- Likely cause: the workflow needs live camera permissions and a GUI display.
- Recovery: treat the webcam route as manual-only and verify camera/display
  access outside the headless wrappers.

## ONNX and benchmark failures

### `onnxruntime` import/provider problems

- Symptom: ONNX demos or benchmarks fail to import `onnxruntime` or report no
  usable provider.
- Likely cause: the runtime dependency is missing or the environment is too
  old/new for the available wheel.
- Recovery: reinstall the CPU wheel set and re-run the import smoke.

### `libomp` or thread warnings on macOS

- Symptom: the ONNX path runs slowly or emits OpenMP warnings.
- Likely cause: the local runtime lacks the OpenMP library expected by the
  wheel.
- Recovery: install `libomp` on macOS and keep the thread-count setting aligned
  with the benchmark helper.

### Benchmark timings vary a lot

- Symptom: repeated runs disagree by a large margin.
- Likely cause: `OMP_NUM_THREADS` is not pinned, the machine is busy, or warmup
  was skipped.
- Recovery: use the benchmark helper defaults, keep the thread count fixed, and
  run the same sample input for comparison.

## Compatibility note

This repo predates modern NumPy behavior. If you see an alias-related import
error, fix the environment with a compatibility shim or a conservative NumPy
pin before blaming the model code.
