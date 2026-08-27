# Training workflow

This reference distills the repository's `train.py` behavior into command-planning guidance. It does not run training.

## What training needs

Fresh SSD300 training needs:

- An importable SSD.PyTorch source tree or installed equivalent.
- PyTorch, TorchVision, NumPy, OpenCV, and dataset dependencies.
- A dataset root matching the selected dataset:
  - VOC: `VOCdevkit/` containing `VOC2007` and `VOC2012` for default training.
  - COCO: a COCO root containing `images/trainval35k/`, `annotations/instances_trainval35k.json`, `PythonAPI/` or `pycocotools`, and `coco_labels.txt`.
- For fresh training, the VGG base weights file named by `--basenet`, default `vgg16_reducedfc.pth`, under `--save_folder`, default `weights/`.
- For resume training, a checkpoint path passed with `--resume` and a matching `--start_iter` when appropriate.
- CUDA is strongly recommended for speed, but the script exposes `--cuda false` and `MultiBoxLoss(..., use_gpu=args.cuda)`.

## Main `train.py` options

| Option | Default | Notes |
|---|---|---|
| `--dataset` | `VOC` | Choices are `VOC` or `COCO`. Selects config, dataset class, and max iteration schedule. |
| `--dataset_root` | VOC default root | Must match the selected dataset. Passing a COCO root while dataset is VOC, or vice versa, triggers parser errors in the source. |
| `--basenet` | `vgg16_reducedfc.pth` | Fresh training loads this file from `--save_folder`. |
| `--batch_size` | `32` | Reduce for CPU or limited VRAM. |
| `--resume` | `None` | Loads a full SSD state_dict with `ssd_net.load_weights`. |
| `--start_iter` | `0` | Use with resume to align LR schedule and logs. |
| `--num_workers` | `4` | Set to `0` for debugging dataset failures. |
| `--cuda` | `True` | Parsed by `str2bool`; use values like `false`, `true`, `0`, `1`. |
| `--lr` / `--learning-rate` | `1e-3` | Initial SGD learning rate. |
| `--momentum` | `0.9` | SGD momentum. |
| `--weight_decay` | `5e-4` | SGD weight decay. |
| `--gamma` | `0.1` | LR decay factor at configured step indices. |
| `--visdom` | `False` | Enables Visdom loss plots; requires a running Visdom server. |
| `--save_folder` | `weights/` | Also receives final dataset checkpoint and intermediate COCO checkpoint names. |

## Dataset-specific schedules

The config dictionaries define the training length and LR decay steps:

| Dataset | Config `num_classes` | LR steps | Max iterations |
|---|---:|---|---:|
| VOC | 21 | `(80000, 100000, 120000)` | `120000` |
| COCO | 201 | `(280000, 360000, 400000)` | `400000` |

These are full-scale schedules, not smoke tests.

## Fresh VOC command template

Use the bundled planner to create a reviewed command string:

```bash
python scripts/plan_training_command.py \
  --dataset VOC \
  --dataset-root VOCDEVKIT_ROOT \
  --save-folder weights/ \
  --basenet vgg16_reducedfc.pth \
  --cuda true \
  --batch-size 32 \
  --num-workers 4
```

The command it emits has the shape:

```bash
python train.py --dataset VOC --dataset_root VOCDEVKIT_ROOT --save_folder weights/ --basenet vgg16_reducedfc.pth --cuda true --batch_size 32 --num_workers 4
```

Before running it, verify that `weights/vgg16_reducedfc.pth` exists and that the VOC layout validator passes for the selected splits.

## COCO command template

COCO requires the COCO trainval35k layout plus `pycocotools` or the COCO `PythonAPI` path:

```bash
python scripts/plan_training_command.py \
  --dataset COCO \
  --dataset-root COCO_ROOT \
  --save-folder weights/ \
  --basenet vgg16_reducedfc.pth \
  --cuda true
```

Check that the COCO label map exists at the location used by the runtime before importing `data` or `train.py`.

## Resume command template

```bash
python scripts/plan_training_command.py \
  --dataset VOC \
  --dataset-root VOCDEVKIT_ROOT \
  --resume weights/VOC.pth \
  --start-iter 80000 \
  --cuda true
```

When resuming, the source skips VGG base-weight loading and calls `ssd_net.load_weights(args.resume)` instead. The checkpoint must match the class count and model head shapes for the selected dataset.

## Debug or CPU-safe planning

For a short diagnostic setup before a real run:

- Use `--cuda false` if GPU behavior is not being verified.
- Use `--num_workers 0` to keep dataset errors in the main process.
- Reduce `--batch_size` for CPU or small GPU memory.
- Do not interpret a single batch or import smoke as evidence that full training will reproduce README mAP.

## Training loop facts

- The script wraps the model in `torch.nn.DataParallel` when `--cuda true`.
- Fresh training initializes `extras`, `loc`, and `conf` weights with Xavier uniform initialization.
- Optimizer is SGD with configured LR, momentum, and weight decay.
- Loss is `MultiBoxLoss(num_classes, 0.5, True, 0, True, 3, 0.5, False, args.cuda)`.
- DataLoader uses `detection_collate`, shuffling, configured workers, and pinned memory.
- Intermediate checkpoints are saved every 5000 iterations under names like `weights/ssd300_COCO_<iteration>.pth` in the source.
- Final checkpoint path is `args.save_folder + args.dataset + '.pth'`.

## Visdom notes

When `--visdom true`, install `visdom` and start a server separately, for example:

```bash
python -m visdom.server
```

Then open the Visdom browser UI before or during training. Visdom is optional and should not be installed merely for data/model inspection.
