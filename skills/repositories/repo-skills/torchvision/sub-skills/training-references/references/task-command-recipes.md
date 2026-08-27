# Task command recipes

These recipes are command plans, not commands to run automatically. They are not standalone commands: run them only after selecting the matching official reference script version, replacing placeholder paths, confirming datasets and output locations, choosing a process count that matches available hardware, and getting approval for downloads, GPU/distributed execution, and long-running work. Prefer adding `--test-only` for evaluation-only workflows where supported.

## Common patterns

- Distributed launch: `torchrun --nproc_per_node=<gpus_on_node> train.py ...` is expensive and requires distributed environment support.
- Single process: `python train.py ...` avoids distributed launch but can still run long jobs and requires datasets.
- Evaluation-only: many families support `--test-only`; optical flow and stereo use validation/evaluation dataset flags rather than a universal `--test-only` in all scripts.
- Weight selection: use modern weight enums such as `ResNet50_Weights.IMAGENET1K_V2`; do not use deprecated `pretrained=True`.
- Version warning: reference scripts can track latest source behavior and may not match an older installed package. Use scripts from the same TorchVision release when reproducibility matters.

## Classification

Baseline training plan, usually multi-GPU and long-running:

```bash
torchrun --nproc_per_node=<gpus> train.py --data-path <imagenet-root> --model resnet50 --batch-size 32 --epochs 90 --lr 0.1
```

Evaluation-only with a specific weight enum and weight-specific preprocessing choices:

```bash
torchrun --nproc_per_node=<gpus> train.py --data-path <imagenet-root> --model resnet50 --test-only --weights ResNet50_Weights.IMAGENET1K_V2
```

Useful knobs include `--auto-augment`, `--random-erase`, `--mixup-alpha`, `--cutmix-alpha`, `--model-ema`, `--interpolation`, `--val-resize-size`, `--val-crop-size`, `--train-crop-size`, `--amp`, and `--use-v2`. For architectures with special validation sizes, prefer checking the weight enum metadata and transforms in `../models-and-weights/`.

## Quantization

Post-training quantization is CPU-oriented and still needs calibration/evaluation data:

```bash
python train_quantization.py --data-path <imagenet-root> --device cpu --post-training-quantize --qbackend fbgemm --model resnet50 --weights ResNet50_Weights.IMAGENET1K_V1
```

Quantization-aware training is a long training job, often launched with GPUs:

```bash
torchrun --nproc_per_node=<gpus> train_quantization.py --data-path <imagenet-root> --model mobilenet_v2 --qbackend qnnpack
```

Important flags include `--num-calibration-batches`, `--num-observer-update-epochs`, `--num-batch-norm-update-epochs`, `--eval-batch-size`, `--qbackend`, `--device`, `--test-only`, and `--post-training-quantize`.

## Detection

COCO detection fine-tuning or reproduction plan, unsafe by default because it needs COCO, pycocotools, GPUs, and long training:

```bash
torchrun --nproc_per_node=<gpus> train.py --data-path <coco-root> --dataset coco --model fasterrcnn_resnet50_fpn --epochs 26 --lr-steps 16 22 --aspect-ratio-group-factor 3 --weights-backbone ResNet50_Weights.IMAGENET1K_V1
```

Evaluation-only plan:

```bash
python train.py --data-path <coco-root> --dataset coco --model fasterrcnn_resnet50_fpn --test-only --weights FasterRCNN_ResNet50_FPN_Weights.COCO_V1
```

Task-specific flags include `--dataset coco`, `--dataset coco_kp`, `--data-augmentation hflip|lsj|multiscale|ssd|ssdlite`, `--rpn-score-thresh`, `--trainable-backbone-layers`, `--use-copypaste`, `--weights`, and `--weights-backbone`.

## Segmentation

COCO-style segmentation references use small per-GPU batches and often auxiliary loss:

```bash
torchrun --nproc_per_node=<gpus> train.py --data-path <coco-root> --dataset coco --model deeplabv3_resnet50 --batch-size 4 --lr 0.02 --aux-loss --weights-backbone ResNet50_Weights.IMAGENET1K_V1
```

Evaluation-only plan:

```bash
python train.py --data-path <coco-root> --dataset coco --model deeplabv3_resnet50 --test-only --weights DeepLabV3_ResNet50_Weights.COCO_WITH_VOC_LABELS_V1
```

Important flags include `--aux-loss`, `--weights-backbone`, `--amp`, `--backend`, and `--use-v2`.

## Video classification

Kinetics training is very large; the reference defaults assume many GPUs and large video storage:

```bash
torchrun --nproc_per_node=<gpus> train.py --data-path <kinetics-root> --kinetics-version 400 --model r3d_18 --clip-len 16 --frame-rate 15 --clips-per-video 5 --batch-size 24 --cache-dataset --sync-bn --amp
```

Evaluation-only plan:

```bash
python train.py --data-path <kinetics-root> --kinetics-version 400 --model r3d_18 --test-only --weights R3D_18_Weights.KINETICS400_V1 --clip-len 16 --clips-per-video 1
```

Key flags include `--clip-len`, `--frame-rate`, `--clips-per-video`, `--train-resize-size`, `--train-crop-size`, `--val-resize-size`, `--val-crop-size`, `--kinetics-version`, and `--cache-dataset`.

## Optical flow

RAFT training is staged and long-running. A safe response usually prepares a plan rather than launching it:

```bash
torchrun --nproc_per_node=<gpus> train.py --dataset-root <flow-root> --name raft_chairs --model raft_large --train-dataset chairs --batch-size 2 --lr 0.0004 --weight-decay 0.0001 --epochs 72 --output-dir <output-dir>
```

Validation plan with pretrained weights:

```bash
python train.py --dataset-root <flow-root> --model raft_large --val-dataset sintel --batch-size 1 --weights Raft_Large_Weights.C_T_SKHT_V2
```

Important flags include `--train-dataset chairs|things`, `--val-dataset sintel|kitti`, `--num_flow_updates`, `--freeze-batch-norm`, `--gamma`, `--resume`, `--weights`, and `--output-dir`.

## Similarity learning

The similarity reference is simpler and defaults to FashionMNIST-style embedding training with triplet loss, but it can still download or read data depending on configuration:

```bash
python train.py --dataset-dir <data-root> --labels-per-batch 8 --samples-per-label 4 --epochs 10 --margin 1.0
```

Evaluation-only plan:

```bash
python train.py --dataset-dir <data-root> --test-only --resume <checkpoint-path>
```

Key flags include `--labels-per-batch`, `--samples-per-label`, `--eval-batch-size`, `--margin`, `--save-dir`, `--resume`, and `--test-only`.

## Stereo depth

Stereo depth training depends on removed/prototype-era components in some source history and should be treated as fragile reference evidence. Do not promise it works against an arbitrary stable install.

Training plan for CREStereo-like data mixtures:

```bash
torchrun --nproc_per_node=<gpus> train.py --dataset-root <stereo-root> --name crestereo_plan --model crestereo_base --train-datasets crestereo eth3d-train middlebury2014-other --dataset-steps 264000 18000 18000 --batch-size 2 --lr 0.0004 --min-lr 0.00002 --lr-decay-method cosine --warmup-steps 6000 --clip-grad-norm 1.0
```

Evaluation is commonly described with a cascade evaluation script rather than only `train.py`:

```bash
python cascade_evaluation.py --dataset middlebury2014-train --batch-size 1 --dataset-root <stereo-root> --model crestereo_base --weights CREStereo_Base_Weights.CRESTEREO_ETH_MBL_V1
```

Important flags include `--train-datasets`, `--dataset-steps`, `--eval-size`, `--resize-size`, `--crop-size`, `--scale-range`, `--max-disparity`, `--mixed-precision`, `--metrics`, `--weights`, and `--resume-path`.
