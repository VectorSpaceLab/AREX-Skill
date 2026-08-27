# Detection model overview

All entries below are public classes exposed through
`PytorchWildlife.models.detection` in the inspected 1.3.0 distribution. The
model zoo's license labels are included for selection context; check the
model's own terms before redistribution.

## Camera-trap and general-purpose detectors

| Wrapper | Constructor version values | Classes / selection guidance |
|---|---|---|
| `MegaDetectorV5` | `a`, `b` | General camera-trap detector; animal, person, vehicle; AGPL-3.0 model variants. |
| `MegaDetectorV6` | `MDV6-yolov9-c`, `MDV6-yolov9-e`, `MDV6-yolov10-c`, `MDV6-yolov10-e`, `MDV6-rtdetr-c` | General camera-trap detector; Ultralytics-backed public variants; AGPL-3.0. The compact variants favor lower resource use; extra variants favor capacity. |
| `MegaDetectorV6MIT` | `MDV6-mit-yolov9-c`, `MDV6-mit-yolov9-e` | MIT-licensed YOLO V9 variants; separate implementation and dependencies. |
| `MegaDetectorV6Apache` | `MDV6-apa-rtdetr-c`, `MDV6-apa-rtdetr-e` | Apache-licensed RT-DETR variants; separate implementation and dependencies. |
| `DeepfauneDetector` | none | Third-party YOLO detector with a 960-pixel inference size; useful as a complementary detector, especially for European fauna. |

`MegaDetectorV6` rejects any other version with a `ValueError` listing the five
accepted values. The MIT and Apache wrappers independently validate their two
version values. Do not substitute a model-zoo display name for the exact
constructor string.

## Dense and overhead localization

| Wrapper | Constructor selection | Behavior |
|---|---|---|
| `HerdNet` | `version="general"` or `version="ennedi"` | Patch-based localization/counting with checkpoint-provided species/class names. It has detection and classification scores. Licensed CC BY-NC-SA-4.0 in the model-zoo table. |
| `OWLC` | `version="general"` or `version="caribou"` | Overhead Wildlife Locator CNN; single animal class (`class_id=1` in the wrapper). |
| `OWLT` | no version argument | Overhead Wildlife Locator Transformer; single animal class (`class_id=1` in the wrapper). |

The model-zoo names OWL-C as overhead CNN and OWL-T as overhead Transformer.
These wrappers resize small images to at least 512 pixels and use tiled/stitch
inference. Their ordinary batch API accepts a directory, but the implementation
processes only the first tensor/path of each loaded batch; use `batch_size=1`.

## Specialized public variant

`MegaDetectorV6_Distributed` is exposed by the package but is not a normal
single-image or folder-batch convenience wrapper. Its batch method requires an
already prepared loader plus `batch_size`, `global_rank`, `local_rank`,
`output_dir`, and optional `checkpoint_frequency`. It returns array-oriented
records and writes rank outputs. Route distributed production to a dedicated
pipeline rather than presenting it as the normal `MegaDetectorV6` API.

## Choosing among models

- Start with `MegaDetectorV6(version="MDV6-yolov10-c")` for a smaller general
  detector, or `MDV6-yolov10-e` when capacity is more important and resources
  permit. These are operational heuristics, not a substitute for validation
  on the user's imagery.
- Prefer `MegaDetectorV5` only when an existing workflow requires its checkpoint
  or legacy YOLO V5 behavior. Its import path is more sensitive to old YOLO V5
  dependencies.
- Use `HerdNet` for dense herds or when species/class outputs from its checkpoint
  are the intended result. Use `general` or `ennedi` to match the target domain.
- Use `OWLC`/`OWLT` for overhead imagery, with `OWLC(version="caribou")` only
  when the caribou checkpoint is appropriate. OWLT has no version selector.
- Use the MIT/Apache classes when their licensing or backend is required; do
  not pass their version strings to the standard `MegaDetectorV6` class.
- Use `DeepfauneDetector` only with awareness that its training domain and
  class behavior differ from MegaDetector; compare recall/false positives on
  the target region.

Performance figures in the public model-zoo table are model-zoo metrics, not
an execution guarantee. The detector's animal-first operating goal can trade
false positives for recall; route downstream class filtering to the
classification skill.
