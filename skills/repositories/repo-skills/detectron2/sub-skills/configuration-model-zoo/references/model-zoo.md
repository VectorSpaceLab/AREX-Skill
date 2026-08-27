# Detectron2 Model Zoo Usage

The Detectron2 model zoo exposes official config files and pretrained checkpoint URLs by path relative to the installed package's `configs/` collection. Use these APIs instead of hard-coding source checkout paths.

## Core APIs

```python
from detectron2 import model_zoo

cfg_file = model_zoo.get_config_file("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_1x.yaml")
url = model_zoo.get_checkpoint_url("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_1x.yaml")
yacs_cfg = model_zoo.get_config("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_1x.yaml", trained=False)
lazy_cfg = model_zoo.get_config("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_1x.py", trained=False)
```

API behavior:

- `get_config_file(config_path)` returns the installed config file path for a path relative to the model-zoo config collection. It raises `RuntimeError` when the config is not available.
- `get_checkpoint_url(config_path)` returns the official pretrained URL when a mapping exists. It does not download the checkpoint by itself.
- `get_config(config_path, trained=False)` returns a `CfgNode` for `.yaml` configs and a LazyConfig/OmegaConf config for `.py` configs.
- `get_config(config_path, trained=True)` injects the official trained checkpoint into `cfg.MODEL.WEIGHTS` for Yacs configs, or into `cfg.train.init_checkpoint` for LazyConfigs that define that field.
- `get(config_path, trained=False, device=None)` builds a model and loads the configured checkpoint through `DetectionCheckpointer`; this may access local files or URLs and is not a static inspection API.

## Config Path Conventions

Use paths such as:

```text
COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml
COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_1x.yaml
COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_1x.py
COCO-Keypoints/keypoint_rcnn_R_50_FPN_1x.yaml
COCO-PanopticSegmentation/panoptic_fpn_R_50_1x.py
Misc/scratch_mask_rcnn_R_50_FPN_3x_gn.yaml
common/models/mask_rcnn_fpn.py
common/coco_schedule.py
new_baselines/mask_rcnn_R_50_FPN_100ep_LSJ.py
```

Notes:

- The extension matters: `.yaml` selects Yacs behavior; `.py` selects LazyConfig behavior.
- Checkpoint URL lookup strips `.yaml` or `.py` before checking the official URL map, so corresponding YAML/Python stems can resolve to the same URL when listed.
- Some LazyConfig files under `common/` are reusable components rather than complete trainable detector configs; they may not have official checkpoint URLs.
- Official model-zoo tables include dataset assumptions, schedules, reported metrics, and download URLs, but future agents should use the APIs above rather than links into the original checkout.

## Safe Static Inspection

Prefer this sequence when the user asks to inspect or validate a config without network access:

```python
from detectron2 import model_zoo
from detectron2.config import LazyConfig
from detectron2.config import CfgNode

cfg = model_zoo.get_config("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_1x.yaml", trained=False)
if isinstance(cfg, CfgNode):
    print(cfg.MODEL.DEVICE)
    print(cfg.MODEL.WEIGHTS)
else:
    print(LazyConfig.to_py(cfg))
```

Use `trained=False` to avoid injecting official checkpoint URLs into the loaded config. If the user only needs the official checkpoint location, call `get_checkpoint_url()` and print it; do not build the model.

## CPU Inference Config Without Network Validation

For a YAML model-zoo config with explicit local weights:

```python
from detectron2 import model_zoo

cfg = model_zoo.get_config("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_1x.yaml", trained=False)
cfg.MODEL.DEVICE = "cpu"
cfg.MODEL.WEIGHTS = "/models/model_final.pth"
```

This is a configuration transformation only. It does not prove that `/models/model_final.pth` exists or is compatible. Runtime loading belongs to inference/training workflows.

For LazyConfig model-zoo configs:

```python
from detectron2 import model_zoo
from detectron2.config import LazyConfig

cfg = model_zoo.get_config("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_1x.py", trained=False)
LazyConfig.apply_overrides(cfg, [
    "model.device='cpu'",
    "train.init_checkpoint='/models/model_final.pth'",
])
```

If the LazyConfig lacks `train.init_checkpoint`, do not invent a weight field without checking the config structure using `LazyConfig.to_py()`.

## Network and Download Expectations

- `get_checkpoint_url()` returns a string URL and does not download.
- `get_config(..., trained=True)` injects a URL but does not build a model by itself.
- `get()` builds a model and loads `MODEL.WEIGHTS` or `train.init_checkpoint`; checkpoint loading can require network access if the value is an HTTP URL and the local cache does not already contain it.
- Avoid `DefaultPredictor(cfg)` as a config check because it builds a model and loads weights.
- Avoid calling original demo CLIs as validation; use API-level static inspection unless the broader workflow explicitly owns runtime inference.
