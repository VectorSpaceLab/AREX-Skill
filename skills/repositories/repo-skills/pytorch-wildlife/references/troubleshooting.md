# Cross-cutting troubleshooting

Read this before changing versions or rerunning an expensive command.

## Import fails around `yolov5` or `pkg_resources`

**Symptom:** importing `PytorchWildlife` fails in the legacy YOLOv5 import chain
with `ModuleNotFoundError: pkg_resources`, or an old package rejects the
installed setuptools.

**Cause:** the root package eagerly imports detector families, including a
legacy YOLOv5 dependency whose import assumptions may not match modern
setuptools. This can block unrelated classifier or bioacoustic imports.

**Recovery:** record the exact Python, setuptools, torch, torchvision, and YOLOv5
versions; use a clean isolated environment and a package-compatible Python
(3.10 or 3.11 is safer than an unconstrained newest interpreter). Prefer a
supported dependency release or a documented compatibility provision in the
private environment. Do not silently downgrade the entire environment or
publish a local shim as a package requirement. If only a narrow API is needed,
verify whether a direct submodule import avoids the eager root import, but do
not claim that as a supported public installation if the package itself cannot
import.

## `pip check` passes but a model import fails

`pip check` validates metadata, not native imports, optional operators, or
weight formats. Run the root import, the relevant submodule import, and a
read-only signature check separately. Compare the traceback to the owning
sub-skill's optional-dependency notes before adding packages.

## Weight or network failures

A default pretrained model may download from an external release URL and cache
under Torch's cache directory. In offline mode use a local `weights=` path,
check it exists and is readable, and verify the checkpoint's architecture and
class mapping. Do not turn an HTTP error into a model or data diagnosis. Stop
when credentials, private datasets, or an approved network route are required.

## CUDA or device failures

Check `torch.cuda.is_available()`, driver compatibility, device index, and a
small tensor allocation before model construction. A CPU fallback is valid for
structural/API checks, but not evidence of CUDA performance or a GPU-only
workflow. Reduce image size/batch size or select CPU when memory is exhausted;
keep the failed GPU claim explicit. Do not install a random CUDA wheel based
only on the driver-reported maximum version.

## Input, config, or output failures

- Verify image paths are readable RGB files and use HWC arrays for single-image
  APIs. Directories are recursive; do not place generated output inside them.
- Validate detection thresholds in `[0, 1]`; the package does not universally
  enforce this range.
- Validate audio window geometry (`0 <= overlap < window size`), sample rate,
  annotation keys, class count, spectrogram paths, and split-group leakage
  before model loading.
- Verify `img_id`, detection arrays, class names, and confidence arrays have
  matching lengths before serialization.
- Use explicit output paths and preserve source images; the safe separation
  helper refuses traversal and unsafe destination choices.

## Video/UI failures

Missing FFmpeg/OpenCV codecs, unsupported `avc1`, browser playback failures,
and large Windows uploads are known operational issues. Try a codec supported
by the local build, test the written file independently, and keep Gradio on a
trusted interface with authentication handled outside the demo. Never expose
an unauthenticated showcase UI as a production service.

## Legacy fine-tuning failures

The companion training directories have distinct dependency assumptions and
may be incompatible with the core environment. First validate CSV/YOLO layout,
config paths, class mapping, and split grouping. A failure in a logger,
checkpoint, or old Lightning/Ultralytics import is an environment/workflow
issue; do not “fix” it by changing the core package without recording the
variant. Training, validation, remote logging, and weight downloads require an
explicit runtime decision.
