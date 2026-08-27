# Detectron2 ResNeSt Workflows

These workflows cover ResNeSt-specific Detectron2 setup, config probing, command construction, and COCO dataset caveats. They intentionally avoid running the original heavyweight training, evaluation, or dataset download scripts.

## Optional dependency readiness

Detectron2 is optional for ResNeSt. Before using this sub-skill for runtime work, confirm all of the following in the active user environment:

- PyTorch and torchvision versions compatible with the intended Detectron2 build.
- Detectron2 installed with any required compiled C++/CUDA operators.
- ResNeSt package installed so `import resnest.d2` succeeds.
- `fvcore`, `iopath`, and Detectron2's transitive dependencies available.
- `pycocotools` available for COCO detection/instance/panoptic evaluation.
- CUDA available for realistic COCO training/evaluation with SyncBN and large ResNeSt-200/3x recipes; CPU can be useful for config probing only.

Run the bundled config probe first:

```bash
python scripts/detectron2_config_probe.py
```

If Detectron2 is unavailable, the probe prints a conditional skip message instead of training or failing with a traceback.

## Config merge workflow

Use this pattern in a Detectron2 launcher, notebook, or config-only smoke test:

```python
from detectron2.config import get_cfg
from resnest.d2 import add_resnest_config

cfg = get_cfg()
add_resnest_config(cfg)
cfg.merge_from_file("path/to/config.yaml")
cfg.merge_from_list([
    "MODEL.BACKBONE.NAME", "build_resnest_fpn_backbone",
    "MODEL.RESNETS.DEPTH", "50",
    "MODEL.RESNETS.RADIX", "2",
    "MODEL.RESNETS.STRIDE_IN_1X1", "False",
])
cfg.freeze()
```

To validate a config without training:

```bash
python scripts/detectron2_config_probe.py --config-file path/to/config.yaml
```

To switch a standard FPN config toward ResNeSt at merge time:

```bash
python scripts/detectron2_config_probe.py \
  --config-file path/to/config.yaml \
  --opts \
  MODEL.BACKBONE.NAME build_resnest_fpn_backbone \
  MODEL.RESNETS.DEPTH 50 \
  MODEL.RESNETS.STRIDE_IN_1X1 False \
  MODEL.RESNETS.DEEP_STEM True \
  MODEL.RESNETS.AVD True \
  MODEL.RESNETS.AVG_DOWN True \
  MODEL.RESNETS.RADIX 2 \
  MODEL.RESNETS.BOTTLENECK_WIDTH 64 \
  INPUT.FORMAT RGB
```

For DCN rows, also override:

```bash
MODEL.RESNETS.DEFORM_ON_PER_STAGE '[False, True, True, True]' \
MODEL.RESNETS.DEFORM_MODULATED True \
MODEL.RESNETS.DEFORM_NUM_GROUPS 2
```

## Train command semantics

The ResNeSt Detectron2 training entry point follows Detectron2's `DefaultTrainer` pattern:

1. Parse standard Detectron2 arguments, including `--config-file`, `--num-gpus`, `--num-machines`, `--machine-rank`, `--dist-url`, `--eval-only`, `--resume`, and trailing `KEY VALUE` config options.
2. Build `cfg = get_cfg()`, call `add_resnest_config(cfg)`, merge the config file and trailing opts, freeze the config, and run Detectron2 default setup.
3. Launch the main function through Detectron2's distributed launcher.
4. For training, construct `Trainer(cfg)`, call `resume_or_load(resume=args.resume)`, optionally register a test-time augmentation eval hook, then call `trainer.train()`.

Generic command shape for a user's own DefaultTrainer-style launcher:

```bash
python your_train_net.py \
  --num-gpus 8 \
  --config-file path/to/resnest_coco_config.yaml \
  OUTPUT_DIR output/resnest_experiment
```

Use fewer GPUs only after adjusting batch size, learning rate, SyncBN/norm behavior, and memory-heavy settings. The released metrics were trained with FPN, SyncBN, COCO data, and scale augmentation; config-only success does not reproduce those metrics.

## Eval-only command semantics

Eval-only mode builds the model, loads `MODEL.WEIGHTS`, runs `Trainer.test(cfg, model)`, optionally applies test-time augmentation when `TEST.AUG.ENABLED` is true, and verifies results on the main process.

Generic eval-only command shape:

```bash
python your_train_net.py \
  --config-file path/to/resnest_coco_config.yaml \
  --eval-only \
  MODEL.WEIGHTS https://s3.us-west-1.wasabisys.com/resnest/detectron/faster_rcnn_ResNeSt_50_FPN_syncbn_range-scale_1x-ad123c0b.pth \
  OUTPUT_DIR output/resnest_eval
```

Practical notes:

- `MODEL.WEIGHTS` may point to an external released checkpoint URL or to a local checkpoint path supplied by the user.
- The config's datasets must already be registered and available before evaluation.
- SyncBN and DCN checkpoints require a Detectron2/PyTorch build compatible with the checkpoint's operators and normalization choices.
- Test-time augmentation can substantially increase eval time and memory; panoptic all-tricks enables it in the distilled catalog.

## Evaluator behavior

The trainer chooses evaluators from each dataset's `MetadataCatalog.evaluator_type`:

| Evaluator type | Evaluator used |
|---|---|
| `coco` | `COCOEvaluator` |
| `coco_panoptic_seg` | `SemSegEvaluator`, `COCOEvaluator`, and `COCOPanopticEvaluator` combined |
| `sem_seg` | `SemSegEvaluator` |
| `cityscapes_instance` | `CityscapesInstanceEvaluator` |
| `cityscapes_sem_seg` | `CityscapesSemSegEvaluator` |
| `pascal_voc` | `PascalVOCDetectionEvaluator` |
| `lvis` | `LVISEvaluator` |

If a custom dataset has no supported evaluator type, create an evaluator explicitly in the launcher instead of relying on the default mapping.

## COCO dataset setup caveats

The original COCO helper was intentionally not bundled because it performs network downloads, zip extraction, symlink mutation, a git clone, package installation, and large filesystem writes. For runtime work, prepare COCO outside this skill and verify the resulting layout before training/evaluation.

Detection/instance recipes expect Detectron2 COCO dataset registrations equivalent to:

```text
coco_2017_train
coco_2017_val
```

Panoptic recipes expect separated panoptic registrations equivalent to:

```text
coco_2017_train_panoptic_separated
coco_2017_val_panoptic_separated
```

A typical dataset root should contain the 2017 images and annotations needed by Detectron2, for example:

```text
$DETECTRON2_DATASETS/coco/train2017/
$DETECTRON2_DATASETS/coco/val2017/
$DETECTRON2_DATASETS/coco/annotations/instances_train2017.json
$DETECTRON2_DATASETS/coco/annotations/instances_val2017.json
$DETECTRON2_DATASETS/coco/annotations/panoptic_train2017.json
$DETECTRON2_DATASETS/coco/annotations/panoptic_val2017.json
$DETECTRON2_DATASETS/coco/panoptic_train2017/
$DETECTRON2_DATASETS/coco/panoptic_val2017/
```

If using a custom dataset, register dataset names and metadata in the user's project and update `DATASETS.TRAIN`, `DATASETS.TEST`, and evaluator logic accordingly.

## Selecting a recipe

- Need object detection only: start from the Faster R-CNN or Cascade R-CNN rows in [config-reference.md](config-reference.md).
- Need instance masks: start from the Mask R-CNN or Cascade Mask R-CNN rows.
- Need panoptic segmentation: start from the Panoptic FPN row and make sure separated panoptic COCO registrations exist.
- Need DCN: choose a DCN row and verify Detectron2 deformable convolution operators before training.
- Need a lightweight config merge smoke: use ResNeSt-50, non-DCN, no TTA, and the bundled probe.
