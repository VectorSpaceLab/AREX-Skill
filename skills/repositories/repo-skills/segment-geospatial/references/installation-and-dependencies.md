# Installation and dependency map

## Purpose

Read this before installing `segment-geospatial`, choosing extras, or diagnosing
import/backend failures. The package is intentionally split into optional extras
because SAM-family models, GPU runtimes, geospatial libraries, notebooks, and
API serving dependencies can be large or platform-sensitive.

## Python and environment choice

- Repository metadata requires Python `>=3.10`.
- CI evidence covers Python 3.10, 3.11, and 3.12.
- Use a fresh Conda/Pixi/venv environment. Avoid installing into an existing
  notebook, QGIS, or system Python unless the user explicitly wants that.
- Prefer Pixi or Conda when PyTorch/CUDA, rasterio/pyproj, or Windows dependency
  resolution is fragile. Pip can work, but ensure the installed torch build
  matches the desired CPU/CUDA runtime.

## Extras and when to choose them

| Install selector | Use when | Main added dependencies / caveats |
| --- | --- | --- |
| `segment-geospatial` | Core SAM1 and geospatial utility work | Base geospatial stack, torch, `segment_anything`, raster/vector helpers |
| `segment-geospatial[samgeo]` | Same core SAM1 surface with explicit extra spelling | Useful when pinning extras uniformly |
| `segment-geospatial[samgeo2]` | `SamGeo2`, SAM2 image/video/prompt workflows | Adds `sam2`, xarray/rioxarray/scipy/scikit-image stack |
| `segment-geospatial[samgeo3]` | `SamGeo3`, SAM3/SAM3.1 image/text/prompt/tiled/video workflows | Adds `sam3`, transformers, scikit-learn/image, leafmap/localtileserver, buildingregulariser, spaCy, triton on Linux |
| `segment-geospatial[fast]` | FastSAM wrapper | Adds `segment-anything-fast`; may require `pkg_resources` via setuptools `<81` |
| `segment-geospatial[hq]` | HQ-SAM wrapper | Adds `segment_anything_hq`, `sam2`, and `timm` |
| `segment-geospatial[text]` | LangSAM / GroundingDINO text prompts with SAM1/SAM2 | Adds GroundingDINO and SAM2 dependencies; model downloads are separate |
| `segment-geospatial[api]` | `samgeo-api` FastAPI service | Adds FastAPI, Uvicorn, and multipart upload support |
| `segment-geospatial[fer]` | Feature edge reconstruction / GDAL-specific FER path | Requires `osgeo`/GDAL; skip unless that workflow is explicitly needed |
| `segment-geospatial[all]` | Broad package install including FER/GDAL | Avoid as a default if GDAL/FER is not selected |
| `segment-geospatial[extra]` | Notebook-heavy examples and all optional package features | Broadest install; includes all plus notebook/GIS helper extras |

A practical broad-but-not-FER install for most package use is:

```bash
pip install "segment-geospatial[samgeo2,samgeo3,fast,hq,text,api]"
```

## CUDA and SAM3 requirements

The repository documentation states that SAM3 and SAM3.1 currently require
NVIDIA CUDA support for real inference. Treat SAM3 runtime guidance as
CUDA-backed even when import-only checks pass on CPU.

Minimum CUDA readiness checks:

```python
import torch
print(torch.__version__, torch.version.cuda)
print(torch.cuda.is_available(), torch.cuda.device_count())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0))
    torch.empty((1,), device="cuda")
```

If CUDA is false on a GPU host, likely causes include a CPU-only torch wheel,
missing GPU passthrough in a container, an old driver, or incompatible CUDA
runtime packages. Do not use CPU-only torch as proof of SAM3 capability.

## Model weights, network, and credentials

- SAM1 checkpoints (`vit_h`, `vit_l`, `vit_b`) may be downloaded by
  `samgeo.common.download_checkpoint()` or supplied as a local checkpoint path.
- SAM2 and SAM3 constructors use package-specific model identifiers and often
  download weights from Hugging Face or upstream model hubs.
- SAM3.1 (`facebook/sam3.1`) is supported by the Meta backend only. It may need
  direct Hugging Face checkpoint downloads when the installed `sam3` helper does
  not expose a versioned downloader.
- Hugging Face-gated SAM3 assets require the user to request access and log in.
- Map tile examples use remote tile providers; obtain permission for large
  downloads and avoid treating notebook examples as offline tests.

## Verified package facts to preserve

Installed-package inspection for version 1.4.1 verified these public facts:

- `samgeo.__version__ == "1.4.1"`.
- `AVAILABLE_MODELS` contains `sam: vit_h/vit_l/vit_b`, `sam2:
  sam2-hiera-tiny/small/base-plus/large`, and `sam3: facebook/sam3,
  facebook/sam3.1`.
- `EXTRAS_MAP` maps `sam -> samgeo`, `sam2 -> samgeo2`, and `sam3 -> samgeo3`.
- `samgeo-api --help` exposes `--host`, `--port`, `--reload`, and `--preload`.
- The package can import `samgeo.common`, `samgeo.api`, SAM1/SAM2/SAM3 modules,
  FastSAM, HQ-SAM, LangSAM, captioning, model registry, and UTM helpers when the
  selected extras above are installed.

## Optional dependency edges

- FastSAM/ultralytics may still import `pkg_resources`; if a very new
  setuptools release removed it, pin `setuptools<81` in the environment.
- `samgeo.caption` imports a remote aerial feature vocabulary at module import
  time; full BLIP captioning also downloads model assets and may download a
  spaCy model.
- `samgeo.detectree2.TreeCrownDelineator` requires external `detectree2` and
  Detectron2. Install those only when tree crown delineation is selected.
- `samgeo.fer` requires `osgeo`/GDAL. Keep it out of default installs unless the
  FER workflow is requested.
