# Model, checkpoint, output, and TensorBoard artifacts

This reference documents artifact path contracts only. Route command construction, training/test scheduling, config overrides, and full inference/runtime behavior to `training-and-evaluation` or `inference-and-demo`.

## Pretrained Faster R-CNN demo/eval checkpoints

The source downloader `data/scripts/fetch_faster_rcnn_models.sh` is reference-only for this sub-skill. It performs network I/O and should not be run automatically.

Source facts from that script:

- Network: `res101`
- Archive filename: `voc_0712_80k-110k.tgz`
- Documented size message: `340M`
- URL pattern: old external server path ending in `/tf-faster-rcnn/res101/voc_0712_80k-110k.tgz`
- MD5 checksum: `cb32e9df553153d311cc5095b2f8c340`
- The script downloads the archive under `data/` and extracts it from there.

The README shows the expected placement for the pretrained ResNet101 VOC 07+12 checkpoint by creating a symlink under `output`:

```bash
NET=res101
TRAIN_IMDB=voc_2007_trainval+voc_2012_trainval
mkdir -p output/${NET}/${TRAIN_IMDB}
cd output/${NET}/${TRAIN_IMDB}
ln -s ../../../data/voc_2007_trainval+voc_2012_trainval ./default
cd ../../..
```

After that symlink, the default demo path is:

```text
output/res101/voc_2007_trainval+voc_2012_trainval/default/res101_faster_rcnn_iter_110000.ckpt
```

`tools/demo.py` checks for the `.meta` sidecar before restoring:

```text
output/res101/voc_2007_trainval+voc_2012_trainval/default/res101_faster_rcnn_iter_110000.ckpt.meta
```

A normal TensorFlow checkpoint restore also needs the checkpoint basename plus data/index sidecars, typically:

```text
res101_faster_rcnn_iter_110000.ckpt.meta
res101_faster_rcnn_iter_110000.ckpt.index
res101_faster_rcnn_iter_110000.ckpt.data-00000-of-00001
checkpoint                         # optional TensorFlow state file
```

`tools/demo.py` also contains a VGG16 mapping:

```text
--net vgg16 --dataset pascal_voc
output/vgg16/voc_2007_trainval/default/vgg16_faster_rcnn_iter_70000.ckpt
```

The README downloader example is specifically for the ResNet101 VOC 07+12 model; do not assume the VGG16 path is present unless the user supplied matching checkpoint files.

## ImageNet initialization weights

Training initialization uses files under:

```text
data/imagenet_weights/<NET>.ckpt
```

`experiments/scripts/train_faster_rcnn.sh` interpolates `<NET>` directly into `data/imagenet_weights/${NET}.ckpt`. The launcher-supported names are:

```text
data/imagenet_weights/vgg16.ckpt
data/imagenet_weights/res50.ckpt
data/imagenet_weights/res101.ckpt
data/imagenet_weights/res152.ckpt
data/imagenet_weights/mobile.ckpt
```

README examples document these renames from TensorFlow-Slim archives:

- VGG16: extract `vgg_16_2016_08_28.tar.gz`, then rename `vgg_16.ckpt` to `vgg16.ckpt`.
- ResNet101: extract `resnet_v1_101_2016_08_28.tar.gz`, then rename `resnet_v1_101.ckpt` to `res101.ckpt`.

The source tree does not bundle ImageNet weights. If a `.ckpt` file is missing for the requested network, the asset layout is incomplete. If TensorFlow cannot read a present checkpoint, route the runtime error to `training-and-evaluation` or `installation-and-configuration` depending on whether it is a model/TF compatibility issue.

## Training snapshot artifact names

When training runs, `lib/model/train_val.py::snapshot` writes checkpoint artifacts into the selected output directory. The basename formula is:

```text
<TRAIN.SNAPSHOT_PREFIX>_iter_<ITER>.ckpt
```

Network YAMLs set the snapshot prefixes:

| Config file | `EXP_DIR` | `TRAIN.SNAPSHOT_PREFIX` |
| --- | --- | --- |
| `experiments/cfgs/vgg16.yml` | `vgg16` | `vgg16_faster_rcnn` |
| `experiments/cfgs/res50.yml` | `res50` | `res50_faster_rcnn` |
| `experiments/cfgs/res101.yml` | `res101` | `res101_faster_rcnn` |
| `experiments/cfgs/res101-lg.yml` | `res101-lg` | `res101_faster_rcnn` |
| `experiments/cfgs/mobile.yml` | `mobile` | `mobile_faster_rcnn` |

Each snapshot also writes a pickle sidecar with training state:

```text
<TRAIN.SNAPSHOT_PREFIX>_iter_<ITER>.pkl
```

The pickle sidecar stores numpy random state, current data-layer positions, current permutations, validation data-layer positions/permutations, and the iteration. Resume logic expects matching `.ckpt.meta` and `.pkl` files in the output directory.

## Output directory formula

`lib/model/config.py::get_output_dir(imdb, weights_filename)` creates:

```text
output/<EXP_DIR>/<imdb.name>/<weights_filename-or-default>
```

`EXP_DIR` defaults to `default` in config but the provided YAML files normally set it to the network name (`vgg16`, `res101`, `res50`, `res101-lg`, or `mobile`). For train commands, `weights_filename` is the CLI tag or `default`.

Examples:

```text
# Training output for ResNet101 on the launcher VOC 07+12 train set:
output/res101/voc_2007_trainval+voc_2012_trainval/default/

# Expected final checkpoint basename for that schedule:
output/res101/voc_2007_trainval+voc_2012_trainval/default/res101_faster_rcnn_iter_110000.ckpt

# Training output for VGG16 on VOC 2007 trainval:
output/vgg16/voc_2007_trainval/default/vgg16_faster_rcnn_iter_70000.ckpt
```

`tools/test_net.py` passes a `weights_filename` of `<tag>/<checkpoint-basename-without-extension>`, so detection/evaluation artifacts are placed under the **test imdb** name:

```text
output/<EXP_DIR>/<test-imdb>/<tag>/<checkpoint-basename>/detections.pkl
```

Example for ResNet101 VOC 07+12 evaluated on `voc_2007_test`:

```text
output/res101/voc_2007_test/default/res101_faster_rcnn_iter_110000/detections.pkl
```

VOC evaluation also writes class precision-recall pickles (`<class>_pr.pkl`) into the same output directory. COCO evaluation writes `detection_results.pkl` there. Temporary VOC result text files are written under the VOC devkit `results` directory and removed unless cleanup is disabled.

## TensorBoard artifact formula

`lib/model/config.py::get_output_tb_dir(imdb, weights_filename)` creates:

```text
tensorboard/<EXP_DIR>/<imdb.name>/<weights_filename-or-default>
```

`SolverWrapper` appends `_val` for validation summaries:

```text
tensorboard/<EXP_DIR>/<imdb.name>/<tag-or-default>/
tensorboard/<EXP_DIR>/<imdb.name>/<tag-or-default>_val/
```

README examples:

```text
tensorboard/vgg16/voc_2007_trainval/
tensorboard/vgg16/coco_2014_train+coco_2014_valminusminival/
```

The code-level path includes the final tag component (`default` if no explicit tag). If a README-style TensorBoard path appears to omit `default`, check the actual printed training output from `tools/trainval_net.py`.

## Safe path validation

Use the bundled validator after arranging existing files:

```bash
python <skill-dir>/scripts/validate_layout.py --repo-root <repo-root> --check demo-model
python <skill-dir>/scripts/validate_layout.py --repo-root <repo-root> --check imagenet
```

The checks only verify expected file and directory names. They do not verify checkpoint tensor contents, TensorFlow compatibility, CUDA availability, or AP quality.
