# Global Histogram Troubleshooting

## Purpose

Use this when the global histogram transfer path fails or when a user asks for a global-reference workflow that the repository does not directly support.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No module named caffe` | PyCaffe is not installed or not on `PYTHONPATH` | Prepare Caffe with Python bindings. This workflow is not available through the repo's PyTorch path. |
| Error opening `global_model.caffemodel` | Global colorization weights are missing | Run [../scripts/check_global_histogram_assets.py](../scripts/check_global_histogram_assets.py) and stage the expected global weight. |
| Error opening `dummy.caffemodel` | Global statistics dummy weights are missing | Stage `models/global_model/dummy.caffemodel`; the stats prototxt alone is insufficient. |
| KeyError for `img_bgr` or `gt_glob_ab_313_drop` | Wrong stats prototxt or incompatible Caffe model | Verify `global_stats.prototxt` and use the matching dummy model. |
| Output ignores the reference image | `glob_dist` was omitted, malformed, all zeros, or mask channel was not enabled by wrapper | Pass the 313-bin vector returned from the stats net to `ColorizeImageCaffeGlobDist.net_forward`. |
| User asks for PyTorch global histogram transfer | This repository does not provide a PyTorch global histogram implementation | State the limitation and route to Caffe/global setup or a different implementation. |
| Reference image load fails | Bad path, unsupported image format, or missing fixture | Validate the reference path before Caffe execution and use an ordinary image file. |

## Diagnostic order

1. Run the bundled global asset checker.
2. Confirm PyCaffe import separately from model loading.
3. Check that both global prototxts and both global weights are present.
4. Confirm the reference image can be loaded and resized.
5. Confirm the stats net exposes `img_bgr` and `gt_glob_ab_313_drop`.
6. Confirm `ColorizeImageCaffeGlobDist` receives the histogram vector rather than `-1` when reference conditioning is desired.

## Verification status

The generated skill verifies global workflow facts from source and notebook evidence. It does not include native Caffe execution results, because PyCaffe and downloaded global weights were not available during construction. Treat missing Caffe/global runtime as an external setup block, not as a generated-skill content failure.
