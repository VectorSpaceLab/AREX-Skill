# Classification Data and Outputs

## Dataset layout

YOLOv5 classification accepts either named datasets or local ImageFolder-style directories.

### Local directory layout

```text
root/
  train/
    class_a/*.jpg
    class_b/*.jpg
  val/
    class_a/*.jpg
    class_b/*.jpg
```

### Named datasets

Supported named datasets in the README and CLI examples include MNIST, Fashion-MNIST, CIFAR10, CIFAR100, Imagenette, Imagewoof, and ImageNet. Named datasets may download data and may need separate storage approval.

## Model/data pairing

- Use `yolov5n-cls.pt` through `yolov5x-cls.pt` for YOLOv5 classification models.
- Use torchvision model names such as `resnet50` or `efficientnet_b0` when the task calls for a standard classifier backbone.
- Keep the model family and dataset size aligned with the compute budget.

## Outputs

Classification outputs are probabilities/top-k labels, not boxes or masks. Any workflow that expects detection-style JSON, boxes, or masks should be routed to another sub-skill.

## Common validation checks

1. Confirm train/val directories exist.
2. Confirm each class has its own subdirectory.
3. Confirm class names are consistent across train and val.
4. Confirm the chosen model family is classification-specific.
5. Use `--imgsz 224` unless the task explicitly wants another input size.
6. Start with a tiny local dataset or a named smoke dataset before ImageNet-scale work.
