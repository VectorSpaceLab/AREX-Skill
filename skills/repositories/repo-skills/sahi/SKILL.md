---
name: sahi
description: "Route SAHI sliced object-detection inference, model integration,
  postprocessing, COCO dataset utilities, prediction objects, CLI usage, and
  troubleshooting workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SAHI

Use this repo skill when the task involves SAHI (Slicing Aided Hyper Inference) for object detection or instance segmentation on large images, especially sliced inference for small objects, detector-framework wrappers, NMS/NMM duplicate handling, COCO dataset utilities, prediction exports, or the `sahi` CLI.

SAHI is a Python package. It does **not** ship detector weights; real inference requires an installed optional detector framework plus local weights, a framework model name, a preloaded model object, or a service/HuggingFace/Roboflow credential where appropriate.

## Minimal setup check

```bash
pip install sahi
python - <<'PY'
import sahi
from sahi import AutoDetectionModel, ObjectPrediction
from sahi.predict import get_sliced_prediction
print(sahi.__version__)
print(AutoDetectionModel, ObjectPrediction, get_sliced_prediction)
PY
```

For deeper diagnostics, run the bundled [environment checker](scripts/check_sahi_env.py):

```bash
python scripts/check_sahi_env.py --json
```

Read [installation and optional dependencies](references/installation-and-optional-deps.md) before installing detector frameworks, GPU packages, COCO evaluation tools, or FiftyOne.

## Route by task

| User task | Read |
| --- | --- |
| Run or debug `get_prediction`, `get_sliced_prediction`, `predict`, `sahi predict`, folder/video inference, batching, exports, progress callbacks, or slice-size tuning | [sliced-inference](sub-skills/sliced-inference/SKILL.md) |
| Choose/configure `AutoDetectionModel.from_pretrained`, model type, optional detector framework, local weights, HuggingFace/Roboflow credentials, category mapping, or device | [model-integrations](sub-skills/model-integrations/SKILL.md) |
| Create, slice, filter, split, merge, convert, evaluate, analyze, or visualize COCO datasets and results | [dataset-tools](sub-skills/dataset-tools/SKILL.md) |
| Choose NMS/NMM/GreedyNMM, `IOS` vs `IOU`, class-aware vs class-agnostic matching, or numpy/numba/torchvision postprocess backend | [postprocess-backends](sub-skills/postprocess-backends/SKILL.md) |
| Work with `BoundingBox`, `Mask`, `ObjectPrediction`, `PredictionResult`, COCO/FiftyOne/imantics conversions, visualization helpers, or image/mask utilities | [annotations-and-results](sub-skills/annotations-and-results/SKILL.md) |
| Diagnose install/import, optional dependency, OpenCV, device, CLI, data, or credential failures that span several workflows | [troubleshooting](references/troubleshooting.md) |

## High-value entry points

- `from sahi import AutoDetectionModel`
- `from sahi.predict import get_prediction, get_sliced_prediction, predict, predict_fiftyone`
- `from sahi.slicing import slice_image, slice_coco, get_slice_bboxes`
- `from sahi.postprocess.backends import set_postprocess_backend, get_postprocess_backend, resolve_backend`
- `from sahi.postprocess.combine import nms, batched_nms, greedy_nmm, nmm, NMSPostprocess, GreedyNMMPostprocess`
- `from sahi.annotation import BoundingBox, Category, Mask, ObjectAnnotation`
- `from sahi.prediction import ObjectPrediction, PredictionResult`
- `from sahi.utils.coco import Coco, CocoImage, CocoAnnotation, CocoPrediction, export_coco_as_yolo`
- CLI groups: `sahi predict`, `sahi predict-fiftyone`, `sahi coco slice`, `sahi coco yolo`, `sahi coco evaluate`, `sahi coco analyse`, `sahi coco fiftyone`, `sahi env`, `sahi version`

## Safe bundled checks

Run these when you need deterministic local validation without model downloads, credentials, training, or GPU requirements:

```bash
python scripts/check_sahi_env.py
python sub-skills/sliced-inference/scripts/sliced_prediction_smoke.py --mode sliced
python sub-skills/dataset-tools/scripts/coco_fixture_smoke.py
python sub-skills/postprocess-backends/scripts/postprocess_backend_smoke.py --print-backend
python sub-skills/annotations-and-results/scripts/prediction_objects_smoke.py
python sub-skills/model-integrations/scripts/check_model_dependencies.py
```

The model dependency checker only probes installed packages. It does not prove that a detector checkpoint exists, can download, has credentials, or can run on the requested device.

## Evidence and refresh

Read [repo provenance](references/repo-provenance.md) before deciding whether this skill is current for another checkout or release. If the package version, public API, CLI entry points, optional dependency matrix, or source commit changed, refresh the skill before relying on exact signatures or troubleshooting notes.

This run intentionally produced a self-contained candidate skill and did not import it into the live DisCo repo-skill library.
