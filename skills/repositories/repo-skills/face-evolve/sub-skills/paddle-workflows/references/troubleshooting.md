# Paddle workflow troubleshooting

Use this when a face.evoLVe PaddlePaddle training, quantization, Paddle Inference, or Paddle Lite task fails before or during a safe prerequisite check.

## `import paddle` has no `__version__`, `inference`, or framework APIs

Likely cause: the local source directory named `paddle/` is shadowing the installed PaddlePaddle package.

Fix checklist:

1. Do not put the repository root on `PYTHONPATH` for Paddle workflows.
2. Do not run framework probes from an import context where the repository root is first on `sys.path`.
3. Import the installed PaddlePaddle framework first, then add the repository's `paddle/` source directory for modules such as `config`, `backbone`, `head`, and `loss`.
4. Run `scripts/inspect_paddle_components.py --repo-root <face.evoLVe checkout> --backbone IR_50` to confirm the framework version and a `[batch, 512]` output shape.

Symptom examples include `AttributeError: module 'paddle' has no attribute '__version__'`, `ImportError` for `paddle.inference`, or seeing an empty local package instead of the real framework.

## `ModuleNotFoundError: paddleslim`

PaddleSlim is needed for QAT and post-training quantization only. It is not required for a plain backbone forward check unless the training script imports QAT unconditionally.

Fix checklist:

- Install a PaddleSlim version compatible with the installed PaddlePaddle version.
- If the task is only component inspection, use the bundled inspection script instead of importing the full training script.
- For QAT, verify `from paddleslim.dygraph.quant import QAT` works.
- For post-training quantization, verify `from paddleslim.quant import quant_post_dynamic` and `paddleslim.quant.quant_post_static` are available.

## `ModuleNotFoundError: requests` or pretrained weight download failure

The `ppResNet_50` path may import/use `requests` for pretrained weight download. If offline or missing `requests`:

- choose `IR_50`, `IR_SE_50`, or `ResNet_50` for a local component check;
- set `USE_PRETRAINED=False` before training `ppResNet_50`; or
- install `requests` and pre-arrange network/cache access for the pretrained model.

## Missing `.pdmodel` or `.pdiparams` for Paddle Inference or quantization

Paddle Inference and post-training quantization require static exported files, not only training checkpoints.

Fix checklist:

1. Confirm training exported a backbone base name such as `Backbone_epoch99`, producing `Backbone_epoch99.pdmodel` and `Backbone_epoch99.pdiparams`.
2. If the demo expects `../model/Backbone.pdmodel` and `../model/Backbone.pdiparams`, either copy/rename the exported files deliberately or update the predictor's model base path.
3. Do not pass `.pdparams` checkpoint-only files to `paddle.inference.Config`; it needs the static model program and params pair.
4. For dynamic/static quant scripts, replace hard-coded source example names with the actual exported epoch and directory.
5. For static quantization, also provide a calibration dataset and reader.

## Paddle Inference predictor always tries GPU

The server demo config calls GPU APIs such as `use_gpu()` and `enable_use_gpu(..., 0)`. On CPU-only systems this can fail before any face recognition logic runs.

Fix checklist:

- If GPU inference is required, verify the installed PaddlePaddle build, CUDA runtime, driver, and device id are compatible.
- If CPU inference is acceptable, change the predictor config to a CPU configuration before running the demo.
- Keep MTCNN predictors and the backbone predictor consistent; the MTCNN utility also enables GPU for PNet/RNet/ONet.

## Missing `FaceDatabase/` or empty `face_data.fdb`

The demos build a face embedding database before recognizing video frames.

Fix checklist:

- Create `FaceDatabase/` in the demo working directory with one reference image per identity.
- Use image filenames whose basename is the desired displayed identity name.
- Ensure each database image contains exactly one detectable face; the demo skips images with zero or multiple faces.
- Delete stale `face_data.fdb` after changing the model, quantization, preprocessing, threshold, or identity images so it is regenerated.
- Treat `face_data.fdb` as model-specific; do not reuse it across different backbones or Paddle Lite/Inferences conversions without validation.

## Missing `test.mp4`, display, or font files

The demo main loops assume a local `test.mp4` and GUI display. Text drawing also references platform-specific fonts.

Fix checklist:

- Provide a readable video file or modify the capture source.
- On headless servers, replace `cv2.imshow`/`cv2.waitKey` with file output or logging before running.
- For Paddle Inference text rendering, supply `simsun.ttc` or change the font path.
- For Paddle Lite text rendering, supply `GBK-EUC-V.ttc` if using the PIL text path, or keep to the OpenCV text branch.

## Paddle Lite runtime or `.nb` model is absent

The Lite demo imports `paddlelite.lite` and loads `.nb` models. The repository does not provide the converted models.

Fix checklist:

- Install a Paddle Lite Python runtime appropriate for the target CPU/edge device.
- Convert the exported Paddle model to the target Paddle Lite version and hardware backend.
- Place or configure the required files: `Backbone.nb`, `model/Pnet.nb`, `model/Rnet.nb`, and `model/Onet.nb`.
- Confirm the Lite runtime can create predictors before opening video input.
- Recalibrate the source threshold `0.6` after conversion and quantization.

## Training data layout or label errors

Paddle training expects an ImageFolder identity-folder tree and eagerly loads images into memory.

Fix checklist:

- Use one directory per identity and image files directly inside each identity directory.
- Remove hidden files, non-image files, empty identity directories, and nested unexpected folders.
- Provide aligned/resized face crops; the active Paddle transform does not resize images by default.
- Validate that the class count used by heads is the number of identity folders. The source `NormalDataset.num_classes` assignment should be checked before serious training because it can reflect image count rather than identity count.
- If memory spikes during dataset construction, reduce dataset size for smoke tests or rewrite the loader to load lazily.

## Multi-GPU script fails before training

The distributed scripts need source repair before use.

Fix checklist:

- Correct the launcher target so `fleetrun` launches the distributed training file rather than recursively invoking the launcher.
- Add or remove the missing `CLIP` configuration usage.
- Replace undefined `LFWDataset` usage with the actual Paddle data loader or a validated custom loader.
- Verify GPU ids, Paddle distributed runtime, data volume, and checkpoint output paths before launching.
