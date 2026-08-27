# Troubleshooting

Use this file for layout and asset-placement failures only. Route dependency, CUDA, Cython, OpenCV, TensorFlow, or NMS build problems to `installation-and-configuration`. Route command-shape, training, evaluation, or demo runtime problems to `training-and-evaluation` or `inference-and-demo`.

## Common failures and what they mean

### `Unknown dataset: ...`

`get_imdb()` only accepts the exact registry keys listed in `references/data-layouts.md`.

Typical fixes:

- For single-dataset evaluation or dataset inspection, use a direct registry key such as `voc_2007_test` or `coco_2014_minival`.
- For combined training sets like `voc_2007_trainval+voc_2012_trainval`, use the launcher path that splits on `+`; do not pass that string to `get_imdb()` directly.

### VOC path errors

Symptoms:

- `VOCdevkit path does not exist`
- `Path does not exist: .../VOC2007`
- `Path does not exist: .../ImageSets/Main/train.txt`
- `Path does not exist: .../JPEGImages/<id>.jpg`

Meaning:

- The repo expects `data/VOCdevkit2007/VOC2007` and `data/VOCdevkit2012/VOC2012`.
- The constructor reads `ImageSets/Main/<split>.txt` and then expects matching JPEG and XML files.

Fix:

- Restore the exact directory tree in `references/data-layouts.md`.
- If you reused a generic `VOCdevkit` folder, rename or symlink it to the versioned layout.

### COCO path or split errors

Symptoms:

- `Path does not exist: .../annotations/instances_*.json`
- `Path does not exist: .../images/<split>/COCO_<split>_*.jpg`
- `ImportError: No module named pycocotools`

Meaning:

- `data/coco` is missing the source-expected annotation/image layout.
- `coco_2014_minival` and `coco_2014_valminusminival` rely on split JSONs that may need to be prepared separately.
- `pycocotools` is an install issue, not a layout issue.

Fix:

- Confirm the exact annotation filename for the registry key.
- Confirm the image directory that `coco.py` will derive from the split name.
- Route missing Python packages to `installation-and-configuration`.

### Stale roidb cache after data edits

Symptoms:

- Dataset loads but boxes/classes do not reflect recent annotation changes.
- Old counts or old image lists appear after updating split files.

Meaning:

- `imdb.gt_roidb()` loaded a cached pickle from `data/cache`.

Fix:

- Delete the affected `data/cache/<imdb-name>_gt_roidb.pkl` file.
- Re-run the dataset constructor or validation.

### Missing pretrained checkpoint sidecars

Symptoms:

- `...ckpt.meta not found`
- `Did you download the proper networks from our server and place them properly?`
- TensorFlow restore errors on a checkpoint basename that looks correct.

Meaning:

- The checkpoint basename exists in name only, or only part of the TensorFlow checkpoint bundle was copied.

Fix:

- Ensure the checkpoint prefix and its `.meta`, `.index`, and `.data-00000-of-00001` files are together.
- For the demo VOC 07+12 asset, keep the symlink under `output/res101/voc_2007_trainval+voc_2012_trainval/default/`.

### Missing ImageNet weights for training

Symptoms:

- Training launcher points to `data/imagenet_weights/<NET>.ckpt` but the file is absent.

Meaning:

- The model initialization archive was not unpacked or renamed to the repo's expected basename.

Fix:

- Place the file at `data/imagenet_weights/<NET>.ckpt`.
- Use the filenames expected by `experiments/scripts/train_faster_rcnn.sh`: `vgg16.ckpt`, `res50.ckpt`, `res101.ckpt`, `res152.ckpt`, or `mobile.ckpt`.

### Demo images missing

Symptoms:

- `cv2.imread` returns `None` for one of the bundled demo files.

Meaning:

- The five `data/demo/*.jpg` files are missing or renamed.

Fix:

- Restore the exact filenames listed in `references/data-layouts.md`.

## When to hand off to another sub-skill

- Missing CUDA, `nvcc`, Cython build failures, or TensorFlow import issues: `installation-and-configuration`
- Need a dry-run command or launcher semantics: `training-and-evaluation`
- Need demo/inference checkpoint handling: `inference-and-demo`
- Need to understand network class APIs instead of asset placement: `api-and-architecture`

## Safe validation

If the issue is only folder naming or missing files, run the bundled validator instead of reopening the source repository:

```bash
python <skill-dir>/scripts/validate_layout.py --repo-root <repo-root> --check voc
python <skill-dir>/scripts/validate_layout.py --repo-root <repo-root> --check coco
python <skill-dir>/scripts/validate_layout.py --repo-root <repo-root> --check demo-model
python <skill-dir>/scripts/validate_layout.py --repo-root <repo-root> --check imagenet
```
