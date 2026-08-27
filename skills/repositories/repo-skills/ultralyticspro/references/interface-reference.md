# Ultralytics Interface Reference

## Purpose

Read this when you need verified runtime facts about the public `ultralytics`
package that the repo wrappers rely on.

## Verified package facts

- Installed distribution: `ultralytics` 8.4.118
- Python requirement from package metadata: `>=3.8`
- Public import root: `ultralytics`
- Main runtime classes used by this repo: `YOLO`, `RTDETR`

## Verified signatures

```python
YOLO(model: str | Path = 'yolo26n.pt', task: str | None = None, verbose: bool = False)
YOLO.train(self, trainer=None, **kwargs)
YOLO.predict(
    self,
    source: str | Path | int | Image.Image | list | tuple | np.ndarray | torch.Tensor = None,
    stream: bool = False,
    predictor=None,
    **kwargs,
) -> Iterator[Results | torch.Tensor] | list[Results] | list[torch.Tensor]
RTDETR(model: str = 'rtdetr-l.pt') -> None
RTDETR.train(self, trainer=None, **kwargs)
```

## Verified CLI syntax

The installed `yolo` command uses this syntax:

```text
yolo TASK MODE ARGS
```

- Tasks: `detect`, `segment`, `semantic`, `depth`, `classify`, `pose`, `obb`
- Modes: `train`, `val`, `predict`, `export`, `track`, `benchmark`
- Common special commands: `help`, `checks`, `version`, `settings`, `login`,
  `logout`, `copy-cfg`, `cfg`, `solutions help`

The `yolo --help` output in the verified environment also shows example command
forms for training, prediction, validation, export, and solutions usage.

## Packaged assets and config paths

These packaged files exist in the verified install and are safe to reference in
skill guidance:

- `assets/zidane.jpg`
- `assets/bus.jpg`
- `cfg/models/v8/yolov8.yaml`
- `cfg/models/v10/yolov10s.yaml`
- `cfg/models/11/yolo11.yaml`
- `cfg/models/11/yolo11-cls.yaml`
- `cfg/models/11/yolo11-obb.yaml`
- `cfg/models/11/yolo11-pose.yaml`
- `cfg/models/11/yolo11-seg.yaml`
- `cfg/models/rt-detr/rtdetr-l.yaml`

This path was **not** present in the verified install and therefore should be
treated as a custom local file path, not a bundled asset:

- `cfg_yolov12/yolo12.yaml`

## Practical implications for the repo wrappers

- Training wrappers should resolve packaged model configs against the installed
  `ultralytics` package root before execution.
- Prediction wrappers can default to the packaged `assets/zidane.jpg` sample
  instead of a repo-local image path.
- The `train-yolo12` preset needs a user-supplied local config file unless the
  target environment has a different Ultralytics build that provides it.
- First-time execution of a `.pt` weight name may download the pretrained model
  if it is not already cached.
