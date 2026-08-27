# Projects Overview

Detectron2 includes research projects that demonstrate using Detectron2 as a library. They are useful as extension examples, but they are not all equally packaged or supported. Avoid installing broad optional stacks unless the user asks for a specific project and the environment needs its dependencies.

## Installed Project Packages

The package setup maps a small set of project implementations into importable `detectron2.projects` modules:

| Import | Purpose | Config adder | Notes |
| --- | --- | --- | --- |
| `detectron2.projects.point_rend` | PointRend instance and semantic segmentation components | `add_pointrend_config(cfg)` | Adds point-head, implicit PointRend, crop/color-augmentation keys, and registers PointRend heads when imported. |
| `detectron2.projects.deeplab` | DeepLabV3 and DeepLabV3+ semantic segmentation components | `add_deeplab_config(cfg)` | Adds DeepLab semantic-head, poly LR, and ResNet dilation/stem settings. |
| `detectron2.projects.panoptic_deeplab` | Panoptic-DeepLab components | `add_panoptic_deeplab_config(cfg)` | Reuses DeepLab config keys and adds panoptic/instance-embedding settings. |

The packaging tests import `point_rend` and `deeplab` directly. `panoptic_deeplab` is part of the setup mapping but may depend on project-specific optional requirements in some environments; treat failures as an optional-project issue unless the user's task specifically requires it.

## Project Config Load Order

For project configs, call the adder before merging a YAML or setting project keys:

```python
from detectron2.config import get_cfg
from detectron2.projects.point_rend import add_pointrend_config

cfg = get_cfg()
add_pointrend_config(cfg)
cfg.merge_from_file("project_config.yaml")
```

Use the analogous order for DeepLab and Panoptic-DeepLab:

```python
from detectron2.projects.deeplab import add_deeplab_config
from detectron2.projects.panoptic_deeplab import add_panoptic_deeplab_config
```

If the import succeeds but the merge fails on an unknown key, the adder was likely skipped or called after the merge. If the registry lookup fails for a project head, the project module defining the head may not have been imported.

## PointRend

PointRend adds point-based mask and semantic segmentation refinement. It demonstrates:

- Custom ROI mask heads registered in `ROI_MASK_HEAD_REGISTRY`.
- A project-specific `POINT_HEAD_REGISTRY`.
- Semantic-segmentation heads registered in `SEM_SEG_HEADS_REGISTRY`.
- `add_pointrend_config(cfg)` for `MODEL.POINT_HEAD`, `MODEL.ROI_MASK_HEAD.POINT_HEAD_ON`, and related options.

Use PointRend as the main example when diagnosing a config load failure caused by missing project imports or missing config adders. It is installed as `detectron2.projects.point_rend` in the core package mapping.

## DeepLab

DeepLab adds semantic segmentation heads and ResNet variants for DeepLabV3/V3+. It demonstrates:

- Custom semantic heads registered in `SEM_SEG_HEADS_REGISTRY`.
- Project-specific backbone behavior registered through Detectron2 model registries.
- `add_deeplab_config(cfg)` for poly LR, semantic-head loss/projection/ASPP settings, and ResNet dilation/stem settings.

Use DeepLab as the reference for semantic-segmentation extensions that need both model registry changes and solver/config additions.

## Panoptic-DeepLab

Panoptic-DeepLab builds on DeepLab for bottom-up panoptic segmentation. It demonstrates:

- A custom meta-architecture registered in `META_ARCH_REGISTRY`.
- Semantic heads and instance-embedding branches.
- A project-specific `INS_EMBED_BRANCHES_REGISTRY`.
- `add_panoptic_deeplab_config(cfg)`, which first adds DeepLab config keys and then adds panoptic/instance-embedding keys.

Because it mixes semantic, panoptic, and instance-like outputs, route full data/evaluation/training questions to the owning sub-skills after using this sub-skill for extension wiring.

## Optional Research Projects

The repository also lists research projects such as DensePose, TridentNet, TensorMask, PointSup, Rethinking-BatchNorm, ViTDet, and MViTv2, plus external projects. Treat them as examples or optional stacks:

- Do not assume they are installed as importable `detectron2.projects.*` packages unless proven in the active environment.
- Do not assume the same stability, compatibility, or support level as core Detectron2 APIs.
- Expect extra dependencies, custom datasets, custom training scripts, or older config assumptions.
- Keep DensePose full tooling and data workflows out of core scope unless the user explicitly asks for DensePose and accepts its optional dependencies.

## Reference-Only Project Scripts

Project train/apply scripts are useful examples of wiring config adders, custom trainers, evaluators, and project imports. They should be treated as reference patterns rather than runtime dependencies of this skill. If a future task needs a project-specific runnable script, create a new bounded script in the user's workspace that imports the installed project package and calls its config adder instead of depending on the original checkout layout.
