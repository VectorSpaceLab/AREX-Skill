# Optional model overview

## FastSAM

- Import: `from samgeo.fast_sam import SamGeo`.
- Extra: `segment-geospatial[fast]`.
- Purpose: faster SAM-style segmentation with everything, point, box, and text
  prompts.
- Key methods: `set_image`, `everything_prompt`, `point_prompt`, `box_prompt`,
  `text_prompt`, `save_masks`, `raster_to_vector`, `show_anns`.
- Caveats: model weights are downloaded when missing; upstream FastSAM/
  ultralytics may require deprecated `pkg_resources`, so pin `setuptools<81` if
  import fails.

## HQ-SAM

- Import: `from samgeo.hq_sam import SamGeo`.
- Extra: `segment-geospatial[hq]`.
- Purpose: high-quality SAM masks with an API similar to `samgeo.samgeo.SamGeo`.
- Key methods: `generate`, `set_image`, `predict`, `save_masks`,
  `tiff_to_gpkg`, `tiff_to_geojson`.
- Caveats: downloads HQ-SAM checkpoints when not supplied; emits upstream `timm`
  registry warnings in some environments.

## LangSAM / GroundingDINO text prompts

- Import: `from samgeo.text_sam import LangSAM`.
- Extra: `segment-geospatial[text]`.
- Purpose: GroundingDINO detects boxes from text and SAM/SAM2 converts boxes to
  masks.
- Key methods: `set_image`, `predict`, `predict_batch`, `save_boxes`,
  `raster_to_vector`, `show_map`, `region_groups`.
- Caveats: GroundingDINO and SAM/SAM2 model weights are downloaded; GPU is
  strongly preferred.

## Image captioning and aerial feature extraction

- Import: `from samgeo.caption import ImageCaptioner, blip_analyze_image,
  extract_features_from_caption`.
- Dependencies: transformers, torch, spaCy, requests, PIL.
- Purpose: generate BLIP captions and extract aerial feature tokens from the
  caption.
- Caveats: importing `samgeo.caption` fetches a remote aerial feature vocabulary;
  constructing `ImageCaptioner` can download a spaCy model and BLIP model.

## detectree2 tree crown delineation

- Import path: `samgeo.detectree2`.
- Purpose: tree crown delineation using external detectree2/Detectron2.
- Key API: `TreeCrownDelineator`, `tile_orthomosaic`, `prepare_training_data`,
  `stitch_predictions`, `list_pretrained_models`, `download_sample_data`.
- Status in this skill: optional gap. The module import is documented, but the
  runtime requires `detectree2` and Detectron2 compatibility that was not
  prepared for the default scope.

## FER / feature edge reconstruction

- Import path: `samgeo.fer` and `samgeo.common.regularize_legacy` style paths.
- Extra: `segment-geospatial[fer]`.
- Purpose: GDAL/geometry-heavy feature edge reconstruction.
- Status in this skill: optional gap. `osgeo`/GDAL was intentionally not
  installed in the default environment because FER was not a selected primary
  workflow.
