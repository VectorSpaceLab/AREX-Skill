---
name: data-preparation
description: "Route for SSD Keras dataset parsing, validation, augmentation, and
  batch generation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Data Preparation

Use this route when the task is about getting object-detection data into a shape that the SSD workflows can use safely.

## What this route covers

- parsing CSV annotations
- parsing Pascal VOC XML annotations
- parsing COCO-style JSON annotations
- loading and reloading HDF5 datasets
- validating boxes, labels, and image sizes
- generating batches with `DataGenerator`
- applying resize and augmentation chains
- converting predictions back to the original image frame with inverse transforms

## What this route excludes

- building or compiling models
- loss configuration
- decoding predictions or evaluating mAP
- transfer learning / weight sampling

Send those tasks to `training` or `inference-evaluation`.

## First things to check

1. Open `references/data-formats.md` to confirm the expected annotation layout.
2. Open `references/compatibility.md` if imports are failing in the environment.
3. Open `references/model-architecture.md` if the data must feed `SSDInputEncoder`.
4. Run `scripts/smoke.py` when you want a tiny synthetic parser / generator check.

## Typical workflow

### 1. Choose the source format

- CSV is easiest for ad hoc detection datasets.
- VOC XML is the best fit for the Pascal VOC splits used in the notebooks.
- JSON is the right path for COCO-style datasets and COCO evaluation.
- HDF5 is useful when you want a reusable cached dataset for faster iteration.

### 2. Verify label conventions

- Keep background as class 0 on the model side.
- Make sure the label order is the one your parser and generator expect.
- Confirm that every transform sees the same `labels_format` mapping.

### 3. Parse and validate

- Use the parser that matches the dataset source.
- Drop or flag degenerate boxes early.
- Decide whether empty images should stay in the batch.
- If boxes disappear after cropping or scaling, loosen the validity filters before changing the labels themselves.

### 4. Generate batches

- Use `Resize` plus `ConvertTo3Channels` for a simple deterministic smoke path.
- Add augmentation chains only after the basic parser / generator flow is stable.
- For training, wire the generator to `SSDInputEncoder` through the training route.
- For evaluation, keep the inverse transforms so predictions can be mapped back to the original image coordinates.

### 5. Cache when it helps

- If the source annotations are expensive to parse repeatedly, build an HDF5 cache.
- Reuse the cache only when the source images and labels are still the same.

## Useful source objects

- `DataGenerator`
- `parse_csv`
- `parse_xml`
- `parse_json`
- `create_hdf5_dataset`
- `generate`
- `BoxFilter`
- `ImageValidator`
- `BoundGenerator`
- `Resize`
- `ConvertTo3Channels`
- `SSDDataAugmentation`
- `DataAugmentationConstantInputSize`
- `DataAugmentationVariableInputSize`
- `DataAugmentationSatellite`
- `apply_inverse_transforms`

## Quick decision guide

- Need a safe parser smoke? Use the bundled script and a tiny synthetic fixture.
- Need the full training path? Go to `training` after the data contract is fixed.
- Need evaluation or visualisation with transformed images? Keep the inverse transforms and go to `inference-evaluation`.
