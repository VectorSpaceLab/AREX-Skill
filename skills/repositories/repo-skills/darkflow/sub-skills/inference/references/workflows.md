# Inference Workflows

## Purpose

Read this when the user needs a concrete Darkflow prediction, demo, JSON-output, Python API, or protobuf export/load workflow. Replace every placeholder with a user-provided model artifact path; do not assume the original checkout is present.

## Image folder prediction

Use a `.cfg` plus either a `.weights` file or checkpoint load value:

```bash
flow --imgdir <image_dir> --model <model.cfg> --load <weights-or-checkpoint> --threshold 0.4
```

Expected behavior:

- Darkflow builds the TensorFlow graph, loads weights/checkpoint state, and scans `<image_dir>` for `.jpg`, `.jpeg`, and `.png` files.
- Annotated outputs are written under `<image_dir>/out/`.
- CPU mode is the default. Add `--gpu <fraction>` only when a compatible TensorFlow 1.x GPU build exists.

## JSON output

Add `--json` when the user wants structured bounding boxes instead of annotated images:

```bash
flow --imgdir <image_dir> --model <model.cfg> --load <weights.weights> --threshold 0.4 --json
```

Each output JSON file is written under `<image_dir>/out/` and contains a list of objects shaped like:

```json
{
  "label": "person",
  "confidence": 0.82,
  "topleft": {"x": 189, "y": 96},
  "bottomright": {"x": 271, "y": 380}
}
```

## Python API prediction

Use `TFNet` directly when the caller already has an image array or wants to integrate Darkflow into another Python application:

```python
from darkflow.net.build import TFNet
import cv2

options = {
    "model": "<model.cfg>",
    "load": "<weights.weights>",
    "threshold": 0.1,
}

tfnet = TFNet(options)
image = cv2.imread("<image.jpg>")
result = tfnet.return_predict(image)
print(result)
```

Important: `return_predict()` requires a `numpy.ndarray`; passing a path string triggers an assertion.

## Camera or video demo

Use the `--demo` flag for a video file or the literal `camera` value:

```bash
flow --model <model.cfg> --load <weights.weights> --demo <video_file.avi>
flow --model <model.cfg> --load <weights.weights> --demo camera
```

Add `--saveVideo` to save a demo video as `video.avi`. Add `--queue <n>` to buffer frames in batches.

## Protobuf export and load

Export a loaded model to a frozen graph plus metadata:

```bash
flow --model <model.cfg> --load <weights-or-checkpoint> --savepb
```

Darkflow writes a `.pb` file and a matching `.meta` JSON file. Load that pair later with:

```bash
flow --pbLoad <graph.pb> --metaLoad <graph.meta> --imgdir <image_dir>
```

The same `pbLoad` and `metaLoad` options can be passed to `TFNet` in Python.

## Validation checklist

- `flow --help` works in the current environment.
- The model, weights/checkpoint, and label source are from the same model family.
- The input directory contains supported image extensions.
- The expected output folder or graph files are created.
- For `.pb` workflows, the `.pb` and `.meta` files are kept together and loaded as a matching pair.
