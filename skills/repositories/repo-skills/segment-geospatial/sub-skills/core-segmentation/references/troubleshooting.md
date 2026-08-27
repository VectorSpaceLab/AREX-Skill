# Core segmentation troubleshooting

## Checkpoint and model-load problems

- If SAM1 cannot find a checkpoint, pass `checkpoint="path/to/sam_vit_h_4b8939.pth"`
  or let `download_checkpoint(model_type="vit_h")` fetch it when network access
  is allowed.
- If SAM2 raises an import error, install `segment-geospatial[samgeo2]`.
- If a Hiera model id fails, use one of `sam2-hiera-tiny`, `sam2-hiera-small`,
  `sam2-hiera-base-plus`, or `sam2-hiera-large`.
- If CUDA is not available, small SAM1/SAM2 tests may run on CPU, but large
  scenes can be impractically slow.

## Prompt-coordinate mistakes

Symptoms:

- Masks appear far from the clicked object.
- Prompt points are outside the image.
- `coords_to_xy` or model prediction returns unexpected pixels.

Recovery:

1. Decide whether prompts are pixel coordinates or geographic coordinates.
2. For geographic coordinates, pass `point_crs="EPSG:4326"` or the actual CRS.
3. Verify the source GeoTIFF has correct CRS metadata.
4. For boxes, confirm order is `[xmin, ymin, xmax, ymax]`.
5. Use a single foreground point and low-resolution image first.

## Empty or noisy masks

- Empty masks can be valid. The package has regression coverage that an all-zero
  mask vectorizes to an empty GeoJSON FeatureCollection rather than crashing.
- If masks are noisy, adjust `points_per_side`, `pred_iou_thresh`,
  `stability_score_thresh`, `min_size`, `max_size`, or postprocessing.
- If masks miss foreground objects, try a different model size, prompt points,
  or image band selection.

## Multi-band and raster issues

- `prepare_image_for_sam` and `read_image_for_sam` convert imagery to contiguous
  uint8 RGB arrays.
- For false-color or non-RGB GeoTIFFs, pass `bands=[5, 3, 1]` or another
  one-based RGB selection.
- If output georeferencing is missing, check whether the source image was a
  georeferenced raster or a plain PNG/JPEG.

## Vector output issues

- Prefer GeoPackage or GeoJSON before Shapefile when debugging.
- Inspect the mask raster before simplifying vectors.
- If the vector file is empty, check mask min/max values before assuming the
  conversion failed.
- If output writing fails, try a local writable directory and a simple `.geojson`
  target first.
