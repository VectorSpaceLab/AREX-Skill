# detrex configuration reference

This reference summarizes the LazyConfig fragments and training-related fields used by detrex. It is self-contained for planning and editing configs; use it instead of opening original docs or source files for common training/config decisions.

## LazyConfig contract

The standard trainer expects a Python LazyConfig that exposes these top-level names:

| Namespace | Purpose | Typical source or shape |
|---|---|---|
| `model` | LazyCall model definition. | Project configs define DETR-family models, backbone, neck, transformer, criterion, post-process, and device fields. |
| `train` | Runtime training/evaluation settings. | Packaged common train fields include output/checkpoint, max iteration, AMP, DDP, clipping, fast debug, checkpointer, logging, WandB, EMA, and device. |
| `dataloader` | Train/test loaders and evaluator. | Usually Detectron2 `build_detection_train_loader`, `build_detection_test_loader`, dataset names, mapper, and evaluator. |
| `optimizer` | Optimizer LazyCall or project-specific optimizer settings. | Common `AdamW` and `SGD` fragments use Detectron2 optimizer param helpers. |
| `lr_multiplier` | Scheduler LazyCall. | Common COCO/DETR schedules and generic warmup scheduler helpers. |

A compact config usually imports common fragments, imports one model fragment, then mutates only the fields that define the experiment.

```python
from detrex.config import get_config
from my_project.models.my_model import model

dataloader = get_config("common/data/coco_detr.py").dataloader
optimizer = get_config("common/optim.py").AdamW
lr_multiplier = get_config("common/coco_schedule.py").lr_multiplier_12ep
train = get_config("common/train.py").train

train.output_dir = "outputs/my_run"
train.init_checkpoint = "weights/backbone_or_model.pth"
train.max_iter = 90000
```

## `train` namespace fields

The common training fragment defines these fields:

| Field | Meaning | Notes |
|---|---|---|
| `train.output_dir` | Directory for checkpoints, metrics, TensorBoard files, and evaluator outputs. | Resume reads from this directory. Set per run. |
| `train.init_checkpoint` | Initial model/checkpoint path. | Required for most eval-only commands and common for backbone/model initialization. |
| `train.max_iter` | Total optimizer iterations. | Keep aligned with dataset size, total batch size, and scheduler length. |
| `train.amp.enabled` | Automatic mixed precision. | Standard trainer uses CUDA AMP; verify CUDA/custom operators first. |
| `train.ddp.broadcast_buffers` | DDP buffer sync behavior. | Defaults false in common config. |
| `train.ddp.find_unused_parameters` | DDP unused parameter detection. | Enable for project models with conditional branches or unused heads. |
| `train.ddp.fp16_compression` | DDP communication compression. | Requires distributed support; treat as optional tuning. |
| `train.clip_grad.enabled` | Enable gradient clipping. | Common DETR configs often use max-norm clipping. |
| `train.clip_grad.params.max_norm` | Gradient norm cap. | Example value: `0.1`. |
| `train.clip_grad.params.norm_type` | Norm type for clipping. | Example value: `2`. |
| `train.seed` | Training seed. | `-1` leaves seed behavior to setup/defaults. |
| `train.fast_dev_run.enabled` | Short debug run. | Standard trainer changes to 20 max iter, 10 eval period, and 1 log period. |
| `train.checkpointer.period` | Save checkpoint every N iterations. | Combine with `max_to_keep`. |
| `train.checkpointer.max_to_keep` | Maximum saved checkpoints to keep. | Tune for disk capacity. |
| `train.eval_period` | Run evaluator every N iterations. | Set lower only for debug or small datasets. |
| `train.log_period` | Metric writer period. | Fast debug uses period 1. |
| `train.wandb.enabled` | Enable WandB writer in the standard trainer. | Requires WandB runtime and valid `train.wandb.params`. |
| `train.wandb.params` | Keyword args for `wandb.init`. | Common fields include `dir`, `project`, and `name`. |
| `train.model_ema.enabled` | Enable EMA state/hook/checkpointing. | Standard trainer builds EMA before checkpointer. |
| `train.model_ema.decay` | EMA decay. | Example value: `0.999`. |
| `train.model_ema.device` | Device for EMA state. | Empty string follows default behavior. |
| `train.model_ema.use_ema_weights_for_eval_only` | Eval-only should apply EMA weights. | Only use when checkpoint contains EMA state. |
| `train.device` | Model/training device. | Common configs use `cuda`; CPU training is not the normal path. |

## Optimizer fragments

Common optimizer fragments:

| Fragment | Behavior | Key defaults |
|---|---|---|
| `SGD` | `torch.optim.SGD` with Detectron2 default parameter grouping. | `lr=0.02`, `momentum=0.9`, `weight_decay=1e-4`, norm weight decay 0. |
| `AdamW` | `torch.optim.AdamW` with Detectron2 default parameter grouping. | `lr=1e-4`, `betas=(0.9, 0.999)`, `weight_decay=0.1`, norm weight decay 0. |

For the common optimizer fragments, the trainer sets `cfg.optimizer.params.model = model` before instantiation. If you change optimizer type, delete incompatible fields and add required ones in the config:

```python
import torch
from detrex.config import get_config

optimizer = get_config("common/optim.py").AdamW
optimizer._target_ = torch.optim.SGD
del optimizer.betas
optimizer.lr = 0.02
optimizer.momentum = 0.9
optimizer.weight_decay = 1e-4
```

Project-specific trainers may ignore the common optimizer LazyCall and build explicit parameter groups. For example, a DINO trainer can use separate rates for backbone parameters and deformable-attention reference/sampling offsets; a tracking trainer can use config fields such as `lr_backbone_names`, `lr_linear_proj_names`, `lr_backbone`, and `lr_linear_proj_mult`.

## Scheduler fragments

Common COCO/DETR scheduler presets:

| Preset | Meaning |
|---|---|
| `lr_multiplier_1x`, `2x`, `3x`, `6x`, `9x` | Detectron2-style COCO schedules based on 90k iterations per 1x at total batch size 16. |
| `lr_multiplier_12ep`, `24ep`, `36ep`, `50ep` | DETR-style epoch schedules based on 7500 iterations per COCO epoch at total batch size 16. |
| `lr_multiplier_12ep_warmup`, `50ep_warmup` | DETR-style epoch schedules with warmup. |

Generic scheduler helper families include `multistep_lr_scheduler`, `step_lr_scheduler`, `step_lr_scheduler_with_fixed_gamma`, `cosine_lr_scheduler`, `linear_lr_scheduler`, `constant_lr_scheduler`, and `exponential_lr_scheduler`. They return LazyCall scheduler configs wrapped with warmup.

When changing total batch size, dataset size, or `train.max_iter`, check that scheduler `num_updates`, milestones, or preset length still represent the intended run.

## Dataloader and dataset fields

A common detection dataloader uses Detectron2 dataset names, `DetrDatasetMapper`, and `COCOEvaluator`:

```python
from detectron2.config import LazyCall as L
from detectron2.data import build_detection_train_loader, build_detection_test_loader, get_detection_dataset_dicts
from detectron2.evaluation import COCOEvaluator
from detrex.data import DetrDatasetMapper

dataloader.train = L(build_detection_train_loader)(
    dataset=L(get_detection_dataset_dicts)(names="coco_2017_train"),
    mapper=L(DetrDatasetMapper)(is_train=True, mask_on=False, img_format="RGB", augmentation=[...], augmentation_with_crop=[...]),
    total_batch_size=16,
    num_workers=4,
)
dataloader.test = L(build_detection_test_loader)(
    dataset=L(get_detection_dataset_dicts)(names="coco_2017_val", filter_empty=False),
    mapper=L(DetrDatasetMapper)(is_train=False, mask_on=False, img_format="RGB", augmentation=[...], augmentation_with_crop=None),
    num_workers=4,
)
dataloader.evaluator = L(COCOEvaluator)(dataset_name="${..test.dataset.names}")
```

Checklist for dataset adaptation:

- Builtin COCO names require `DETECTRON2_DATASETS` with a `coco/annotations`, `train2017`, and `val2017` layout.
- Custom datasets must be registered before dataloader construction and config names must match registration names.
- `total_batch_size` is global across all GPUs, not per-GPU batch size.
- If you enable masks or panoptic/semantic targets, choose a mapper and evaluator that emit the fields expected by the model.
- Evaluator `output_dir` can be set to `train.output_dir` if result JSONs/visualization artifacts should live with the run.

## Command-line override conventions

Plain launcher trailing overrides:

```bash
python -m tools.train_net --config-file user_configs/model.py train.max_iter=30000 train.fast_dev_run.enabled=True
```

Hydra launcher overrides:

```bash
python -m tools.hydra_train_net config_file=user_configs/model.py auto_output_dir=true +train.max_iter=30000 +model.num_queries=50
```

Use plain `key=value` for Hydra launcher fields and `+key=value` for LazyConfig overrides that should be forwarded into the loaded Python config.

## Custom backbone wiring

When replacing a backbone, update the backbone object, the neck feature metadata, and the initialization checkpoint plan together.

### Torchvision backbone pattern

```python
from detectron2.config import LazyCall as L
from detectron2.modeling import ShapeSpec
from detrex.modeling.backbone import TorchvisionBackbone

model.backbone = L(TorchvisionBackbone)(
    model_name="resnet50",
    pretrained=False,
    return_nodes={
        "layer2": "res3",
        "layer3": "res4",
        "layer4": "res5",
    },
)
model.neck.input_shapes = {
    "res3": ShapeSpec(channels=512),
    "res4": ShapeSpec(channels=1024),
    "res5": ShapeSpec(channels=2048),
}
model.neck.in_features = ["res3", "res4", "res5"]
train.init_checkpoint = ""
```

### timm backbone pattern

```python
from detectron2.config import LazyCall as L
from detectron2.layers import FrozenBatchNorm2d
from detectron2.modeling import ShapeSpec
from detrex.modeling.backbone import TimmBackbone

model.backbone = L(TimmBackbone)(
    model_name="resnet152d",
    features_only=True,
    pretrained=False,
    in_channels=3,
    out_indices=(1, 2, 3),
    norm_layer=FrozenBatchNorm2d,
)
model.neck.input_shapes = {
    "p1": ShapeSpec(channels=256),
    "p2": ShapeSpec(channels=512),
    "p3": ShapeSpec(channels=1024),
}
model.neck.in_features = ["p1", "p2", "p3"]
train.init_checkpoint = ""
```

Use `pretrained=True` only when the user authorizes weight downloads or has configured local caches. For deterministic/offline config work, prefer `pretrained=False` and set an explicit local checkpoint path later.

## Project-specific training config cautions

- DINO configs may rely on a hacked trainer that builds explicit optimizer groups for non-backbone, backbone, and deformable-attention reference/sampling-offset parameters. Use the DINO trainer or reproduce that grouping before comparing results.
- CO-MOT configs add tracking-specific fields such as `lr_backbone_names`, `lr_linear_proj_names`, and custom data movement to CUDA. Use the CO-MOT trainer for tracking workflows.
- Some project configs set both `train.device` and `model.device`; keep them synchronized when changing devices.
- Absolute output paths copied from public examples should be replaced with user-approved run directories.
- If a project-specific trainer lacks AMP/EMA/WandB features present in the generic trainer, do not assume the same overrides are supported without inspecting or porting that trainer behavior.
