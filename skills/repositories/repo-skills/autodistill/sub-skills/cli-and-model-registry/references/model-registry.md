# Model Registry and Plugin Selection

Read this when choosing `--base`, `--target`, or plugin packages for Autodistill. The core package does not include the concrete foundation or target models; it keeps a registry of aliases and imports separate plugin modules.

## Registry Behavior

The source registry contains entries like:

```python
("grounded_sam", "GroundedSAM")
("grounding_dino", "GroundingDINO")
("yolov8", "YOLOv8", "yolov8n.pt")
```

`import_requisite_module(module_name, noninteractive_install=False)`:

1. checks that `module_name` is in the registry;
2. checks whether `importlib.import_module("autodistill_" + module_name)` succeeds;
3. if missing, asks the user or, with noninteractive install, runs `pip install autodistill_<module_name>`;
4. imports the plugin module;
5. returns the configured class, passing a default checkpoint argument when the registry tuple has a third element.

Do not call `import_requisite_module` as a harmless inspection helper; it may install packages or prompt. Use the bundled `inspect_model_registry.py` script for read-only inspection.

## Aliases in This Snapshot

```text
grounded_sam, grounding_dino, yolov8, yolov5, fastsam, owl-vit, albef,
detic, blipv2, sam-clip, dinov2, yolonas, blip, vit, detr, llava,
kosmos-2, fastvit, metaclip, owlv2, azure-vision, rekognition,
gcp-vision, roboflow-universe, codet, altclip, vlpart
```

Several aliases contain hyphens, but `importlib.import_module("autodistill_" + module_name)` uses the alias literally. Confirm the concrete plugin import name before relying on automatic install/import for hyphenated aliases.

## Default Target Checkpoints

The registry constructs these target models with default checkpoint names:

| Alias | Class | Default constructor argument |
|---|---|---|
| `yolov8` | `YOLOv8` | `yolov8n.pt` |
| `yolov5` | `YOLOv5` | `yolov5n.pt` |

Other registry entries return the class object without a default argument.

## Model Matrix Tasks

The package model matrix groups plugins by:

- object detection base models;
- object detection target models;
- instance segmentation base and target models;
- classification base and target models.

Model support status can be complete, in progress, or not started. Treat the matrix as selection guidance, not as proof that a plugin is installed or verified in the current environment.

## Roboflow Upload-Supported Target Values

The CLI source allows deployment upload only for:

```text
yolov5, yolov5-seg, yolov8, yolov8-seg
```

For other target models, keep upload disabled or use that target plugin's own deployment guidance.

## Package Naming Caution

Documentation commonly names distributions with hyphens, for example `autodistill-grounding-dino` and `autodistill-yolov8`. The core registry's noninteractive install path constructs underscore names such as `autodistill_grounding_dino`. Pip normalizes some package spellings, but not every alias maps cleanly. Prefer explicit, documented `pip install autodistill-...` commands after selecting the plugin.

## Selection Checklist

- Does the base model task match the target model task (detection, segmentation, classification)?
- Does the plugin need GPU, large model weights, API credentials, or special framework wheels?
- Does the plugin license fit the intended use?
- Can a small single-image prediction run before labeling a folder or training?
- Is the target model upload-supported if Roboflow deployment is requested?
