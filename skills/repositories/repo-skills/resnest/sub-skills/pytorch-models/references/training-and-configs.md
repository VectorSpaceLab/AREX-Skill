# Training and Configuration Notes

This reference keeps the heavyweight PyTorch training path readable without turning it into a launcher copy.

## Configuration shape

`get_cfg()` returns a config tree with these top-level sections:

| Section | Key | Default | Meaning |
|---|---|---:|---|
| `SEED` | `SEED` | `1` | Global random seed |
| `DATA` | `DATASET` | `ImageNet` | Dataset registry name |
|  | `ROOT` | `~/.encoding/data/ILSVRC2012` | ImageNet root used by the bundled dataset wrapper |
|  | `BASE_SIZE` | `None` | Optional base image size for augmentation |
|  | `CROP_SIZE` | `224` | Crop size used by the transform builder |
|  | `LABEL_SMOOTHING` | `0.0` | Switches to label smoothing when positive |
|  | `MIXUP` | `0.0` | Switches to MixUp when positive |
|  | `RAND_AUG` | `False` | Enables RandAugment in the train transform |
| `MODEL` | `NAME` | `resnet50` | Registry name consumed by the training path |
|  | `FINAL_DROP` | `False` | Optional final dropout value |
| `TRAINING` | `BATCH_SIZE` | `64` | Per-GPU training batch size |
|  | `TEST_BATCH_SIZE` | `256` | Per-GPU evaluation batch size |
|  | `LAST_GAMMA` | `False` | Requests zero-init last BN gamma when supported |
|  | `EPOCHS` | `120` | Number of epochs |
|  | `START_EPOCHS` | `0` | Resume offset |
|  | `WORKERS` | `4` | DataLoader worker count |
| `OPTIMIZER` | `LR` | `0.025` | Per-GPU base learning rate |
|  | `LR_SCHEDULER` | `cos` | Learning-rate schedule mode |
|  | `MOMENTUM` | `0.9` | SGD momentum |
|  | `WEIGHT_DECAY` | `1e-4` | SGD weight decay |
|  | `DISABLE_BN_WD` | `False` | Exempts BN and bias parameters from weight decay |
|  | `WARMUP_EPOCHS` | `0` | Warmup length |

## Baseline config snippet

The bundled ImageNet baseline config sets:

- `MODEL.NAME = resnet50`
- `TRAINING.EPOCHS = 120`
- `TRAINING.BATCH_SIZE = 32`
- `OPTIMIZER.LR = 0.0125`

Interpretation note: the launcher multiplies learning rate by the effective world size before spawning workers.

## Model selection rules

- The training path uses `get_model(cfg.MODEL.NAME)`.
- That means registry-backed names work directly: `resnet50`, `resnet101`, `resnet152`, `resnest50`, `resnest101`, `resnest200`, `resnest269`.
- The fast ablation factories are not registry entries, so they are not drop-in config names in the bundled training path.

## Loss and augmentation selection

`get_criterion(cfg, train_loader, gpu)` chooses one of three training losses:

| Condition | Criterion | Extra behavior |
|---|---|---|
| `cfg.DATA.MIXUP > 0` | `NLLMultiLabelSmooth` | wraps the loader in `MixUpWrapper` and assumes 1000 classes |
| `cfg.DATA.LABEL_SMOOTHING > 0` | `LabelSmoothing` | no loader wrapping |
| otherwise | `torch.nn.CrossEntropyLoss()` | plain ImageNet classification loss |

Transform selection for `ImageNet`:

- train: random crop, flip, color jitter, tensor conversion, PCA lighting, normalization;
- val: center crop, tensor conversion, normalization.

## Training-launcher semantics

The bundled launcher is intentionally heavyweight and CUDA-oriented.

- It detects `torch.cuda.device_count()` and spawns one worker per GPU.
- It initializes distributed training with `DistributedDataParallel` and a process group backend of `nccl` by default.
- It uses `DistributedSampler` for both train and validation loaders.
- It supports resume, eval-only, and export flows.
- It writes checkpoints and metrics with `PathManager`.

What to remember:

- this is not a CPU-only training path;
- if you need a non-distributed or CPU smoke, use the tiny inference helper instead;
- the dataset wrapper accepts the root path but does not download data for you.

## ImageNet preparation notes

The dataset-prep flow expects the official tar files and expands them into a standard raw-image tree.

Key facts to retain:

- expected tar names are the standard ImageNet train and val archives;
- optional SHA1 checks guard the tar files before extraction;
- extracted data lands under `train/` and `val/` subfolders;
- the validation preparation step performs a shell-based folder reorganization for raw images.

Do not treat this as a lightweight helper. It is a dataset-preparation workflow with large disk, network, and mutation costs.
