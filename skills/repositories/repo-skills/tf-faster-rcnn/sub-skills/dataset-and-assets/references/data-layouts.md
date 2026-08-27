# Data layouts, registry names, and roidb/cache behavior

This repo uses `<repo-root>/data` as `cfg.DATA_DIR`. Dataset constructors build paths relative to that directory; they do not search arbitrary external dataset roots.

## Dataset registry

`lib/datasets/factory.py` registers exactly these names:

| Family | Registry keys |
| --- | --- |
| VOC 2007 | `voc_2007_train`, `voc_2007_val`, `voc_2007_trainval`, `voc_2007_test` |
| VOC 2012 | `voc_2012_train`, `voc_2012_val`, `voc_2012_trainval`, `voc_2012_test` |
| VOC 2007 including difficult objects | `voc_2007_train_diff`, `voc_2007_val_diff`, `voc_2007_trainval_diff`, `voc_2007_test_diff` |
| VOC 2012 including difficult objects | `voc_2012_train_diff`, `voc_2012_val_diff`, `voc_2012_trainval_diff`, `voc_2012_test_diff` |
| COCO 2014 | `coco_2014_train`, `coco_2014_val`, `coco_2014_minival`, `coco_2014_valminusminival`, `coco_2014_trainval` |
| COCO 2015 | `coco_2015_test`, `coco_2015_test-dev` |

Important distinction:

- `get_imdb(name)` accepts only the exact registry keys above.
- Training code can accept combined strings such as `voc_2007_trainval+voc_2012_trainval` because `tools/trainval_net.py` splits the string on `+`, loads each component with `get_imdb`, concatenates the roidbs, and creates a synthetic combined `imdb` name.
- The launcher-supported combined examples are `voc_2007_trainval+voc_2012_trainval` and `coco_2014_train+coco_2014_valminusminival`. Route launcher details to `training-and-evaluation`.

## PASCAL VOC layout

The VOC constructor expects a versioned devkit directory. A generic `data/VOCdevkit/VOC2007` layout is not sufficient unless it is symlinked or renamed to the versioned layout below.

```text
<repo-root>/data/
  VOCdevkit2007/
    VOC2007/
      JPEGImages/
        <image-id>.jpg
      Annotations/
        <image-id>.xml
      ImageSets/
        Main/
          train.txt
          val.txt
          trainval.txt
          test.txt
      results/                 # created/used by VOC evaluation
  VOCdevkit2012/
    VOC2012/
      JPEGImages/
      Annotations/
      ImageSets/
        Main/
          train.txt
          val.txt
          trainval.txt
          test.txt
      results/
```

Source-derived path formulas:

- Default devkit path: `data/VOCdevkit<year>`
- Data path: `data/VOCdevkit<year>/VOC<year>`
- Image-set list: `data/VOCdevkit<year>/VOC<year>/ImageSets/Main/<split>.txt`
- Image file: `data/VOCdevkit<year>/VOC<year>/JPEGImages/<image-id>.jpg`
- Annotation file: `data/VOCdevkit<year>/VOC<year>/Annotations/<image-id>.xml`
- VOC result-file template: `data/VOCdevkit<year>/results/VOC<year>/Main/<comp-id>_det_<split>_<class>.txt`

VOC classes are fixed to 20 foreground classes plus `__background__`: `aeroplane`, `bicycle`, `bird`, `boat`, `bottle`, `bus`, `car`, `cat`, `chair`, `cow`, `diningtable`, `dog`, `horse`, `motorbike`, `person`, `pottedplant`, `sheep`, `sofa`, `train`, `tvmonitor`.

`*_diff` registry keys pass `use_diff=True`; non-diff keys exclude annotation objects whose `difficult` field is `1`.

The README states that Faster R-CNN does not rely on pre-computed external proposal files in the normal RPN workflow, so py-faster-rcnn proposal-setup steps can be ignored for this repo unless a user deliberately selects an RPN-file proposal path.

## COCO layout

The COCO constructor expects a local COCO root at `data/coco` plus the Python COCO API available in the environment. If Python raises `ImportError` for `pycocotools`, route to `installation-and-configuration`; this sub-skill only covers the data paths.

```text
<repo-root>/data/
  coco/
    annotations/
      instances_train2014.json
      instances_val2014.json
      instances_minival2014.json
      instances_valminusminival2014.json
      instances_trainval2014.json
      image_info_test2015.json
      image_info_test-dev2015.json
    images/
      train2014/
        COCO_train2014_000000119993.jpg
      val2014/
        COCO_val2014_000000447991.jpg
      trainval2014/
        COCO_trainval2014_<12-digit-id>.jpg
      test2015/
        COCO_test2015_<12-digit-id>.jpg
```

Source-derived annotation formulas:

- Non-test COCO split: `data/coco/annotations/instances_<image_set><year>.json`
- Test split: `data/coco/annotations/image_info_<image_set><year>.json`

Source-derived image formulas:

- Base image root: `data/coco/images/<data-name>`
- File pattern: `COCO_<data-name>_<12-digit-id>.jpg`
- Example from source comment: `images/train2014/COCO_train2014_000000119993.jpg`

View mapping used by `lib/datasets/coco.py`:

| Registry key | Annotation file | Image directory used |
| --- | --- | --- |
| `coco_2014_train` | `instances_train2014.json` | `images/train2014` |
| `coco_2014_val` | `instances_val2014.json` | `images/val2014` |
| `coco_2014_minival` | `instances_minival2014.json` | `images/val2014` |
| `coco_2014_valminusminival` | `instances_valminusminival2014.json` | `images/val2014` |
| `coco_2014_trainval` | `instances_trainval2014.json` | `images/trainval2014` |
| `coco_2015_test` | `image_info_test2015.json` | `images/test2015` |
| `coco_2015_test-dev` | `image_info_test-dev2015.json` | `images/test2015` |

The `minival` and `valminusminival` JSONs are py-faster-rcnn-style split files; standard COCO downloads do not always include them under those names.

## Demo images

The checkout includes five tiny demo images under `data/demo`:

- `000456.jpg`
- `000542.jpg`
- `001150.jpg`
- `001763.jpg`
- `004545.jpg`

`tools/demo.py` reads these by joining `cfg.DATA_DIR`, `demo`, and the exact image names above. Missing demo images are an asset-layout issue; runtime OpenCV, display, TensorFlow, and NMS errors should be routed to `inference-and-demo` or `installation-and-configuration` depending on the failure.

## roidb and cache semantics

`imdb.roidb` is a lazy property. On first access it calls the active `roidb_handler` and stores the result on the `imdb` object. The default handler for VOC and COCO is ground-truth roidb (`gt_roidb`).

Cache path:

```text
<repo-root>/data/cache/<imdb-name>_gt_roidb.pkl
```

The cache directory is created automatically when `imdb.cache_path` is accessed. If an existing cache file is present, the dataset constructor loads it and does not re-read annotation XML/JSON. Delete the specific cache file after changing annotations, split lists, category mappings, or image dimensions.

Ground-truth roidb entries contain these keys:

| Key | VOC | COCO | Meaning |
| --- | --- | --- | --- |
| `boxes` | yes | yes | `N x 4` box array in zero-based coordinates |
| `gt_classes` | yes | yes | integer class indices, background is `0` |
| `gt_overlaps` | yes | yes | sparse class-overlap matrix |
| `flipped` | yes | yes | `False` for original examples; `True` for appended horizontal flips |
| `seg_areas` | yes | yes | box/segment areas |
| `width`, `height` | added later by `prepare_roidb` | present in COCO annotation loader | image size |

`roi_data_layer/roidb.py::prepare_roidb(imdb)` adds:

- `image`: absolute path to the image file returned by the dataset object
- `width`, `height` for VOC/non-COCO datasets
- `max_classes`: class with maximum overlap for each ROI
- `max_overlaps`: maximum overlap value for each ROI

Training preparation may call `append_flipped_images`, which doubles the roidb and image index by adding horizontally mirrored boxes. If a user observes unexpected doubled counts, check whether flipped images were enabled before assuming the split files are duplicated.

## Safe validation examples

Run the bundled validator from any directory. It reads only path names and emits JSON:

```bash
python <skill-dir>/scripts/validate_layout.py --repo-root <repo-root> --check voc
python <skill-dir>/scripts/validate_layout.py --repo-root <repo-root> --check coco
python <skill-dir>/scripts/validate_layout.py --repo-root <repo-root> --check demo-model
```

The validator does not import the repo, does not parse XML/JSON annotations, does not create caches, and does not download datasets or checkpoints.
