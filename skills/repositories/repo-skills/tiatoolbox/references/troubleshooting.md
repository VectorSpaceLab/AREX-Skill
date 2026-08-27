# TIAToolbox Cross-Cutting Troubleshooting

Use this reference before diving into a workflow-specific troubleshooting file when the failure is about installation, imports, package discovery, or dependencies shared across TIAToolbox.

## Install and Import Checks

Run small checks before expensive WSI reads or model inference:

```bash
python - <<'PY'
import tiatoolbox
print(tiatoolbox.__version__)
PY
tiatoolbox --help
```

If import works but `tiatoolbox` is missing, the console script may not be on `PATH`. Use `python -m pip show tiatoolbox` to confirm the installed distribution, or run the console script from the environment where TIAToolbox is installed.

## Optional Native Dependencies

TIAToolbox workflows can depend on image codecs, OpenSlide-compatible readers, Torch, torchvision, Shapely, Flask/Bokeh, and scientific Python packages. Symptoms and first moves:

- Unsupported WSI or codec errors: confirm the file extension and route to `wsi-io` for reader support and metadata checks.
- Torch/CUDA/MPS errors: route to `model-inference` or `cli-and-configuration`; prefer CPU unless the user confirms hardware and installed wheels.
- Shapely or spatial query errors: route to `annotation-visualization` and validate geometry/properties separately from visualization.
- Browser/server failures: route to `annotation-visualization`; use `--noshow` and explicit `--port` for bounded checks.

## Network and Weights

Pretrained model construction can fetch weights from external model repositories when local weights are not supplied. For offline or reproducible tasks:

- Validate model keys with `model-inference/scripts/model_registry_probe.py` first.
- Prefer a user-provided local `weights` file or custom model object.
- State clearly when a plan requires network access or a pre-populated model cache.

## Data and Memory Safety

Whole-slide images and annotation stores can be large. Keep early checks small:

- Read metadata before full-resolution crops.
- Use thumbnails, bounded `read_bounds`, and small patch sizes for probes.
- Validate mask/image coordinate systems before extraction.
- Avoid launching visualization servers or long inference runs unless the user explicitly asks.
