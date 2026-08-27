# RefineCAM and ARCC

## RefineCAM

`RefineCAM` wraps a base CAM method over multiple target layers and combines the
per-layer outputs by elementwise product after normalization. It is useful when
an early layer adds localization detail and a later layer adds class signal.

Typical use:

```python
from pytorch_grad_cam.refine_cam import RefineCAM
from pytorch_grad_cam import GradCAMPlusPlus

cam = RefineCAM(
    model=model,
    target_layers=[model.layer4[-1], model.layer4[-2]],
    base_method=GradCAMPlusPlus,
)
grayscale_cam = cam(input_tensor=input_tensor, targets=targets)
```

## ARCC

ARCC evaluates explanation quality by measuring how a CAM-based perturbation
changes a model's confidence. It is implemented in
`pytorch_grad_cam.metrics.arcc` and can be used after a CAM is produced.

Example:

```python
from pytorch_grad_cam.metrics.arcc import ARCC

metric = ARCC(base_method=cam)
score = metric(input_tensor=input_tensor, grayscale_cams=grayscale_cam, targets=targets, model=model)
```

## Practical notes

- Use small batches and deterministic models while debugging.
- `RefineCAM` still depends on a base CAM class and valid target layers.
- ROAD/ARCC metrics can be expensive; keep synthetic smoke tests tiny.
