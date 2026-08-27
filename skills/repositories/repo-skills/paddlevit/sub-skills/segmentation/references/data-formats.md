# Segmentation data formats

The built-in dataset classes return images as RGB CHW arrays/tensors and
integer indexed masks. Training applies paired transforms; validation returns a
label for metric computation. Masks are grayscale/paletted class-index images,
not RGB color visualizations. The common ignore id is 255, but always follow
the selected config and dataset implementation.

## Factory keys and defaults

| `DATA.DATASET` | Default classes | Physical root contract |
|---|---:|---|
| `PascalContext` | 60 | VOC-style `JPEGImages`, context PNGs, and split lists |
| `ADE20K` | 150 | `images/{training,validation}` plus matching annotations |
| `Cityscapes` | 19 | `leftImg8bit/{split}` and `gtFine/{split}` city folders |
| `Trans10kV2` | 12 | `{train,validation,test}/{images,masks_12}` |

The factory also contains `Vaihingen`; this sub-skill focuses on the four
requested layouts. Use the exact spelling from the factory, not a humanized
variant.

## Pascal-Context

```text
pascal_context/
├── JPEGImages/<id>.jpg
├── SegmentationClassContext/<id>.png
└── ImageSets/SegmentationContext/
    ├── train.txt
    └── val.txt
```

Each split line is an image id without extension. `PascalContext` appends
`.jpg` and `.png` to the two directories. README preparation artifacts such as
`Annotations`, `SegmentationClass`, `SegmentationObject`, and
`trainval_merged.json` are not the direct pair contract. The
`voc2010_to_pascalcontext.py` converter maps VOC/detail ids to the selected
context class-index space and writes context masks/lists; do not use raw source
ids as model labels without that mapping.

## ADE20K

```text
ADEChallengeData2016/
├── images/
│   ├── training/*.jpg
│   └── validation/*.jpg
└── annotations/
    ├── training/*.png
    └── validation/*.png
```

The implementation scans every file in the chosen image directory and replaces
`.jpg` with `.png`; use matching lowercase `.jpg` names. ADE20K raw masks use
class 0 as the void/background convention. The loader subtracts one; during
training it changes raw-zero-derived 254 back to ignore 255. Effective labels
are therefore 0--149 plus 255 for a 150-class config. A custom reader must
preserve this offset rule or explicitly define another mapping.

## Cityscapes

```text
cityscapes/
├── leftImg8bit/
│   ├── train/<city>/*_leftImg8bit.png
│   ├── val/<city>/*_leftImg8bit.png
│   └── test/<city>/*_leftImg8bit.png
└── gtFine/
    ├── train/<city>/*_gtFine_labelTrainIds.png
    ├── val/<city>/*_gtFine_labelTrainIds.png
    └── test/<city>/*_gtFine_labelTrainIds.png
```

The loader glob-sorts image and label lists and zips by position. A robust
preflight should compare city-relative logical stems as well; equal counts do
not prove correspondence. Training expects `labelTrainIds.png` in the 19-class
space, not polygon JSON or raw label ids. `tools/convert_cityscapes.py` calls
Cityscapes `json2labelImg(..., 'trainIds')` and generates those masks. Its
helper writes labels by replacing the polygon suffix, so stage a copied root
and inspect outputs rather than assuming `--out-dir` relocates each label.

## Trans10kV2

```text
Trans10K_cls12/
├── train/{images/*.jpg,masks_12/*_mask.png}
├── validation/{images/*.jpg,masks_12/*_mask.png}
└── test/{images/*.jpg,masks_12/*_mask.png}
```

The config key is `Trans10kV2`; dataset mode `val` maps to physical
`validation`. The loader sorts images and masks by filename prefixes and zips
them. Validate exact logical stems instead of relying on counts. Typical
configs use 12 classes; some set `TRAIN.IGNORE_INDEX: -1`, while dataset
classes default to 255. Check the loss and actual mask values before changing
that convention.

## Custom tutorial layout

```text
your_dataset/
├── images/
│   ├── training/<id>.<image-suffix>
│   └── validation/<id>.<image-suffix>
└── annotations/
    ├── training/<id>.<mask-suffix>
    └── validation/<id>.<mask-suffix>
```

The tutorial requires a new dataset class to populate `file_list`, implement
suffix/pairing rules, set the class count, and register the exact key in
`src/datasets/__init__.py`. The generic base class does not discover pairs by
itself. Masks must be single-channel/indexed; each pixel is a class index.

Before a custom run, check that:

1. every image has one same-stem label and dimensions match before transforms;
2. labels contain only `0..NUM_CLASSES-1` plus the configured ignore id;
3. train/validation lists are non-empty and disjoint;
4. `DATA.NUM_CLASSES`, loss ignore id, and documented class mapping agree; and
5. the model output geometry matches `DATA.CROP_SIZE` and validation resizing.

`--img_dir` for the demo is different: it is an unlabeled, image-only
prediction directory, not a train/val dataset root.

## Tensor and transform rules

`Compose` reads OpenCV BGR, converts to RGB, applies transforms, and transposes
HWC to CHW. Images use bilinear resize; labels use nearest-neighbor. Training
ADE20K uses scale/crop/flip/distortion/normalization; Trans10kV2 uses resize,
flip, and normalization; other dataset keys are not covered by the current
`get_transforms` helper and may require explicit transform lists. Validation
uses configured resize, optional size-divisor/slide geometry, and `VAL.MEAN` /
`VAL.STD`. Never normalize or bilinear-resize a label.

## Conversion and COCO boundary

VOC/Pascal-Context and Cityscapes converters require optional external
packages and may write into dataset trees. They are not read-only preflight
scripts. Run only on an approved copied/staged output root.

COCO polygon/RLE annotations are a different contract. They must be rasterized
with an explicit category/overlap policy into single-channel class-index masks
and registered through a dataset implementation before this toolkit can use
them. A COCO JSON is not a drop-in value for `DATA.DATASET` here.
