# Optional model workflows

## FastSAM workflow

```python
from samgeo.fast_sam import SamGeo

sam = SamGeo(model="FastSAM-x.pt")
sam.set_image("image.tif", device="cuda")
sam.everything_prompt(output="fast-masks.tif")
sam.raster_to_vector("fast-masks.tif", "fast-masks.gpkg")
```

Prompt variants:

```python
sam.point_prompt(points=[[100, 200]], pointlabel=[1], output="point.tif")
sam.box_prompt(bbox=[50, 50, 300, 300], output="box.tif")
sam.text_prompt(text="building", output="text.tif")
```

## HQ-SAM workflow

```python
from samgeo.hq_sam import SamGeo

sam = SamGeo(model_type="vit_h", automatic=True, device="cuda")
sam.generate("image.tif", output="hq-masks.tif", unique=True)
sam.tiff_to_geojson("hq-masks.tif", "hq-masks.geojson")
```

Prompt mode follows the SAM1 pattern:

```python
sam = SamGeo(model_type="vit_h", automatic=False, device="cuda")
sam.set_image("image.tif")
sam.predict(point_coords=[[100, 200]], point_labels=[1], output="hq-point.tif")
```

## LangSAM text prompts

```python
from samgeo.text_sam import LangSAM

sam = LangSAM(model_type="vit_h")
sam.predict(
    image="image.tif",
    text_prompt="building",
    box_threshold=0.25,
    text_threshold=0.24,
    output="text-masks.tif",
)
sam.raster_to_vector("text-masks.tif", "text-masks.gpkg")
```

Batch text prompts:

```python
sam.predict_batch(
    images=["tile-1.tif", "tile-2.tif"],
    out_dir="text-batch",
    text_prompt="tree",
    box_threshold=0.25,
    text_threshold=0.24,
    merge=True,
)
```

## Captioning workflow

Use captioning only when network/model assets are allowed.

```python
from samgeo.caption import ImageCaptioner

captioner = ImageCaptioner(
    blip_model_name="Salesforce/blip-image-captioning-base",
    spacy_model_name="en_core_web_sm",
)
caption, features = captioner.analyze("image.jpg", include_features="default")
print(caption)
print(features)
```

For a known caption string, `extract_features_from_caption(...)` still creates
a default captioner, so it can trigger spaCy/BLIP setup. For pure string parsing
without downloads, write a small custom parser from the vocabulary instead of
using the convenience function.

## detectree2 and FER paths

Only proceed if the user explicitly selects these optional workflows:

```python
from samgeo.detectree2 import TreeCrownDelineator

delineator = TreeCrownDelineator(model_name="default", device="cuda")
delineator.predict("orthomosaic.tif", "crowns.gpkg")
```

This requires external `detectree2` and Detectron2 installation first.

FER/GDAL paths require `osgeo`/GDAL and are not part of the default skill scope.
Prefer normal `raster_to_vector`, `regularize`, or `smooth_vector` unless the
user specifically asks for FER.
