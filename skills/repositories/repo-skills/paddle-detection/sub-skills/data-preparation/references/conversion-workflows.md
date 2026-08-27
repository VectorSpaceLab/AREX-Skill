# Conversion and Preparation Workflows

## LabelMe or custom JSON to COCO

Use a source-checkout conversion command only after validating file names and labels. The documented `tools/x2coco.py` flow accepts a dataset type, JSON input directory, image input directory, output directory, and train/validation/test proportions. The generated dataset should have `annotations/train.json`, `annotations/valid.json`, and an `images/` directory. Avoid non-ASCII paths when the target platform or image decoder is not known.

```bash
python tools/x2coco.py \
  --dataset_type labelme \
  --json_input_dir ./labelme_annos \
  --image_input_dir ./labelme_imgs \
  --output_dir ./coco_custom \
  --train_proportion 0.8 \
  --val_proportion 0.2 \
  --test_proportion 0.0
```

The command is network-free but writes a new dataset; use a disposable output directory and validate the result with the bundled checker.

## Semi-supervised COCO split

`tools/gen_semi_coco.py` selects a percentage of images, optionally using a saved supervision-index JSON and seed. It writes labeled and unlabeled files beneath `semi_annotations/`. Record `percent`, `seed`, `seed_offset`, and the input annotation checksum; a later run must reproduce the same split.

## Small-object slicing

`tools/slice_image.py` delegates to optional `sahi`. Inputs are an image directory, COCO JSON, output directory, slice size, and overlap ratio. Installation of `sahi` is optional and should be isolated from the base environment. For inference-time slicing, `tools/infer.py`/`tools/eval.py` additionally expose slice size, overlap ratio, combine method (`nms`, `nmm`, or `concat`), match threshold, and match metric.

## Download helpers

COCO/VOC/road-sign/MOT download scripts and pipeline model download helpers write caches and use external URLs. Treat them as explicit network operations. Prefer pre-staged data with checksums for reproducible runs, and never let an automatic download silently change a benchmark or training set.
