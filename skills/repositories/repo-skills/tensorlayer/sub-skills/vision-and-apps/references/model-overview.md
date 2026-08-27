# Model Overview

## Verified image constructors

- `vgg16(pretrained=False, end_with='outputs', mode='dynamic', name=None)`
- `MobileNetV1(pretrained=False, end_with='out', name=None)`
- `ResNet50(pretrained=False, end_with='fc1000', n_classes=1000, name=None)`
- `SqueezeNetV1(pretrained=False, end_with='out', name=None)`

## App wrappers and modules

- `tensorlayer.app.computer_vision.object_detection('yolo4-mscoco')`
- `tensorlayer.app.computer_vision.human_pose_estimation('3D-pose')`
- `tensorlayer.app.YOLOv4(NUM_CLASS=80, pretrained=True|False)`
- `tensorlayer.app.CGCNN(pretrained=True|False)`

## Usage notes

- Use `pretrained=False` for bundled smoke checks.
- The wrapper classes expect external model/data files when `pretrained=True`.
- YOLOv4 uses a fixed input size of 416x416 in the source implementation.
- Headless environments should avoid interactive `image.show()` or GUI assumptions.

## Evidence summary

This page distills the pretrained CNN tutorials, app-wrapper source, spatial-transformer notes, and quantized-vision examples into constructor and dependency guidance. Full examples with external files remain reference-only and are not needed by the runtime skill.
