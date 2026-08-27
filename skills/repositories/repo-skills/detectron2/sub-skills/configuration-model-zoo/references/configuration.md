# Detectron2 Configuration Systems

Detectron2 has two configuration systems. Treat them as distinct tools with different file formats, object types, and override grammars.

## Quick Choice

| Need | Use | File type | Main APIs |
| --- | --- | --- | --- |
| Built-in legacy detector configs, legacy training CLI-style workflows, `MODEL.*` keys | Yacs config | `.yaml` / `.yml` | `get_cfg()`, `CfgNode.merge_from_file()`, `CfgNode.merge_from_list()`, `cfg.dump()` |
| Python-composable configs, model-zoo `common/` and `new_baselines/`, recursive object construction | LazyConfig | `.py` and loadable `.yaml` | `LazyConfig.load()`, `LazyConfig.apply_overrides()`, `LazyConfig.to_py()`, `LazyCall`, `instantiate()` |

## Yacs YAML Configs

A Yacs workflow starts from Detectron2 defaults, merges one or more YAML files, then applies CLI-style key/value overrides.

```python
from detectron2.config import get_cfg
from detectron2 import model_zoo

cfg = get_cfg()
cfg.merge_from_file(model_zoo.get_config_file("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_1x.yaml"))
cfg.merge_from_list([
    "MODEL.DEVICE", "cpu",
    "MODEL.WEIGHTS", "/models/mask_rcnn_final.pth",
    "INPUT.MIN_SIZE_TEST", "800",
])
print(cfg.dump())
```

Key details:

- `get_cfg()` returns a `CfgNode` populated with Detectron2 default keys.
- `merge_from_file(path)` loads YAML and resolves Detectron2's `_BASE_` inheritance before applying child values.
- `_BASE_: base.yaml` loads a relative base config first; child values override conflicts from the base.
- `merge_from_list()` accepts a flat list of strings as alternating `KEY`, `VALUE` entries, not `KEY=VALUE` entries.
- Yacs values are limited by the configured schema. For custom projects, add project-specific defaults before merging project config files.
- `cfg.dump()` produces a YAML representation suitable for review or saving.

Common Yacs override examples:

```text
MODEL.WEIGHTS /models/model_final.pth
MODEL.DEVICE cpu
SOLVER.IMS_PER_BATCH 2
DATASETS.TRAIN ('my_train',)
INPUT.MIN_SIZE_TEST 1000
```

Do not use LazyConfig syntax such as `MODEL.DEVICE=cpu` inside `merge_from_list()`.

## LazyConfig Python Configs

LazyConfig loads Python config files into OmegaConf-style config objects. The files can define dictionaries, import other config files, use simple Python expressions, and describe objects that are created later with `instantiate()`.

```python
from detectron2.config import LazyConfig, instantiate
from detectron2 import model_zoo

cfg = model_zoo.get_config("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_1x.py")
LazyConfig.apply_overrides(cfg, [
    "model.device='cpu'",
    "train.init_checkpoint='/models/model_final.pth'",
    "dataloader.train.total_batch_size=2",
])
print(LazyConfig.to_py(cfg))
model = instantiate(cfg.model)
```

Key details:

- `LazyConfig.load(filename, keys=None)` accepts `.py`, `.yaml`, or `.yml` files.
- For Python configs, the return value contains global dictionaries/config objects that do not start with `_`; pass `keys="model"` or `keys=("model", "train")` to select entries.
- `LazyConfig.load_rel()` supports relative loading from inside another config file.
- Relative imports in LazyConfig files can only import other config files, not directories or arbitrary packages by relative path.
- `LazyConfig.apply_overrides(cfg, overrides)` uses `key=value` syntax. With Hydra installed, it uses Hydra override parsing; otherwise it falls back to a simpler parser.
- `LazyConfig.to_py(cfg, prefix="cfg.")` renders human-readable pseudo-Python for inspection; it is not guaranteed to be executable.
- `LazyConfig.save(cfg, filename)` writes YAML when possible and may create `filename + ".pkl"` if objects are not YAML-serializable.

Common LazyConfig override examples:

```text
model.device='cpu'
train.init_checkpoint='/models/model_final.pth'
dataloader.train.total_batch_size=2
optimizer.lr=0.00025
train.max_iter=1000
```

Do not use Yacs syntax such as `MODEL.DEVICE cpu` with `LazyConfig.apply_overrides()`.

## LazyCall and Instantiate

LazyConfig uses recursive instantiation to describe calls without executing them at config-load time.

```python
from detectron2.config import LazyCall as L, instantiate
import torch.nn as nn

cfg = L(nn.Conv2d)(in_channels=3, out_channels=16, kernel_size=3)
cfg.out_channels = 32
layer = instantiate(cfg)
```

The config object contains a `_target_` entry plus keyword arguments. `instantiate()` recursively builds nested `_target_` configs, lists, and supported structured objects. Use this when explaining LazyConfig internals or debugging why an object construction fails.

## CPU and Weights Conversion Patterns

Yacs and LazyConfig store device and weight locations in different places:

| Task | Yacs | LazyConfig model-zoo convention |
| --- | --- | --- |
| Force CPU model construction | `cfg.MODEL.DEVICE = "cpu"` or `MODEL.DEVICE cpu` | `cfg.model.device = "cpu"` when present, or build through `model_zoo.get(..., device="cpu")` |
| Use explicit trained weights | `cfg.MODEL.WEIGHTS = "/path/model.pth"` | `cfg.train.init_checkpoint = "/path/model.pth"` when the config has `cfg.train.init_checkpoint` |
| Get official trained URL | `model_zoo.get_checkpoint_url("...yaml")` | `model_zoo.get_checkpoint_url("...py")` if a URL mapping exists for the same stem |

For static validation, avoid loading weight files. Confirm that the selected key exists and that the path or URL is intentional; let training/evaluation or inference workflows perform actual checkpoint loading.
