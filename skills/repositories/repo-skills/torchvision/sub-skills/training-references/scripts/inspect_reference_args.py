#!/usr/bin/env python3
"""Print safe static summaries of TorchVision reference training arguments.

This helper is intentionally self-contained: it does not import torchvision,
import original reference scripts, read datasets, download weights, or launch
training. It exists to help agents plan commands and inspect flag families.
"""

from __future__ import annotations

import argparse
import json
import textwrap

TASKS = {
    "classification": {
        "scripts": ["classification/train.py"],
        "safety": "Training is long-running and usually GPU/distributed; --test-only is evaluation-only but still needs ImageNet-style data and may download weights.",
        "required": ["--data-path", "--model"],
        "common_flags": [
            "--weights", "--test-only", "--batch-size", "--epochs", "--lr", "--opt",
            "--lr-scheduler", "--auto-augment", "--random-erase", "--mixup-alpha",
            "--cutmix-alpha", "--model-ema", "--interpolation", "--val-resize-size",
            "--val-crop-size", "--train-crop-size", "--amp", "--sync-bn", "--use-v2",
        ],
        "example_plan": "torchrun --nproc_per_node=<gpus> train.py --data-path <imagenet-root> --model resnet50 --test-only --weights ResNet50_Weights.IMAGENET1K_V2",
    },
    "quantization": {
        "scripts": ["classification/train_quantization.py"],
        "safety": "Post-training quantization can run on CPU but needs calibration data; QAT is a long training job.",
        "required": ["--data-path", "--model", "--qbackend"],
        "common_flags": [
            "--post-training-quantize", "--test-only", "--device", "--qbackend",
            "--num-calibration-batches", "--num-observer-update-epochs",
            "--num-batch-norm-update-epochs", "--eval-batch-size", "--weights",
            "--val-resize-size", "--val-crop-size", "--train-crop-size", "--use-v2",
        ],
        "example_plan": "python train_quantization.py --data-path <imagenet-root> --device cpu --post-training-quantize --qbackend fbgemm --model resnet50",
    },
    "detection": {
        "scripts": ["detection/train.py"],
        "safety": "COCO detection training/evaluation needs prepared COCO data, pycocotools, and often GPUs.",
        "required": ["--data-path", "--dataset", "--model"],
        "common_flags": [
            "--weights", "--weights-backbone", "--test-only", "--dataset", "--data-augmentation",
            "--aspect-ratio-group-factor", "--rpn-score-thresh", "--trainable-backbone-layers",
            "--use-copypaste", "--amp", "--sync-bn", "--use-v2",
        ],
        "example_plan": "python train.py --data-path <coco-root> --dataset coco --model fasterrcnn_resnet50_fpn --test-only --weights FasterRCNN_ResNet50_FPN_Weights.COCO_V1",
    },
    "segmentation": {
        "scripts": ["segmentation/train.py"],
        "safety": "Segmentation references need COCO-style masks/annotations; training is GPU-oriented.",
        "required": ["--data-path", "--dataset", "--model"],
        "common_flags": [
            "--weights", "--weights-backbone", "--test-only", "--aux-loss", "--batch-size",
            "--lr", "--lr-warmup-epochs", "--amp", "--backend", "--use-v2",
        ],
        "example_plan": "python train.py --data-path <coco-root> --dataset coco --model deeplabv3_resnet50 --test-only --weights DeepLabV3_ResNet50_Weights.COCO_WITH_VOC_LABELS_V1",
    },
    "video": {
        "scripts": ["video_classification/train.py"],
        "safety": "Kinetics-scale video training is storage- and GPU-heavy; even evaluation needs readable video data/codecs.",
        "required": ["--data-path", "--kinetics-version", "--model"],
        "common_flags": [
            "--weights", "--test-only", "--clip-len", "--frame-rate", "--clips-per-video",
            "--train-resize-size", "--train-crop-size", "--val-resize-size", "--val-crop-size",
            "--cache-dataset", "--sync-bn", "--amp",
        ],
        "example_plan": "python train.py --data-path <kinetics-root> --kinetics-version 400 --model r3d_18 --test-only --weights R3D_18_Weights.KINETICS400_V1 --clip-len 16 --clips-per-video 1",
    },
    "optical-flow": {
        "scripts": ["optical_flow/train.py"],
        "safety": "RAFT training is staged and expensive; validation still needs Sintel/KITTI/FlyingThings-style data.",
        "required": ["--dataset-root", "--model"],
        "common_flags": [
            "--train-dataset", "--val-dataset", "--weights", "--resume", "--output-dir",
            "--name", "--num_flow_updates", "--freeze-batch-norm", "--gamma", "--batch-size",
        ],
        "example_plan": "python train.py --dataset-root <flow-root> --model raft_large --val-dataset sintel --batch-size 1 --weights Raft_Large_Weights.C_T_SKHT_V2",
    },
    "similarity": {
        "scripts": ["similarity/train.py"],
        "safety": "Default training is smaller than other references but can still download/read data and run epochs.",
        "required": ["--dataset-dir"],
        "common_flags": [
            "--labels-per-batch", "--samples-per-label", "--eval-batch-size", "--epochs",
            "--lr", "--margin", "--save-dir", "--resume", "--test-only",
        ],
        "example_plan": "python train.py --dataset-dir <data-root> --labels-per-batch 8 --samples-per-label 4 --epochs 10",
    },
    "stereo-depth": {
        "scripts": ["depth/stereo/train.py", "depth/stereo/cascade_evaluation.py"],
        "safety": "Stereo references are fragile and may depend on prototype-era code; training is GPU-heavy and data-layout sensitive.",
        "required": ["--dataset-root", "--model"],
        "common_flags": [
            "--train-datasets", "--dataset-steps", "--test-datasets", "--weights", "--resume-path",
            "--eval-size", "--resize-size", "--crop-size", "--scale-range", "--max-disparity",
            "--mixed-precision", "--metrics", "--clip-grad-norm",
        ],
        "example_plan": "python cascade_evaluation.py --dataset middlebury2014-train --batch-size 1 --dataset-root <stereo-root> --model crestereo_base --weights CREStereo_Base_Weights.CRESTEREO_ETH_MBL_V1",
    },
}

ALIASES = {
    "video-classification": "video",
    "flow": "optical-flow",
    "optical_flow": "optical-flow",
    "stereo": "stereo-depth",
    "depth": "stereo-depth",
    "classification-quantization": "quantization",
}


def normalize_task(task: str) -> str:
    key = task.strip().lower().replace("_", "-")
    return ALIASES.get(key, key)


def print_task(name: str, data: dict[str, object], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps({"task": name, **data}, indent=2, sort_keys=True))
        return

    if output_format == "shell":
        print(f"# {name}")
        print(f"# Safety: {data['safety']}")
        print(data["example_plan"])
        return

    print(name)
    print("=" * len(name))
    print(textwrap.fill(str(data["safety"]), width=88))
    print(f"Scripts: {', '.join(data['scripts'])}")
    print(f"Required placeholders: {', '.join(data['required'])}")
    print("Common flags:")
    for flag in data["common_flags"]:
        print(f"  - {flag}")
    print("Example command plan:")
    print(f"  {data['example_plan']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely inspect static TorchVision reference argument summaries.")
    parser.add_argument("--list", action="store_true", help="List available task names.")
    parser.add_argument("--task", help="Show one task summary.")
    parser.add_argument("--format", choices=["text", "json", "shell"], default="text", help="Output format for --task.")
    args = parser.parse_args()

    if args.list:
        for name in sorted(TASKS):
            print(name)
        return 0

    if not args.task:
        parser.error("choose --list or --task <name>")

    task = normalize_task(args.task)
    if task not in TASKS:
        choices = ", ".join(sorted(TASKS))
        parser.error(f"unknown task {args.task!r}; choose one of: {choices}")

    print_task(task, TASKS[task], args.format)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
