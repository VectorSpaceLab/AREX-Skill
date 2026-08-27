# Evaluation and demo troubleshooting

Use this reference to classify evaluation/test/demo failures. Fixes that require
model graph changes belong in model-inference. Fixes that require acquiring or
repairing VOC/COCO data belong in data-training.

## Missing or incompatible weights

Symptoms:

- `FileNotFoundError` or similar when loading the `.pth` file.
- `Missing key(s)`, `Unexpected key(s)`, or tensor size mismatch from
  `load_state_dict`.
- Detections are empty or nonsensical despite a successful load.

Likely causes:

- The weight file path is wrong or the file was not downloaded.
- The state_dict is for a different SSD size, class count, or code revision.
- The model was built for VOC 21 classes but the weights are not VOC SSD300
  weights.

Action:

- Confirm the file exists and is a compatible SSD300 VOC state_dict.
- Do not continue to mAP claims until model compatibility is verified.
- Route architecture/key conversion or weight-loading patches to model-inference.

## Missing VOC2007 data

Symptoms:

- Missing `VOC2007/ImageSets/Main/test.txt`.
- Missing annotation XML or JPEG files.
- Evaluation stops while reading image ids, annotations, or images.
- AP files are absent because detections were never written.

Required layout under the VOCdevkit root:

```text
VOC2007/
  Annotations/
  JPEGImages/
  ImageSets/Main/test.txt
```

Action:

- Verify the VOC root points to the VOCdevkit directory, not directly to
  `VOC2007`.
- For unmodified `eval.py`, use a trailing separator in the VOC root template to
  avoid legacy string-concatenation mistakes.
- Route dataset download, extraction, and layout repair to data-training.

## Import-time dataset metadata failures

Symptoms:

- A VOC command or even a help/import smoke fails while importing the repository
  `data` package.
- The traceback mentions missing COCO label metadata such as
  `coco_labels.txt`, even though the intended task is VOC evaluation.

Likely cause:

- The package-level data import eagerly imports COCO helpers whose default
  transform reads COCO label metadata at import time.

Action:

- Treat this as a dataset/import-layout issue, not an mAP result.
- Provide the expected metadata only if COCO is in scope, or patch/lazy-load the
  import path for VOC-only work through the appropriate data/model route.
- Do not count this as a failed VOC evaluation; the evaluator did not reach its
  parser or dataset loop.

## Legacy Detect(Function) failure on modern PyTorch

Symptoms:

- Forward pass fails inside `Detect` or an autograd `Function` call.
- Errors mention legacy autograd functions, non-static `forward`, or deprecated
  `Variable`/`volatile` behavior.
- `eval.py`, `test.py`, notebook, and webcam demos all fail at `net(x)`.

Action:

- Stop evaluation/demo claims at this point.
- Route implementation details and compatibility patches to model-inference.
- After the patch, re-run a small forward smoke before attempting full VOC mAP.

## NumPy `np.bool` compatibility risk

Symptoms:

- Evaluation reaches AP computation and fails with an attribute error for
  `np.bool`.

Likely cause:

- Newer NumPy versions removed the deprecated `np.bool` alias used when parsing
  VOC `difficult` flags.

Action:

- Patch the evaluator to use `bool` or `np.bool_` before claiming AP results.
- Re-run enough AP computation to verify the fix.

## CUDA default tensor and device issues

Symptoms:

- `Expected all tensors to be on the same device`.
- CUDA initialization errors when CPU was intended.
- `Torch not compiled with CUDA enabled`.
- Slow or inconsistent behavior after a script changes the global default tensor
  type.

Likely causes:

- `eval.py` and `test.py` set global default tensor types.
- `test.py` and `demo.live` use legacy `argparse type=bool`, so strings like
  `False` may parse as true.
- Inputs, priors, model weights, or detection tensors are split across CPU/CUDA.

Action:

- Prefer explicit CPU/CUDA planning before running a script.
- For `eval.py`, use the robust string boolean values supported by its parser.
- For `test.py` or `demo.live`, do not trust `--cuda False` without checking or
  patching the parser.
- Route durable parser/device fixes to model-inference.

## Evaluation output appears missing

Symptoms:

- `--save_folder` exists but no AP files are inside it.
- VOC result text files are not where expected.
- `test1.txt` is not in the expected folder.

Likely causes and actions:

- `eval.py` creates `--save_folder`, but writes primary artifacts under
  `ssd300_120000/test` and the VOCdevkit `VOC2007/results` folder.
- `test.py` forms `test1.txt` as `save_folder + 'test1.txt'`; use a trailing
  separator in `--save_folder`.
- Old `test1.txt` content is appended to, not overwritten. Delete or rotate it
  before a fresh qualitative test.

## OpenCV GUI or webcam failures

Symptoms:

- `cv2` import fails.
- `cv2.imshow` fails, hangs, or reports no display backend.
- The webcam opens to black frames, cannot be found, or access is denied.
- `WebcamVideoStream(src=0)` cannot read frames.
- Cleanup after exit raises a legacy stream-scope error.

Action:

- Use `scripts/check_demo_requirements.py` to verify imports first.
- Separately confirm a GUI/display session and camera availability; the bundled
  checker intentionally does not open windows or access the camera.
- Change the camera index only after the user approves camera access.
- Treat a cleanup-only error after a visible demo as a script issue, not proof
  that detection failed.

## Missing `imutils`

Symptoms:

- `python -m demo.live` fails immediately with `ModuleNotFoundError: imutils`.

Cause:

- `demo.live` imports `FPS` and `WebcamVideoStream` from `imutils.video` at
  module import time.

Action:

- Install or provide `imutils` only for live webcam demo scope.
- Notebook and VOC mAP evaluation do not require `imutils`.

## Missing Jupyter, IPython, or Matplotlib

Symptoms:

- Notebook cannot start or kernel cannot import notebook components.
- Inline display or plotting cells fail.
- `%matplotlib inline` or `matplotlib.pyplot` import fails.

Action:

- Use `scripts/check_demo_requirements.py` to check import availability.
- Install Jupyter/IPython/Matplotlib only when notebook demos are in scope.
- A notebook display success is not a VOC mAP verification.

## Do not over-interpret partial success

- A command template printed by the planner proves only that arguments were
  assembled safely; it does not execute the repository script.
- A dependency checker pass proves only imports and CUDA reporting; it does not
  prove camera access, GUI display, weight compatibility, dataset layout, or
  model-forward success.
- A successful qualitative `test.py` or demo output does not reproduce VOC mAP.
