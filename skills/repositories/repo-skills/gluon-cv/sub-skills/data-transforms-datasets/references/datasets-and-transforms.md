# Dataset layouts and data workflows

This reference helps an agent choose a GluonCV dataset class, validate the expected files, and assemble transform/batchify pieces without depending on the original repository checkout.

## Dataset selection checklist

1. Name the task family: classification, detection, instance segmentation, keypoints, semantic segmentation, video/action, tracking, depth, or re-identification.
2. Locate the data root. Many GluonCV classes default to `~/.mxnet/datasets/...`; pass `root=` (and for video, often `setting=`) explicitly when data is elsewhere.
3. Confirm split names before constructing the dataset. Several classes fail at initialization if a split text file or annotation JSON is missing.
4. Verify label format and class list before creating a model or loader. Detection labels should be `[xmin, ymin, xmax, ymax, class_id]` plus optional extra fields.
5. Choose the transform/preset before the `DataLoader`, then choose a `batchify_fn` compatible with the transformed sample tuple.

## Built-in dataset classes and common layouts

| Family | Classes | Typical root/layout | Key arguments and validation |
| --- | --- | --- | --- |
| Image classification | `ImageNet` | `imagenet/train/<class>/...`, `imagenet/val/<class>/...`; default root `~/.mxnet/datasets/imagenet` | `ImageNet(train=True/False, root=..., transform=...)`; can use Gluon vision transforms with `transform_first`. ImageRecord format is separate from this folder dataset. |
| Pascal VOC detection | `VOCDetection`, `CustomVOCDetection`, `CustomVOCDetectionBase` | `voc/VOC2007` or `voc/VOC2012` with `Annotations/*.xml`, `JPEGImages/*.jpg`, `ImageSets/Main/<split>.txt` | `splits=((2007, 'trainval'), (2012, 'trainval'))` by default. Labels are zero-based pixel boxes `[xmin, ymin, xmax, ymax, class_id, difficult]`. Custom VOC-like datasets may use tuple splits such as `((2018, 'train'),)` or a custom subfolder. |
| Pascal VOC segmentation | `VOCSegmentation`, `VOCAugSegmentation` | `voc/VOC2012/JPEGImages`, `SegmentationClass`, `ImageSets/Segmentation`; augmented data under `voc/VOCaug/dataset` | `split='train'|'val'|'test'`, `mode` controls training/validation/test transforms. |
| COCO detection/instance/keypoints | `COCODetection`, `COCOInstance`, `COCOKeyPoints`, `COCODetectionDALI` | `coco/train2017`, `coco/val2017`, `coco/annotations/*.json` | Splits are annotation names without `.json`, e.g. `instances_train2017`, `instances_val2017`, `person_keypoints_val2017`. Requires `pycocotools` for normal dataset classes; DALI reader is optional and GPU/data-pipeline-specific. Category names must match the class list. |
| COCO semantic segmentation | `COCOSegmentation` | `coco/train2017`, `coco/val2017`, `coco/annotations/instances_*.json`, generated id caches | `split='train'|'val'`; uses COCO annotations and generated ids. |
| ADE20K semantic segmentation | `ADE20KSegmentation` | `ade/ADEChallengeData2016/images/{training,validation}` and `annotations/{training,validation}` | `root` defaults to `~/.mxnet/datasets/ade`; splits are train/val. |
| Cityscapes semantic segmentation | `CitySegmentation` | `citys/leftImg8bit/{train,val,test}` and `citys/gtFine/{train,val,test}` | Requires files downloaded from the Cityscapes site; helper cannot download without credentials. |
| Multi-human parsing | `MHPV1Segmentation` | `mhp/LV-MHP-v1/images` and `annotations` | Large parsing dataset; treat helper as reference-only. |
| VisDrone detection | `VisDroneDetection` | `visdrone/<split>/images` and `visdrone/<split>/annotations/*.txt` | Splits default to `('train',)`. VisDrone annotation text uses width/height-style boxes converted by the dataset. |
| Custom detection list | `LstDetection` | One `.lst` file plus image files under a supplied `root` | LST rows are `index<TAB>header+labels<TAB>relative_image_path`; use `coord_normalized=True` for normalized boxes. The loader converts from MXNet ImageDetIter label order to GluonCV `[xmin, ymin, xmax, ymax, id]`. |
| Detection RecordIO | `RecordFileDetection` | `.rec` plus matching `.idx` in the same directory | Intended for MXNet ImageDetIter-compatible RecordIO. Use only if comfortable with RecordIO; pass `coord_normalized=` correctly. |
| Video/action | `UCF101`, `Kinetics400`, `Kinetics700`, `HMDB51`, `SomethingSomethingV2`, `VideoClsCustom` | Decoded frame folders plus setting/list files such as `*_train_list_rawframes.txt`; defaults under `~/.mxnet/datasets/<dataset>` | Common args: `root`, `setting`, `train`, `test_mode`, `name_pattern`, `new_length`, `new_step`, `num_segments`, `num_crop`, `video_loader`, `use_decord`, `slowfast`, `data_aug`, `transform`. Frame tensors typically add an `extra` segment/crop axis and sometimes a temporal/depth axis. |
| Tracking | `OTBTracking`, `TrkDataset` | OTB root or tracking crop datasets with JSON annotations | `OTBTracking(name, dataset_root, load_img=False)` is evaluation-style; `TrkDataset` is for SiamRPN-style training crops and anchors. |
| Depth | `KITTIRAWDataset`, `KITTIOdomDataset`, `KITTIDepthDataset` | KITTI raw/odom/depth folders plus split file lists | Constructors inherit Monodepth-style args such as `data_path`, `filenames`, `height`, `width`, `frame_idxs`, `num_scales`, `is_train`, `img_ext`. |
| Re-identification | `ImageTxtDataset`, `LabelList` for Market1501 | Market1501 folder under `~/.mxnet/datasets/market1501` | Helper functions produce image text lists with person/camera labels; training details route to command/training workflows. |
| Wrappers/samplers | `MixupDetection`, `SplitSampler`, `ShuffleSplitSampler`, `SplitSortedBucketSampler` | Wrap an existing dataset or split indices | Use after the base dataset is already valid. |

## Custom object detection workflows

### Minimal JSON validation before GluonCV

For quick sanity checks, create JSON records like either of these:

```json
{
  "classes": ["dog", "bike"],
  "records": [
    {"image": "images/0001.jpg", "width": 640, "height": 480,
     "boxes": [[10, 20, 110, 200, 0], [50, 60, 300, 350, "bike"]]}
  ]
}
```

```json
[
  {"image_path": "images/0001.jpg", "annotations": [
    {"bbox": [10, 20, 110, 200], "class_id": 0}
  ]}
]
```

Then run the bundled validator before constructing a `LstDetection`, VOC-like dataset, or training command:

```bash
python sub-skills/data-transforms-datasets/scripts/validate_detection_record.py annotations.json --image-root /data/my-dataset --check-files
```

What it checks:

- Records contain an image path.
- Classes are non-empty when present, and class ids/names resolve.
- Every box is finite and ordered as `xmin < xmax`, `ymin < ymax`.
- Negative coordinates and out-of-bounds coordinates are rejected by default when dimensions are known.
- Image file existence is checked only when `--check-files` is supplied.

### VOC-like custom data

Use a VOC-like layout when you already have XML annotations:

```text
VOC2018/
  Annotations/000001.xml
  JPEGImages/000001.jpg
  ImageSets/Main/train.txt
```

Subclass `VOCDetection`, override `CLASSES`, and pass `root` plus `splits=((2018, 'train'),)`. GluonCV subtracts 1 from VOC XML coordinates and returns zero-based pixel boxes. If class names are generated from annotations, ensure they are lowercase and stable before aligning model heads.

### LST and RecordIO custom data

Use LST when you want a compact list file compatible with MXNet RecordIO tooling. Each row contains an integer index, a variable-length label block, and a relative image path separated by tabs. The detection label block follows the MXNet ImageDetIter convention with a header and per-object fields. `LstDetection` and `RecordFileDetection` convert the loaded labels to GluonCV coordinate columns:

```text
[xmin, ymin, xmax, ymax, class_id, extra0, ...]
```

Use RecordIO only when IO performance is a real bottleneck; malformed `.rec`/`.idx` pairs are harder to inspect than raw images plus JSON/VOC/LST.

## Transform and loader recipes

### Detection training/validation data

1. Construct the dataset (`VOCDetection`, `COCODetection`, `LstDetection`, or custom subclass).
2. Choose a preset transform matching the detector and image size.
3. Use the batchify pattern expected by the preset/model.

Common patterns from GluonCV tests:

```python
from gluoncv.data import batchify
from gluoncv.data.transforms.presets import ssd, rcnn, yolo

# SSD validation: image stack + variable-length labels.
val_batchify = batchify.Tuple(batchify.Stack(), batchify.Pad(pad_val=-1))

# Faster R-CNN validation: transformed samples are ragged; Append keeps per-sample fields.
rcnn_val_batchify = batchify.Tuple(*[batchify.Append() for _ in range(3)])

# YOLO training commonly stacks target tensors and pads raw labels.
yolo_train_batchify = batchify.Tuple(*([batchify.Stack() for _ in range(6)] +
                                      [batchify.Pad(axis=0, pad_val=-1)]))
```

Route to the model-zoo sub-skill when the transform requires anchors or a `net` object.

### Semantic segmentation data

Use `get_segmentation_dataset(name, **kwargs)` for names `ade20k`, `pascal_voc`, `pascal_aug`, `coco`, `citys`, and `mhpv1`, or instantiate the class directly when explicit root/split/mode control is needed. Multi-scale evaluation uses `ms_batchify_fn` for segmentation samples.

### Video/action data without downloads

Video dataset helpers are designed around either decoded frames or direct video loading:

- Decoded frame mode: `root` points at a rawframes directory; `setting` is a text list built by the dataset preparation helper; `name_pattern` controls frame filenames such as `img_%05d.jpg` or `%06d.jpg`.
- Direct video mode: set `video_loader=True`; use `use_decord=True` only if `decord` is installed and you explicitly want direct video decoding.
- Multi-segment/multi-crop evaluation changes output shape: expect an `extra` dimension for segments/crops and a temporal/depth dimension when `new_length > 1`.

If the user cannot download UCF101/Kinetics/HMDB51, still provide the expected folder/list contract and a no-network plan: place local videos/frames under a chosen root, build a setting list with relative paths, frame counts, and class ids, and set `root`/`setting` explicitly.

## Dataset preparation helper scripts are reference-only

The upstream dataset helpers mostly download or convert large archives. Treat them as recipes to plan data acquisition; do not run them unless the user approves network/storage/time side effects.

| Helper family | Important flags and outputs | Notes |
| --- | --- | --- |
| ADE20K, MHP, Cityscapes | `--download-dir`; extracted segmentation folders | Cityscapes requires manual credentialed downloads. |
| Pascal VOC | `--download-dir`, `--no-download`, `--overwrite`; extracts VOC 2007/2012 and VOCaug | Use `--no-download` only when all archives already exist. |
| COCO | `--download-dir`, `--no-download`, `--overwrite`; expects `train2017`, `val2017`, `annotations` | COCO classes require `pycocotools` at runtime. |
| ImageNet | `--download-dir`, `--target-dir`, `--checksum`, `--with-rec`, `--num-thread` | `--with-rec` builds ImageRecord files; raw folder dataset and RecordIO are separate workflows. |
| UCF101, HMDB51, Kinetics400 | `--download_dir`, `--src_dir`, `--out_dir`, `--frame_path`, `--anno_dir`, `--out_list_path`, `--decode_video`, `--build_file_list`, `--new_width`, `--new_height`, `--num_worker`, `--format`, `--resume`, `--tiny_dataset` | Frame extraction is CPU/storage-heavy; optical flow options require dense-flow tooling and often GPUs. Kinetics defaults do not download unless requested. |
| Something-Something-V2 | `--video_root`, `--frame_root`, `--anno_root`, `--num_threads`, `--decode_video`, `--build_file_list` | User must provide annotations; frame names default to `%06d.jpg`. |
| Market1501 | `--download-dir`, `--no-download`; produces label/list files | Re-id training routes to command/training guidance. |
| OTB / tracking COCO/VID/DET | `--download-dir`, `--instance-size`, `--num-threads`, sometimes `--no-download`/`--overwrite` | Crops exemplar/search patches and generates tracking JSON. Storage-heavy. |
| RecordIO/ImageRecord | `--with-rec` or external `im2rec.py` with `--recursive`, `--list`, `--pass-through`, `--pack-label`, `--no-shuffle`, `--num-thread` | Use when high-throughput IO matters and labels have already been validated. |

## Metrics and visualization support

Use metrics and visualization as data sanity checks, not as substitutes for training/evaluation orchestration:

- Detection visualization: `gluoncv.utils.viz.plot_bbox(img, bboxes, scores=None, labels=None, class_names=...)`; use `absolute_coordinates=True` for pixel boxes.
- Image visualization: `plot_image(img)`.
- Segmentation visualization: `get_color_pallete(npimg, dataset='pascal_voc')`.
- Detection metrics: `VOCMApMetric`, `VOC07MApMetric`, `COCODetectionMetric`; COCO metrics require a dataset object and often `pycocotools`.
- Segmentation metrics: `SegmentationMetric(nclass)`, `pixelAccuracy`, `intersectionAndUnion`.
- Instance/keypoint/tracking metrics exist but often need task-specific dataset result formats; route full evaluation command construction to the training/evaluation sub-skill.
