# CLI reference and command builder

Use this reference for tf-faster-rcnn train/test/reval/convert command construction. The bundled script is intentionally dry-run only and should be preferred for planning.

## Bundled dry-run command builder

Script path inside the generated skill:

```bash
python sub-skills/training-and-evaluation/scripts/tf_faster_rcnn_command_builder.py --help
```

The script prints expanded shell commands and metadata. It never imports TensorFlow, touches datasets, launches training, launches evaluation, or mutates outputs.

Common examples:

```bash
# VOC 07+12 ResNet101 training plan, including the post-train test command the shell launcher would run.
python sub-skills/training-and-evaluation/scripts/tf_faster_rcnn_command_builder.py \
  train --dataset pascal_voc_0712 --net res101 --gpu-id 0

# Test a VOC 07+12 ResNet101 checkpoint and override TEST.MODE.
python sub-skills/training-and-evaluation/scripts/tf_faster_rcnn_command_builder.py \
  test --dataset pascal_voc_0712 --net res101 --gpu-id 0 --set TEST.MODE top

# Re-evaluate an existing detections.pkl directory with NMS applied before evaluation.
python sub-skills/training-and-evaluation/scripts/tf_faster_rcnn_command_builder.py \
  reval --dataset pascal_voc_0712 --net res101 --reval-nms

# Deprecated VGG16 checkpoint conversion plan.
python sub-skills/training-and-evaluation/scripts/tf_faster_rcnn_command_builder.py \
  convert --dataset pascal_voc --gpu-id 0

# Machine-readable output for a verifier or wrapper.
python sub-skills/training-and-evaluation/scripts/tf_faster_rcnn_command_builder.py \
  test --dataset coco --net mobile --format json
```

## Actions

| Action | What it builds | Real side effects if the printed command is manually run |
| --- | --- | --- |
| `train` | Expanded `tools/trainval_net.py` command plus the follow-up `tools/test_net.py` command that the original training shell launcher invokes. | Full training, snapshots, TensorBoard summaries, and test evaluation. Expensive; requires data, ImageNet weights, TF1/native extensions, and usually GPU/CUDA. |
| `test` | Expanded `tools/test_net.py` command using mapped imdbs, anchors, ratios, config, and checkpoint prefix. | Full dataset inference/evaluation and `detections.pkl` output. Requires dataset, trained checkpoint, TF1/native extensions, and often GPU/CUDA. |
| `reval` | `tools/reval.py` command for an existing output directory. | Re-runs dataset evaluation from `detections.pkl`; no model inference, but still requires dataset annotations and evaluation dependencies. |
| `convert` | Expanded `tools/convert_from_depre.py` VGG16 conversion command. | Reads old VGG16 checkpoint files, writes converted checkpoint and copies `.pkl`; requires TensorFlow 1.x checkpoint compatibility. |

## Dataset aliases

The builder preserves the launcher mappings:

| Alias | Train imdb | Test imdb | Iters | Stepsize | Anchors |
| --- | --- | --- | ---: | --- | --- |
| `pascal_voc` | `voc_2007_trainval` | `voc_2007_test` | 70000 | `[50000]` | `[8,16,32]` |
| `pascal_voc_0712` | `voc_2007_trainval+voc_2012_trainval` | `voc_2007_test` | 110000 | `[80000]` | `[8,16,32]` |
| `coco` | `coco_2014_train+coco_2014_valminusminival` | `coco_2014_minival` | 490000 | `[350000]` | `[4,8,16,32]` |

All aliases use anchor ratios `[0.5,1,2]`.

Use `--iters`, `--train-imdb`, or `--test-imdb` only when intentionally leaving the launcher defaults, and record the reason because output directories and AP comparability change.

## Network selectors

Accepted by the builder and by the Python tools:

```text
vgg16, res50, res101, res152, mobile
```

Default config path is `experiments/cfgs/<net>.yml`, unless `--cfg` is supplied. Evidence notes:

- `vgg16.yml`, `res50.yml`, `res101.yml`, `mobile.yml`, and `res101-lg.yml` were present in the observed checkout.
- `res152` is accepted by source CLIs and mentioned in README results, but `res152.yml` was not present in the observed config directory. Use `--cfg` or provide a matching config before a real `res152` run.
- `res101-lg.yml` is a config variant and not a `--net res101-lg` selector. Use `--net res101 --cfg experiments/cfgs/res101-lg.yml` only after confirming the intended experiment directory and snapshot naming.

## Config override grammar

The repository's Python tools use:

```bash
--set KEY VALUE [KEY VALUE ...]
```

Rules enforced by `model.config.cfg_from_list`:

- The list length must be even: every key needs a value.
- Nested keys use dot notation, such as `TRAIN.STEPSIZE`, `TEST.MODE`, or `ANCHOR_SCALES`.
- Keys must already exist in the config object.
- Values are parsed with Python `literal_eval` when possible, so lists and numbers should be quoted in the shell:
  - `--set TRAIN.STEPSIZE '[80000]'`
  - `--set ANCHOR_SCALES '[8,16,32]'`
  - `--set TEST.MODE top`
- The parsed value type must exactly match the current config value type. For example, `TRAIN.STEPSIZE` is a list, `TEST.MODE` is a string, `TRAIN.DISPLAY` is an integer, and `USE_GPU_NMS` is a boolean.

The original shell launchers append user extra tokens inside their own `--set` list and derive an output tag slug by replacing spaces with underscores. The bundled builder models this with repeated pairs:

```bash
python sub-skills/training-and-evaluation/scripts/tf_faster_rcnn_command_builder.py \
  test --dataset pascal_voc_0712 --net res101 \
  --set TEST.MODE top --set TRAIN.DISPLAY 100
```

If `--tag` is not supplied, the builder derives the same slug style from user-provided pairs, such as `TEST.MODE_top_TRAIN.DISPLAY_100`, and passes it to `--tag` for direct Python commands. This mirrors the shell launcher output layout when extra tokens are used.

## `tools/trainval_net.py`

Primary arguments:

| Argument | Default in parser | Launcher value | Meaning |
| --- | --- | --- | --- |
| `--cfg` | `None` | `experiments/cfgs/<net>.yml` | YAML config merged before `--set`. |
| `--weight` | required by workflow | `data/imagenet_weights/<net>.ckpt` | ImageNet initialization checkpoint. |
| `--imdb` | `voc_2007_trainval` | mapped train imdb | Training dataset; `+` combines multiple roidbs. |
| `--imdbval` | `voc_2007_test` | mapped test imdb | Validation dataset sampled during training with flipping disabled. |
| `--iters` | `70000` | mapped iteration count | Maximum training iterations. |
| `--tag` | `None` | slug when extra args exist | Output/TensorBoard subdirectory; `None` becomes `default`. |
| `--net` | `res50` | user net | Instantiates VGG16, ResNet50/101/152, or MobileNet. |
| `--set` | remainder | mapped anchors/ratios/stepsize + extras | Config overrides. |

The parser prints help and exits if invoked without arguments.

## `tools/test_net.py`

Primary arguments:

| Argument | Default in parser | Launcher value | Meaning |
| --- | --- | --- | --- |
| `--cfg` | `None` | `experiments/cfgs/<net>.yml` | YAML config. |
| `--model` | `None` | expected training checkpoint | TensorFlow checkpoint prefix to restore. |
| `--imdb` | `voc_2007_test` | mapped test imdb | Dataset to evaluate. |
| `--comp` | `False` | optional | Dataset competition mode. |
| `--num_dets` | `100` | optional | Maximum detections per image over all classes. |
| `--tag` | empty string | slug when extra args exist | Included in test output path. Empty becomes `default`. |
| `--net` | `res50` | user net | Network selector. |
| `--set` | remainder | mapped anchors/ratios + extras | Config overrides. |

The tool writes detections under an output directory derived from `cfg.EXP_DIR`, the test imdb, the tag, and the checkpoint filename, then calls dataset evaluation.

## `tools/reval.py`

Primary arguments:

| Argument | Default | Meaning |
| --- | --- | --- |
| positional `output_dir` | required | Directory containing `detections.pkl`. |
| `--imdb` | `voc_2007_test` | Dataset metadata/evaluator to use. |
| `--matlab` | `False` | Use MATLAB VOC evaluation path if supported by the dataset class. |
| `--comp` | `False` | Competition mode. |
| `--nms` | `False` | Apply NMS to saved detections before evaluation. |

Use `reval` for metric/evaluator reruns, not for checkpoint inference.

## `tools/convert_from_depre.py`

Primary arguments:

| Argument | Default | Meaning |
| --- | --- | --- |
| `--cfg` | `None` | YAML config, normally `experiments/cfgs/vgg16.yml`. |
| `--snapshot` | required by workflow | Snapshot prefix such as `vgg16_faster_rcnn_iter_70000`. |
| `--imdb` | `voc_2007_trainval` | Dataset used to derive output directory/classes. |
| `--iters` | `70000` | Iteration count associated with the snapshot. |
| `--tag` | `None` | Output tag. |
| `--set` | remainder | Anchors/ratios and extra config overrides. |

This tool is VGG16-specific and expects old checkpoints under a sibling `vgg16_depre` output path derived internally.

## Command-builder options

Run `--help` for authoritative usage. Important options:

| Option | Use |
| --- | --- |
| `action` | One of `train`, `test`, `reval`, `convert`. |
| `--dataset` | `pascal_voc`, `pascal_voc_0712`, or `coco`; default `pascal_voc`. |
| `--net` | `vgg16`, `res50`, `res101`, `res152`, or `mobile`; ignored/forced to `vgg16` for conversion. |
| `--gpu-id` | Value for `CUDA_VISIBLE_DEVICES` in generated train/test/convert commands. |
| `--cfg` | Override config path; needed for custom presets or missing `res152.yml`. |
| `--iters` | Override mapped iteration count. |
| `--train-imdb`, `--test-imdb` | Override mapped imdb names. |
| `--set KEY VALUE` | Add a config pair. Repeat for multiple pairs. |
| `--tag` | Explicit output tag; otherwise user `--set` pairs derive a slug and no extras use `default`. |
| `--model` | Explicit checkpoint prefix for test. |
| `--output-dir` | Explicit directory for reval. |
| `--reval-nms`, `--matlab`, `--comp` | Reval/test evaluation options. |
| `--format shell|json` | Human-readable shell snippets or JSON. |
| `--repo-root` | Path used only for optional existence warnings. Default `.`. |

## Interpreting builder warnings

The builder can warn about issues it can infer without importing the repo:

- missing config file under `--repo-root`
- `res152` default config absence
- VGG conversion requested with a non-VGG net
- expensive/side-effectful action reminders
- auto-derived tags from extra config pairs

Warnings are planning signals, not proof that a real run will succeed. Validate environment and data through sibling sub-skills before launching printed commands.
