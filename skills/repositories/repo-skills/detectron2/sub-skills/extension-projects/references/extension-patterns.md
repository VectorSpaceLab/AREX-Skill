# Extension Patterns

Detectron2 is designed for research extension through two complementary interfaces:

- Config-driven defaults: builders receive a `CfgNode` and use strings in the config to select registered components.
- Explicit Python construction: model pieces can be instantiated directly with documented constructor arguments when config-only wiring is too limited.

Use config-driven defaults when the extension should be selectable from a Yacs config. Use explicit construction when a small research change requires Python objects, custom losses, custom submodules, or partial reuse of built-in components.

## Registries

Detectron2 exposes `detectron2.utils.registry.Registry`, backed by `fvcore.common.registry.Registry`, plus `detectron2.utils.registry.locate` for resolving Python import strings.

Common model registries include:

| Registry | Config key or builder | Registered callable shape |
| --- | --- | --- |
| `META_ARCH_REGISTRY` | `build_model(cfg)` and `cfg.MODEL.META_ARCHITECTURE` | callable receiving `cfg`, returning `torch.nn.Module` |
| `BACKBONE_REGISTRY` | `build_backbone(cfg, input_shape=None)` and `cfg.MODEL.BACKBONE.NAME` | callable receiving `(cfg, input_shape)`, returning `Backbone` |
| `ROI_HEADS_REGISTRY` | `build_roi_heads(cfg, input_shape)` and `cfg.MODEL.ROI_HEADS.NAME` | callable receiving `(cfg, input_shape)`, returning ROI heads module |
| `PROPOSAL_GENERATOR_REGISTRY` | `build_proposal_generator(cfg, input_shape)` | callable receiving `(cfg, input_shape)` |
| `RPN_HEAD_REGISTRY` | RPN head construction | callable receiving `(cfg, input_shape)` |
| `ROI_BOX_HEAD_REGISTRY` | `build_box_head(cfg, input_shape)` | callable receiving `(cfg, input_shape)` |
| `ROI_MASK_HEAD_REGISTRY` | `build_mask_head(cfg, input_shape)` | callable receiving `(cfg, input_shape)` |
| `ROI_KEYPOINT_HEAD_REGISTRY` | `build_keypoint_head(cfg, input_shape)` | callable receiving `(cfg, input_shape)` |
| `SEM_SEG_HEADS_REGISTRY` | semantic-segmentation head construction | callable receiving `(cfg, input_shape)` |

Registration only happens when Python imports the module containing the `@REGISTRY.register()` decorator. A config string cannot resolve a class that has not been imported in the current process.

## Minimal Registry Pattern

```python
from detectron2.modeling import BACKBONE_REGISTRY, Backbone
from detectron2.layers import ShapeSpec

@BACKBONE_REGISTRY.register()
class ToyBackbone(Backbone):
    def __init__(self, cfg, input_shape):
        super().__init__()
        # initialize layers here

    def forward(self, images):
        return {"toy": ...}

    def output_shape(self):
        return {"toy": ShapeSpec(channels=64, stride=16)}
```

Then make sure the module is imported before building the model:

```python
import my_project.toy_backbone  # registers ToyBackbone
cfg.MODEL.BACKBONE.NAME = "ToyBackbone"
model = build_model(cfg)
```

If lookup fails, first prove that import side effects happened:

```python
from detectron2.modeling import BACKBONE_REGISTRY
assert BACKBONE_REGISTRY.get("ToyBackbone")
```

## `@configurable`

`detectron2.config.configurable` lets a class `__init__` or function support both explicit arguments and config-driven construction.

For classes:

```python
from detectron2.config import configurable

class MyHead:
    @configurable
    def __init__(self, *, num_classes, hidden_dim):
        self.num_classes = num_classes
        self.hidden_dim = hidden_dim

    @classmethod
    def from_config(cls, cfg, input_shape=None):
        return {
            "num_classes": cfg.MODEL.ROI_HEADS.NUM_CLASSES,
            "hidden_dim": cfg.MODEL.MY_HEAD.HIDDEN_DIM,
        }
```

Then both forms work:

```python
head = MyHead(num_classes=3, hidden_dim=256)
head = MyHead(cfg)
head = MyHead(cfg, hidden_dim=512)
```

The `from_config` callable must take `cfg` as its first argument. Extra arguments accepted by `from_config` can be forwarded, and extra keyword overrides are merged into the final explicit argument dictionary.

## Config Adders

Project packages commonly expose `add_*_config(cfg)` functions that add new keys to a default config before a project YAML or project-specific options are merged.

Typical order:

```python
from detectron2.config import get_cfg
from detectron2.projects.point_rend import add_pointrend_config

cfg = get_cfg()
add_pointrend_config(cfg)
cfg.merge_from_file("path/to/pointrend_config.yaml")
cfg.merge_from_list(["MODEL.ROI_MASK_HEAD.POINT_HEAD_ON", "True"])
```

If you merge a project config before calling the config adder, Yacs may reject unknown keys such as `MODEL.POINT_HEAD` or project-specific solver/input keys.

## Custom `DefaultTrainer` Subclasses

Subclass `DefaultTrainer` when you want to keep Detectron2's default training loop but replace selected pieces:

```python
from detectron2.engine import DefaultTrainer

class Trainer(DefaultTrainer):
    @classmethod
    def build_model(cls, cfg):
        model = super().build_model(cfg)
        # wrap, freeze, or inspect the model here
        return model

    @classmethod
    def build_evaluator(cls, cfg, dataset_name, output_folder=None):
        # return evaluator(s) for the task
        ...
```

Common override points are `build_model`, `build_optimizer`, `build_lr_scheduler`, `build_train_loader`, `build_test_loader`, `build_evaluator`, `build_hooks`, and `test_with_TTA`. Keep data-format changes synchronized with dataset registration and mapper logic; a new model task usually needs more than a registry entry.

## LazyConfig and `locate`

LazyConfig-based workflows can use `LazyCall(target)` and import strings resolved with `locate`. For registry-style extensions, the same import rule applies: modules defining custom classes must be importable and imported before the object is referenced by name.

Use `locate("package.module.ClassName")` for dynamic import-string resolution, not for arbitrary untrusted strings. It may fall back to Hydra's locator when `pydoc.locate` is insufficient.
