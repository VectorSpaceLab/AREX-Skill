# Config selection

AdelaiDet is config-first. Select the model family from the task, then choose a YAML under the corresponding config directory.

## Family mapping

| User asks for | Start with | Notes |
| --- | --- | --- |
| Anchor-free object detection, FCOS | `configs/FCOS-Detection/` | Core detector; checkpoint conversion utility exists for official FCOS weights. |
| Instance segmentation with BlendMask | `configs/BlendMask/` | Needs basis/attention settings; see dataset semantic-mask requirements if enabled. |
| Conditional instance segmentation | `configs/CondInst/` | Can overlap with BoxInst; inspect config for weak-supervision settings. |
| Box-supervised instance segmentation | `configs/BoxInst/` | Dataset and pairwise-color settings matter. |
| SOLOv2 | `configs/SOLOv2/` | Requires OpenCV import through utility modules. |
| MEInst | `configs/MEInst-InstanceSegmentation/` | May require mask component/PCA artifacts from data-prep. |
| FCPose | `configs/FCPose/` | Needs keypoint/person data layout and FCPose mapper. |
| DenseCL | `configs/DenseCL/` | Specialized training/pretraining; not a demo/export-first path. |
| BAText/ABCNet/text spotting | `configs/BAText/` | Switch to `text-spotting` for dictionaries, Bezier data, and TextEvaluator. |

## Config loading rule

Always load configs through AdelaiDet defaults:

```python
from adet.config import get_cfg
cfg = get_cfg()
cfg.merge_from_file("/path/to/config.yaml")
cfg.merge_from_list(["MODEL.WEIGHTS", "/path/to/model.pth"])
cfg.freeze()
```

The repository train/demo/export scripts do this for you. Custom scripts that start from Detectron2 `get_cfg()` must call `add_adet_config(cfg)` before merging AdelaiDet YAML.

## Common overrides

| Override | Use |
| --- | --- |
| `MODEL.WEIGHTS /path/to/model.pth` | Load pretrained/checkpoint weights for eval/demo/export. |
| `OUTPUT_DIR output/my-run` | Change logs/checkpoints/metrics output directory. |
| `MODEL.DEVICE cuda` or `cpu` | Choose runtime device. CPU is not valid for every custom op workflow. |
| `SOLVER.IMS_PER_BATCH N` | Global training batch size. Keep consistent with GPU count. |
| `MODEL.FCOS.NUM_CLASSES N` | Change detection classes for FCOS-family heads. |
| `MODEL.BATEXT.CUSTOM_DICT path/to/dict.txt` | Text spotting custom dictionary. |
| `DATASETS.TRAIN (...)` / `DATASETS.TEST (...)` | Use registered dataset names. |

## Before launch checklist

- The environment passes `scripts/check_install.py --cuda-ops` for CUDA jobs.
- The config file belongs to the intended model family.
- Dataset names in the config are registered and annotation/image roots exist.
- `MODEL.WEIGHTS` exists for eval/demo/export.
- `OUTPUT_DIR` is writable and not accidentally pointing at another run.
- Optional family-specific artifacts exist (text dictionaries/lexicons, MEInst components, semantic masks).
