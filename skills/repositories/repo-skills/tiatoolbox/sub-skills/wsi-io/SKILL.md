---
name: wsi-io
description: "Use TIAToolbox for whole-slide image reading, metadata,
  resolutions, thumbnails, tiles, region reads, multichannel inputs, and
  registration setup."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# WSI I/O

Use this sub-skill when a task needs to open pathology whole-slide images or image-like arrays, inspect WSI metadata, select a reader, choose resolution units, read crops, create thumbnails or tiles, diagnose multichannel reads, or prepare image pairs for registration.

## Route Here For

- Opening WSIs or image arrays with `WSIReader.open`, `OpenSlideWSIReader`, or `VirtualWSIReader`.
- Reading metadata through `WSIMeta`, `wsi.info`, `slide-info`, and resolution conversion helpers.
- Choosing among `mpp`, `power`, `level`, and `baseline` units for safe crop dimensions.
- Using `read_rect`, `read_bounds`, `read_region`, `slide_thumbnail`, `slide-thumbnail`, `save_tiles`, and `read-bounds`.
- Handling OME-TIFF/QPTIFF/NGFF multichannel reads and `post_proc=None` versus RGB conversion.
- Setting up fixed/moving image pairs for `DFBRegister` registration and diagnosing transform ordering.

## Route Elsewhere

- Use `image-preprocessing` for tissue masks, stain normalization, stain augmentation, patch extraction, and preprocessing validation.
- Use `model-inference` for patch predictors, semantic segmentors, nucleus detectors, feature extractors, and inference engine batching.
- Use `annotation-visualization` for overlays, annotation stores, tile server visualization, and rendered review views.
- Use `cli-and-configuration` for exhaustive CLI option tables, shared command flags, config conventions, and command orchestration.

## References

- `references/api-reference.md` summarizes reader selection, metadata fields, read APIs, resolution semantics, CLI entry points, and registration APIs.
- `references/workflows.md` gives copyable recipes for metadata inspection, safe crops, thumbnails, tiles, multichannel reads, and registration setup.
- `references/troubleshooting.md` maps common WSI I/O failures to concrete checks and fixes.
- `scripts/wsi_io_smoke.py` runs a tiny in-memory `VirtualWSIReader` smoke check without network access or WSI downloads.

## Fast Start

```python
import numpy as np
from tiatoolbox.wsicore.wsireader import WSIReader

wsi = WSIReader.open("slide.svs")
print(wsi.info.as_dict())

# Fixed output size; field of view changes with resolution.
patch = wsi.read_rect((10_000, 20_000), (512, 512), resolution=0.5, units="mpp")

# Fixed baseline field of view; output size changes with resolution.
region = wsi.read_bounds((10_000, 20_000, 12_000, 22_000), resolution=1, units="level")

# For arrays, masks, thumbnails, and small fixtures, use the virtual reader path.
array_reader = WSIReader.open(np.zeros((128, 192, 3), dtype=np.uint8), mpp=(0.5, 0.5))
thumbnail = array_reader.slide_thumbnail(resolution=1.0, units="baseline")
```

Before a large read, confirm `wsi.info.slide_dimensions`, available `level_downsamples`, whether `mpp` or `objective_power` exists, and whether the requested output is bounded enough to fit memory.
