# VOC Workflow

## Expected VOC tree

The repository converter expects the Pascal VOC layout below.
The `ImageSets/Main/*.txt` split files list image ids without file extensions.

```text
<VOC_ROOT>/
├── train/
│   └── VOCdevkit/
│       ├── VOC2007/
│       │   ├── Annotations/
│       │   ├── JPEGImages/
│       │   └── ImageSets/Main/trainval.txt
│       └── VOC2012/
│           ├── Annotations/
│           ├── JPEGImages/
│           └── ImageSets/Main/trainval.txt
└── test/
    └── VOCdevkit/
        └── VOC2007/
            ├── Annotations/
            ├── JPEGImages/
            └── ImageSets/Main/test.txt
```

The converter joins each image id to `JPEGImages/<id>.jpg` and `Annotations/<id>.xml`.
If the split file is wrong, the converter will silently miss data or fail on missing files.

## What the repo converter does

The repository-maintained VOC converter:

- uses the 20 Pascal VOC class names in fixed order
- skips `difficult=1` boxes on the main code path
- writes one annotation row per image in the YOLO row format
- overwrites the default `./data/dataset/voc_train.txt` and `./data/dataset/voc_test.txt` files before writing new ones

That means you should back up custom annotation lists before re-running the conversion.

## Safe conversion sequence

1. Confirm the VOC tree and split files exist.
2. Run the repository's VOC conversion step so the default output paths land under `./data/dataset/`.
3. Update `core/config.py` if you are using non-default class or annotation paths.
4. Validate the generated rows with the bundled checker.
5. Only then hand the data to the training or evaluation sub-skills.

Example validation step after conversion:

```bash
python scripts/validate_yolo_annotations.py data/dataset/voc_train.txt \
  --class-file data/classes/voc.names \
  --anchor-file data/anchors/basline_anchors.txt \
  --check-images --image-root <VOC_ROOT>/train/VOCdevkit/VOC2007
```

Use the matching `test` root when checking `voc_test.txt`.

## Tiny conversion plan for smoke tests

For a small, safe planning case, create the minimum tree for one train image and one test image:

- one JPEG and one XML in the relevant `JPEGImages/` and `Annotations/` directories
- one line in the matching split file that names the image id without an extension
- a VOC class name that exists in `voc.names`

This is enough to confirm that the converter, annotation schema, and validator agree before you scale up to the full dataset.
