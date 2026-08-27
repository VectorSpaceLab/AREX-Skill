# Detection troubleshooting

## Import fails before a model is constructed

The package root eagerly imports many model families, so a missing optional
legacy dependency can prevent even an unrelated detector from importing. Run
`check_detection_environment.py` and read its captured import error. Common
categories include missing `supervision`, `ultralytics`, or legacy YOLO V5
packages. Install the dependency set appropriate to the chosen public wrapper,
then rerun the checker. Do not work around an import failure by copying private
source shims into an application.

If the error mentions legacy `yolov5`, `pkg_resources`, or a removed setuptools
compatibility API, treat it as an environment compatibility problem. Use a
modern environment with a compatible setuptools/pkg_resources provision and a
matching YOLO V5 dependency, or use a V6/Apache/OWL/HerdNet wrapper when the
V5 checkpoint is not required. The exact workaround is environment-specific;
do not assume that a successful V6 model import proves V5 is usable.

## Invalid MegaDetector V6 version

The standard `MegaDetectorV6` accepts exactly:

- `MDV6-yolov9-c`
- `MDV6-yolov9-e`
- `MDV6-yolov10-c`
- `MDV6-yolov10-e`
- `MDV6-rtdetr-c`

MIT values must be passed to `MegaDetectorV6MIT`, and Apache values to
`MegaDetectorV6Apache`. HerdNet accepts only `general` and `ennedi`; OWL-C
accepts only `general` and `caribou`. Correct the class/version pair before
retrying. Do not catch the error and silently fall back to a different model.

## Offline run unexpectedly contacts the network

A constructor with `pretrained=True` can fetch weights when its cache is empty.
For V5, `pretrained=False` disables the default URL, but a local `weights` file
is still required. For standard V6, the source still creates its URL even when
`pretrained=False`; pass a readable local `weights` file. HerdNet and OWL also
need a local checkpoint for offline use. Apache prefers local weights. The MIT
implementation reconstructs its configuration and loads its configured URL or
cache path during inference; its `weights` argument is not a dependable offline
override. Stop the run, check network policy and checkpoint compatibility, and
never substitute an empty or unrelated file.

## `Need weights for inference` or checkpoint load failure

This means no usable local checkpoint or configured remote source was available.
Check that the path exists, is readable by the executing user, and matches the
wrapper family and version. A PyTorch checkpoint may fail for architecture,
state-dict key, serialization, or device reasons even when the file exists.
For CPU loading, use a checkpoint compatible with CPU map location and pass
`device="cpu"`. Do not run a training command to repair an inference checkpoint.

HerdNet and OWL checkpoints must contain the metadata and model state expected
by their wrapper. A generic YOLO checkpoint is not a HerdNet/OWL checkpoint.
Custom V6 Ultralytics weights must be loadable by the installed Ultralytics
predictor and expose the expected three detector classes.

## CUDA or device errors

Start with `device="cpu"` and run one local image. Check
`torch.cuda.is_available()` and the selected device index before using CUDA.
A CUDA-enabled torch build, a visible driver, and a model/backend compatible
with the selected device are all required. If CUDA initialization fails, do
not label the model broken until CPU inference is tested. Reduce batch size for
out-of-memory errors; batch size changes throughput, not confidence semantics.

## Image or shape errors

Use an RGB HWC ndarray (`H x W x 3`) or a readable image path. Convert grayscale,
RGBA, and CHW inputs before calling the detector. If an ndarray call returns a
missing or unhelpful image identifier, supply `img_path` as an identifier even
when it is not a filesystem path. For a batch ndarray input to standard V6 or
Deepfaune, pass a list of HWC images, not one HWC array.

## Empty detections or unexpected false positives

First print `model.CLASS_NAMES`, the number of rows in `result["detections"]`,
and the confidence values. Confirm that `det_conf_thres` is a float in `[0,1]`
and that the image domain matches the chosen model. Lower the threshold for
small/distant animals and raise it for screening precision, then measure on a
representative labeled sample. For HerdNet, inspect both detection and
classification scores; both must be strictly greater than their thresholds.
Do not assume score scales are comparable across MegaDetector, HerdNet, OWL,
and Deepfaune.

## Batch output is missing images or coordinates look wrong

Use `batch_size=1` for HerdNet and OWL because their patch loops currently use
the first image in a loaded batch. Retain each returned `img_id`; directory
walk order is not a stable external index. `normalized_coords` is not emitted
by every single-image path, and some batch implementations transpose width and
height while normalizing. Recompute `[x1/W, y1/H, x2/W, y2/H]` from
`detections.xyxy` and the original image dimensions when coordinates are used
for evaluation, Timelapse, or downstream geometry.

## Next route

If the detector result is valid but the task asks for species classification,
route to `classification`. If it asks for JSON/image/video/crop/separation
artifacts, route to `data-and-postprocessing`. If it asks to train or adapt a
model, route to `fine-tuning` rather than altering an inference workflow.
