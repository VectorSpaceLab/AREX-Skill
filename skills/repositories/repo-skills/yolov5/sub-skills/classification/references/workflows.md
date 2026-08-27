# Classification Workflows

## Predict

`classify/predict.py` supports image, video, directory, glob, list, webcam, screen, and stream sources. The inspected parser includes flags such as `--weights`, `--source`, `--data`, `--imgsz`, `--device`, `--view-img`, `--save-txt`, `--nosave`, `--update`, `--project`, `--name`, `--exist-ok`, `--half`, `--dnn`, and `--vid-stride`.

Example shape:

```bash
python classify/predict.py --weights yolov5s-cls.pt --source data/images/bus.jpg --imgsz 224 --device cpu
```

Guidance:

- Use local files for deterministic work.
- Keep `--imgsz 224` unless the task explicitly wants another classifier input size.
- Use `--nosave` for inspection-only runs.
- Use `--half` only on a compatible CUDA device.

## Train

`classify/train.py` trains YOLOv5-cls or torchvision models.

Common inspected flags include `--model`, `--data`, `--epochs`, `--batch-size`, `--imgsz`, `--nosave`, `--cache`, `--device`, `--workers`, `--project`, `--name`, `--exist-ok`, `--pretrained`, `--freeze`, `--dropout`, `--cutoff`, `--multi-scale`, `--optimizer`, `--seed`, and `--lr`/scheduler-style controls where exposed by the CLI.

Example shapes:

```bash
python classify/train.py --model yolov5s-cls.pt --data cifar100 --epochs 5 --imgsz 224 --batch-size 128
python classify/train.py --model resnet50 --data imagenette --epochs 3 --imgsz 224 --device 0
```

Guidance:

- Named datasets such as `cifar100`, `imagenette`, or `imagenet` may download data.
- For a local dataset, use ImageFolder-style directory layout and confirm class subdirectories exist.
- `--pretrained` controls whether the selected model begins with pretrained weights.
- `--freeze` and `--cutoff` matter when adapting YOLOv5-cls architectures or torchvision backbones.
- Training writes run artifacts; confirm `--project` and `--name` before launching.

## Validate

`classify/val.py` validates classification accuracy.

Common parser flags include `--data`, `--weights`, `--batch-size`, `--imgsz`, `--device`, `--workers`, `--verbose`, `--project`, `--name`, `--exist-ok`, `--half`, and `--dnn`.

Example shapes:

```bash
python classify/val.py --weights yolov5m-cls.pt --data ../datasets/imagenet --imgsz 224
python classify/val.py --weights yolov5s-cls.pt --data path/to/imagefolder --imgsz 224 --device cpu
```

## Model-family notes

- YOLOv5-cls checkpoints use the `*-cls.pt` naming family.
- TorchVision models such as `resnet50` and `efficientnet_b0` are also supported by the training script.
- Classification outputs are probability vectors or top-k predictions, not boxes or masks.
- If the task expects detection outputs, route back to the detection sub-skill.
