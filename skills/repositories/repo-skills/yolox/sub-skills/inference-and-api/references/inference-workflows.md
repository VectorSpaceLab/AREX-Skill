# YOLOX Inference Workflows

This reference distills YOLOX PyTorch inference behavior into checkout-independent commands and API recipes.

## Demo command patterns

Package-style module commands are preferred:

```bash
python -m yolox.tools.demo image -n yolox-s -c yolox_s.pth --path image.jpg --conf 0.25 --nms 0.45 --tsize 640 --save_result --device cpu
python -m yolox.tools.demo image -f path/to/exp.py -c custom.pth --path image.jpg --device gpu --fp16
python -m yolox.tools.demo video -n yolox-s -c yolox_s.pth --path video.mp4 --save_result --device gpu
python -m yolox.tools.demo webcam -n yolox-s -c yolox_s.pth --camid 0 --device gpu
```

Important flags:

| Flag | Meaning | Notes |
|---|---|---|
| `image`, `video`, `webcam` | Demo mode | `image` accepts a file or directory; video/webcam use OpenCV capture. |
| `-n, --name` | Built-in model name | Use for packaged YOLOX defaults. |
| `-f, --exp_file` | Custom `Exp` file | Takes priority for custom class counts, sizes, or architecture. |
| `-c, --ckpt` | Checkpoint | Required for real inference unless using TensorRT mode with a generated TRT module. |
| `--path` | Input image directory/file or video file | Validate existence and OpenCV readability before heavy work. |
| `--device cpu|gpu` | Runtime device | `gpu` moves the model and inputs to CUDA. |
| `--fp16` | Half precision | Use only on compatible CUDA devices. |
| `--conf`, `--nms`, `--tsize` | Test thresholds/size | Override `exp.test_conf`, `exp.nmsthre`, `exp.test_size`. |
| `--legacy` | Old preprocessing compatibility | Needed for older weights affected by YOLOX preprocessing changes. |
| `--fuse` | Fuse Conv+BN | Do not combine with TensorRT mode. |
| `--trt` | Use generated TensorRT module | Route setup and conversion to export/deployment. |

## Python API recipe

```python
import cv2
import torch
from yolox.data.data_augment import ValTransform
from yolox.data.datasets import COCO_CLASSES
from yolox.exp import get_exp
from yolox.utils import fuse_model, postprocess, vis

exp = get_exp(exp_file=None, exp_name="yolox-s")
exp.test_conf = 0.25
exp.nmsthre = 0.45
exp.test_size = (640, 640)

model = exp.get_model()
ckpt = torch.load("yolox_s.pth", map_location="cpu")
state = ckpt["model"] if isinstance(ckpt, dict) and "model" in ckpt else ckpt
model.load_state_dict(state)
model.eval()
# model = fuse_model(model)  # optional

img = cv2.imread("image.jpg")
assert img is not None, "image could not be read"
height, width = img.shape[:2]
ratio = min(exp.test_size[0] / height, exp.test_size[1] / width)
preproc = ValTransform(legacy=False)
tensor, _ = preproc(img, None, exp.test_size)
tensor = torch.from_numpy(tensor).unsqueeze(0).float()

with torch.no_grad():
    outputs = model(tensor)
    outputs = postprocess(outputs, exp.num_classes, exp.test_conf, exp.nmsthre, class_agnostic=True)

if outputs[0] is not None:
    det = outputs[0].cpu()
    boxes = det[:, 0:4] / ratio
    scores = det[:, 4] * det[:, 5]
    class_ids = det[:, 6]
    annotated = vis(img.copy(), boxes, scores, class_ids, exp.test_conf, COCO_CLASSES)
    cv2.imwrite("yolox_result.jpg", annotated)
```

For CUDA, move model and input tensor to CUDA. Apply `.half()` only when using FP16 on CUDA.

## Output convention

`postprocess` returns a list with one element per input image. Each non-empty tensor has columns `x1, y1, x2, y2, objectness, class_confidence, class_id`. The visualization score is `objectness * class_confidence`. Divide predicted boxes by the preprocessing ratio to map back to original image pixels.

## Video/webcam notes

Open frames with `cv2.VideoCapture`, check each `ret` value, run the same preprocessing/model/postprocess/visualization path per frame, and use `cv2.VideoWriter` only when saving. In headless environments, avoid GUI display and save outputs instead.

## Lightweight validation

From this reference directory:

```bash
python ../scripts/yolox_inference_smoke.py --name yolox-nano --device auto --test-size 64
python ../scripts/yolox_inference_smoke.py --name yolox-nano --device auto --test-size 64 --dummy-forward
```

A dummy forward proves architecture execution, not checkpoint accuracy or detection quality.
