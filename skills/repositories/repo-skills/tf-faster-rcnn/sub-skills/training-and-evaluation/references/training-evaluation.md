# Training and evaluation workflow

This reference distills the repository's train/test/re-evaluate/convert workflows into self-contained operating guidance. Use it with [cli-reference.md](cli-reference.md) and the bundled dry-run script before any expensive run.

## Preconditions owned by other sub-skills

Before running a real command, confirm the prerequisites elsewhere:

- Environment: TensorFlow 1.x-compatible Python, Cython extensions, NMS mode, CUDA/NVCC expectations, and `USE_GPU_NMS` are handled by [installation-and-configuration](../../installation-and-configuration/SKILL.md).
- Data and assets: VOC/COCO layouts, dataset registry names, `data/imagenet_weights/<net>.ckpt`, pretrained Faster R-CNN checkpoints, output symlinks, and cache directories are handled by [dataset-and-assets](../../dataset-and-assets/SKILL.md).

This sub-skill assumes the user is already at a repository checkout and is asking which train/eval command shape to use or how to recover from workflow-level failures.

## Dataset schedule mapping

The original shell launchers define three dataset aliases. Preserve these values when reconstructing direct Python tool commands.

| Dataset alias | Train imdb | Test/validation imdb | Train iters | Train stepsize | Anchor scales | Anchor ratios | Notes |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| `pascal_voc` | `voc_2007_trainval` | `voc_2007_test` | 70000 | `[50000]` | `[8,16,32]` | `[0.5,1,2]` | VOC 2007 trainval to VOC 2007 test; README reports VGG16 70.8 and ResNet101 75.7 in historical runs. |
| `pascal_voc_0712` | `voc_2007_trainval+voc_2012_trainval` | `voc_2007_test` | 110000 | `[80000]` | `[8,16,32]` | `[0.5,1,2]` | VOC 2007+2012 schedule following R-FCN; README reports VGG16 75.7 and ResNet101 79.8 historically. |
| `coco` | `coco_2014_train+coco_2014_valminusminival` | `coco_2014_minival` | 490000 | `[350000]` | `[4,8,16,32]` | `[0.5,1,2]` | Shell launcher schedule is 490k. README benchmark notes mention longer 900k/1190k COCO results; use explicit overrides for reproduction attempts. |

The launchers pass these values through `--set ANCHOR_SCALES ... ANCHOR_RATIOS ...`; training additionally passes `TRAIN.STEPSIZE ...`.

## Network and config mapping

The Python CLIs accept `--net vgg16|res50|res101|res152|mobile` and instantiate:

| Net | Network class behavior | Default config path used by launchers | Evidence status |
| --- | --- | --- | --- |
| `vgg16` | `vgg16()` | `experiments/cfgs/vgg16.yml` | Config present; snapshot prefix `vgg16_faster_rcnn`. |
| `res50` | `resnetv1(num_layers=50)` | `experiments/cfgs/res50.yml` | Config present; snapshot prefix `res50_faster_rcnn`. |
| `res101` | `resnetv1(num_layers=101)` | `experiments/cfgs/res101.yml` | Config present; snapshot prefix `res101_faster_rcnn`. |
| `res152` | `resnetv1(num_layers=152)` | `experiments/cfgs/res152.yml` | CLIs and README mention it, but the observed checkout did not include `res152.yml`; require a user-supplied config before a real run. |
| `mobile` | `mobilenetv1()` | `experiments/cfgs/mobile.yml` | Config present; README reports MobileNet COCO performance. |

A separate `experiments/cfgs/res101-lg.yml` preset changes image scale, max size, RPN test proposals, and anchor scales for an approximate FPN-style baseline. It is a config variant, not a distinct `--net` selector; combine it with an appropriate ResNet net only after checking the intended checkpoint prefix and output directory.

## Training workflow

Source launcher behavior:

1. Read `GPU_ID`, `DATASET`, and `NET`.
2. Map the dataset alias to train/test imdb, iters, stepsize, anchors, and ratios.
3. Build a tag slug from any extra config tokens after the first three launcher arguments by replacing spaces with underscores.
4. Predict final checkpoint:
   - no extra tokens: `output/<net>/<train_imdb>/default/<net>_faster_rcnn_iter_<iters>.ckpt`
   - with extra tokens: `output/<net>/<train_imdb>/<extra_slug>/<net>_faster_rcnn_iter_<iters>.ckpt`
5. If `<checkpoint>.index` is missing, run `tools/trainval_net.py` from ImageNet initialization weights.
6. Always call the test launcher after the training block.

Expanded default training command shape:

```bash
CUDA_VISIBLE_DEVICES=<gpu_id> time python ./tools/trainval_net.py \
  --weight data/imagenet_weights/<net>.ckpt \
  --imdb <train_imdb> \
  --imdbval <test_imdb> \
  --iters <iters> \
  --cfg experiments/cfgs/<net>.yml \
  --net <net> \
  --set ANCHOR_SCALES <anchor_scales> ANCHOR_RATIOS <anchor_ratios> TRAIN.STEPSIZE <stepsize> [extra KEY VALUE pairs]
```

If extra key/value tokens are used, add `--tag <extra_slug>` so direct Python invocation matches the launcher output layout.

Training details preserved from `lib/model/train_val.py`:

- Training uses `get_training_roidb`, filters invalid roidb entries, and creates both train and validation `RoIDataLayer`s.
- The validation roidb is built after temporarily setting `cfg.TRAIN.USE_FLIPPED = False`; train flipping is controlled by the main config.
- `cfg.RNG_SEED` seeds NumPy and TensorFlow graph construction, but the README explicitly warns that TensorFlow/GPU training remains nondeterministic.
- Learning rate starts at `cfg.TRAIN.LEARNING_RATE`, is multiplied by `cfg.TRAIN.GAMMA` after configured step boundaries, and snapshots are taken before reducing LR at `stepsize + 1`.
- Bias gradient doubling is controlled by `cfg.TRAIN.DOUBLE_BIAS`; ResNet/Mobile configs set it to `False`.
- Default `cfg.TRAIN.SNAPSHOT_ITERS` is 5000 and `cfg.TRAIN.SNAPSHOT_KEPT` is 3.

## Snapshot and resume behavior

Training resumes automatically from existing snapshots in the output directory. The solver searches for:

- model meta files matching `<SNAPSHOT_PREFIX>_iter_*.ckpt.meta`
- metadata pickles matching `<SNAPSHOT_PREFIX>_iter_*.pkl`

It sorts them by modification time, ignores the learning-rate-transition snapshots at `stepsize + 1`, asserts the `.ckpt` and `.pkl` counts match, and restores the most recent pair. The `.pkl` stores NumPy random state, train/validation data-layer cursors, permutations, and last iteration. TensorFlow's random state is not fully restored, so resumed training can diverge numerically.

Failure-recovery implications:

- A stale or unrelated snapshot in the output directory can silently make the run resume instead of starting from ImageNet weights.
- Missing `.pkl` metadata or mismatched `.ckpt.meta`/`.pkl` counts can trigger the internal assertion before training starts.
- If a previous run ended at a learning-rate boundary, a snapshot at `stepsize + 1` may be deliberately ignored by the search logic.
- To force a clean run, move the old `output/<net>/<train_imdb>/<tag>/` directory aside or use a new tag instead of deleting files piecemeal.

## TensorBoard and output directories

`model.config.get_output_dir` and `get_output_tb_dir` create directories under the repository root using `cfg.EXP_DIR`, the imdb name, and a tag/weights filename.

For default config files, `cfg.EXP_DIR` matches the net selector (`vgg16`, `res50`, `res101`, `mobile`). The README summarizes common directories as:

```text
output/<net>/<train_imdb>/default/
output/<net>/<test_imdb>/default/<snapshot>/
tensorboard/<net>/<train_imdb>/default/
tensorboard/<net>/<train_imdb>/default_val/
```

The training code writes summaries for both train and validation. Example TensorBoard commands from the README use paths such as:

```bash
tensorboard --logdir=tensorboard/vgg16/voc_2007_trainval/ --port=7001
tensorboard --logdir=tensorboard/vgg16/coco_2014_train+coco_2014_valminusminival/ --port=7002
```

If a custom config changes `EXP_DIR` or a custom `--tag` is used, output and TensorBoard paths follow those new values.

## Test/evaluation workflow

The test launcher uses the same dataset mapping and anchors/ratios as the train launcher, but it does not pass `TRAIN.STEPSIZE`. It computes the model prefix from the expected training output and invokes `tools/test_net.py`:

```bash
CUDA_VISIBLE_DEVICES=<gpu_id> time python ./tools/test_net.py \
  --imdb <test_imdb> \
  --model output/<net>/<train_imdb>/<tag>/<net>_faster_rcnn_iter_<iters>.ckpt \
  --cfg experiments/cfgs/<net>.yml \
  --net <net> \
  --set ANCHOR_SCALES <anchor_scales> ANCHOR_RATIOS <anchor_ratios> [extra KEY VALUE pairs]
```

`tools/test_net.py` behavior:

- Loads the requested imdb and toggles competition mode if `--comp` is set.
- Builds the network in `TEST` mode with `anchor_scales=cfg.ANCHOR_SCALES` and `anchor_ratios=cfg.ANCHOR_RATIOS`.
- Restores the TensorFlow checkpoint specified by `--model`.
- Runs `model.test.test_net`, which writes `detections.pkl` and calls the dataset's `evaluate_detections` method.
- Default `--num_dets` is 100, limiting detections over all classes per image.

Testing is still a real model/data evaluation. Do not run it for mere command discovery.

## Re-evaluation workflow

`tools/reval.py` re-runs dataset evaluation from an existing output directory containing `detections.pkl`.

Command shape:

```bash
python ./tools/reval.py <output_dir> --imdb <test_imdb> [--nms] [--matlab] [--comp]
```

Use reval when model inference already finished but metric formatting, VOC/COCO evaluation settings, competition mode, MATLAB VOC evaluation, or optional NMS application needs to be revisited. It still requires the dataset metadata and annotations corresponding to the selected imdb.

The optional `--nms` flag applies `model.test.apply_nms` to saved detections using `cfg.TEST.NMS` before evaluation. Without it, reval evaluates detections as stored.

## Deprecated VGG16 snapshot conversion

The repository includes a VGG16-only conversion path for old snapshots. The shell launcher fixes `NET=vgg16`, maps the dataset alias, builds `NET_FINAL=vgg16_faster_rcnn_iter_<iters>`, and runs:

```bash
CUDA_VISIBLE_DEVICES=<gpu_id> time python ./tools/convert_from_depre.py \
  --snapshot vgg16_faster_rcnn_iter_<iters> \
  --imdb <train_imdb> \
  --iters <iters> \
  --cfg experiments/cfgs/vgg16.yml \
  --set ANCHOR_SCALES <anchor_scales> ANCHOR_RATIOS <anchor_ratios> [extra KEY VALUE pairs]
```

If extra key/value tokens are used, pass `--tag <extra_slug>` to match the shell launcher. The converter derives its input directory by replacing `/vgg16/` with `/vgg16_depre/` in the output directory, reads old checkpoint variables with TensorFlow's checkpoint reader, renames VGG variable scopes, saves the new checkpoint, and copies the `.pkl` metadata.

Treat conversion as a targeted migration workflow, not a generic model conversion utility. It needs matching old VGG16 checkpoint files and TensorFlow 1.x checkpoint compatibility.

## Evaluation modes and AP caveats

- Default testing uses `cfg.TEST.MODE = 'nms'`. The README notes `TEST.MODE top` may produce slightly better performance, especially for COCO, but can be slower.
- Default NMS threshold is `cfg.TEST.NMS = 0.3`; NMS implementation correctness affects AP. The README explicitly warns that failure to match the reported VOC ResNet101 number can indicate an incorrectly compiled NMS function.
- Reported benchmark numbers are best or representative historical results, not deterministic guarantees. VOC can vary by about 1% due to GPU/TensorFlow nondeterminism; COCO is reported as usually within about 0.2% in the README.
- The repository intentionally keeps small proposals and uses no final detection score threshold in `model.test.test_net` (`thresh=0.` default), which affects recall and benchmark comparability.
- COCO benchmark reproduction may require longer schedules than the shell launcher's 490k default. Record iteration overrides explicitly when comparing AP.

## Safe workflow checklist

Before a real training or evaluation run:

1. Use `tf_faster_rcnn_command_builder.py` to dry-run the command and verify schedule, config, tag, model prefix, and output directory.
2. Confirm the checkout has the selected config file, especially for `res152` or custom variants.
3. Confirm dataset aliases map to actual VOC/COCO layouts in `data/`.
4. Confirm `data/imagenet_weights/<net>.ckpt` exists for training or the expected trained checkpoint exists for testing.
5. Confirm NMS mode and compiled extensions match the runtime backend.
6. Decide whether stale snapshots should resume or be isolated under a new tag.
7. Treat full train/test as expensive; obtain explicit approval for long GPU runs or benchmark reproduction.
