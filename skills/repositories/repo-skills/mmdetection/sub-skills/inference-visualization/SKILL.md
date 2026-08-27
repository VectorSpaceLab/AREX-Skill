---
name: inference-visualization
description: "Use MMDetection 3.3.0 public APIs for image, batch, folder,
  NumPy-array, video, large-image, visualization, prediction-dump, and
  deployment-route inference tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# inference-visualization

Use this sub-skill when the task is to run MMDetection inference, save predictions or visualizations, process arrays/videos/large images, or choose a deployment path. For config/model-zoo selection route to `configuration-model-zoo`; for training/testing route to `training-testing`; for dataset conversion and metrics route to `datasets-evaluation`.

## Fast Routes

- **High-level image/folder/batch inference:** use `mmdet.apis.DetInferencer`; see `references/api-reference.md` and `references/workflows.md`.
- **Scripted image inference:** run `scripts/mmdet_infer_image.py` for safe argparse around `DetInferencer`.
- **Raw downstream objects:** use `return_datasamples=True` or `init_detector` + `inference_detector`; see `references/api-reference.md`.
- **Headless visualization/dumping:** set `out_dir`, `no_save_pred`, and `no_save_vis` deliberately; see `references/workflows.md`.
- **Video, webcam, and large images:** prefer public API patterns and environment-aware caveats in `references/workflows.md`.
- **TorchServe/MMDeploy/ONNX/TensorRT route choice:** use `references/deployment.md`.
- **Known failures:** check `references/troubleshooting.md` before debugging package, device, GUI, checkpoint, or ABI errors.

## Minimal Examples

```python
from mmdet.apis import DetInferencer

inferencer = DetInferencer(model='rtmdet_tiny_8xb32-300e_coco', device='cpu')
result = inferencer('images/', batch_size=4, out_dir='outputs', no_save_pred=False, no_save_vis=True)
```

```python
import mmcv
from mmdet.apis import init_detector, inference_detector

model = init_detector('config.py', 'checkpoint.pth', device='cpu')
image_bgr = mmcv.imread('image.jpg')
sample = inference_detector(model, image_bgr)
```

## Packaged Helper

```shell
python scripts/mmdet_infer_image.py \
  image_or_folder rtmdet_tiny_8xb32-300e_coco --device cpu \
  --out-dir outputs --no-save-vis --save-pred
```

The helper uses public package APIs only and is safe for image files, image folders, model aliases, config files, local checkpoint files, and open-vocabulary prompt parameters supported by MMDetection.
