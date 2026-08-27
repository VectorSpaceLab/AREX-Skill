# Specialized model troubleshooting

## FastSAM

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Import error mentioning `pkg_resources` | Upstream `segment-anything-fast`/ultralytics expects deprecated `pkg_resources` | Pin `setuptools<81` and retry import. |
| Model file downloads unexpectedly | `FastSAM-x.pt` or `FastSAM-s.pt` not cached | Provide a known model path/cache or authorize the download. |
| Text prompt path fails | CLIP/text dependencies or model assets missing | Confirm `[fast]` extra, CLIP dependency, and model weights. |

## HQ-SAM

- Install `[hq]` and confirm `segment_anything_hq` imports.
- Upstream `timm` and registry warnings can be non-fatal; distinguish warnings
  from import/model construction failures.
- Provide checkpoint paths when running offline.

## LangSAM / GroundingDINO

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `groundingdino` import failure | `[text]` extra missing or install failed | Install `segment-geospatial[text]`; restart notebooks/kernels after install. |
| Checkpoint/config download fails | Hugging Face/network blocked | Pre-download GroundingDINO and SAM assets or avoid the text workflow offline. |
| Many false positives or no detections | Thresholds unsuitable for imagery/prompt | Tune `box_threshold`, `text_threshold`, `min_size`, and prompt wording on a small crop. |
| Slow inference | CPU or large image | Use CUDA, crop/split imagery, or try SAM3 text-prompt workflows. |

## Captioning

- Importing `samgeo.caption` fetches an aerial feature vocabulary from a remote
  URL. If import fails offline, do not treat all of SamGeo as broken.
- `ImageCaptioner()` can download `en_core_web_sm` and a BLIP model. Ask before
  triggering model downloads in restricted environments.
- If feature extraction seems generic, pass `include_features="default"` to use
  the aerial vocabulary or pass a custom feature list.

## detectree2

- `TreeCrownDelineator()` raises a clear `ImportError` until external
  `detectree2` and Detectron2 are installed.
- Detectron2 compatibility depends on Python, torch, CUDA, and platform. Do not
  install it as part of ordinary SamGeo setup unless tree crown delineation is
  the user's selected task.
- Pretrained model downloads are external and should be authorized.

## FER / GDAL

- `samgeo.fer` reports missing `osgeo` when GDAL is absent.
- Install a Conda/Pixi GDAL environment for FER, not a random pip GDAL wheel,
  unless the platform's GDAL ABI is known.
- If the user only needs polygon cleanup, try `regularize` or `smooth_vector`
  from the geospatial utilities path before selecting FER.
