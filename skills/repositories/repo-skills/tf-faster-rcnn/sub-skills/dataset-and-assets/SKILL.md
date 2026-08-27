---
name: dataset-and-assets
description: "Prepare, validate, and troubleshoot tf-faster-rcnn dataset
  folders, registry names, roidb caches, pretrained checkpoints, ImageNet
  initialization weights, and output/tensorboard artifact paths without
  downloads or training."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# dataset-and-assets

Use this sub-skill when a future Researcher needs to place or validate VOC/COCO data, understand dataset registry names, reason about `roidb` and `data/cache`, place pretrained Faster R-CNN checkpoints or ImageNet initialization weights, or locate generated output and TensorBoard artifacts for `tf-faster-rcnn`.

Do **not** use this sub-skill for dependency installation, Cython/CUDA build failures, TensorFlow compatibility, or NMS extension import errors; route those to `installation-and-configuration`. Do **not** include or construct training/test/demo commands here; route command construction and runtime choices to `training-and-evaluation` or `inference-and-demo`.

## Operating inputs

- A checkout root, referenced below as `<repo-root>`.
- An intended dataset family: PASCAL VOC, COCO, the bundled `data/demo` images, pretrained Faster R-CNN checkpoint assets, and/or ImageNet initialization weights.
- Whether the user wants a read-only validation of paths or instructions for arranging existing local/downloaded assets. Never download from this sub-skill without explicit user approval; the bundled validator performs no network access.

## Exact dataset registry keys

`lib/datasets/factory.py` registers 23 keys. Use these exact strings for `--imdb` values and for roidb/cache names:

- VOC 2007: `voc_2007_train`, `voc_2007_val`, `voc_2007_trainval`, `voc_2007_test`
- VOC 2012: `voc_2012_train`, `voc_2012_val`, `voc_2012_trainval`, `voc_2012_test`
- VOC 2007 difficult-inclusive variants: `voc_2007_train_diff`, `voc_2007_val_diff`, `voc_2007_trainval_diff`, `voc_2007_test_diff`
- VOC 2012 difficult-inclusive variants: `voc_2012_train_diff`, `voc_2012_val_diff`, `voc_2012_trainval_diff`, `voc_2012_test_diff`
- COCO 2014: `coco_2014_train`, `coco_2014_val`, `coco_2014_minival`, `coco_2014_valminusminival`, `coco_2014_trainval`
- COCO 2015: `coco_2015_test`, `coco_2015_test-dev`

`voc_2007_trainval+voc_2012_trainval` and `coco_2014_train+coco_2014_valminusminival` are not registry keys accepted directly by `get_imdb`; they are combined training-set strings split by `tools/trainval_net.py`. Route command use of those combined strings to `training-and-evaluation`.

## Asset workflow

1. Establish `<repo-root>` and treat `<repo-root>/data` as `cfg.DATA_DIR`.
2. Pick the registry key(s) or source-supported combined training string needed by the downstream task.
3. Validate the intended layout with the bundled script:

   ```bash
   python <skill-dir>/scripts/validate_layout.py --repo-root <repo-root> --check voc
   python <skill-dir>/scripts/validate_layout.py --repo-root <repo-root> --check coco
   python <skill-dir>/scripts/validate_layout.py --repo-root <repo-root> --check demo-model
   python <skill-dir>/scripts/validate_layout.py --repo-root <repo-root> --check imagenet
   ```

   Omit `--check` to run all layout checks. The script reports deterministic JSON and exits nonzero when required expected paths for the selected check are absent.
4. If data annotations or image-set files changed, remove stale `data/cache/<imdb-name>_gt_roidb.pkl` files before the next dataset constructor run.
5. For pretrained checkpoint placement and output/TensorBoard path reasoning, use `references/model-artifacts.md`.

## Reference map

- `references/data-layouts.md`: VOC/COCO folder contracts, exact registry keys, image-name patterns, `roidb` dict fields, cache semantics, and safe validation examples.
- `references/model-artifacts.md`: pretrained Faster R-CNN checkpoint layout, `data/imagenet_weights` naming, snapshot sidecars, demo-model symlink layout, and output/TensorBoard path formulas.
- `references/troubleshooting.md`: common missing-path, stale-cache, split-file, checkpoint-sidecar, and route-to-other-sub-skill decisions.
- `scripts/validate_layout.py`: safe stdlib-only path/name validator; no imports from the legacy repo, no downloads, no dataset parsing, no TensorFlow execution.

## Guardrails

- Do not run `data/scripts/fetch_faster_rcnn_models.sh` automatically. It downloads a large archive and depends on an old external server.
- Do not assert full COCO/VOC data correctness from path checks alone; this sub-skill validates expected paths and names, not annotation content.
- Do not treat CUDA/NVCC/TensorFlow errors as dataset problems. Route install/build/backend failures to `installation-and-configuration`.
- Do not generate training/test commands in this sub-skill. Route commands, iterations, config overrides, snapshots, resume behavior, and benchmark evaluation to `training-and-evaluation`.
