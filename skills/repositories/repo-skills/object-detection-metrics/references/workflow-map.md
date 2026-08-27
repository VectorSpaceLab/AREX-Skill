# Workflow map

This reference maps Object-Detection-Metrics capabilities to the generated skill tree and names deliberate non-goals.

## Capability ownership

| Capability | Kind | Owner | Runtime files | Verification path |
|---|---|---|---|---|
| PASCAL VOC AP/mAP from text folders | Primary workflow | `sub-skills/file-evaluation` | `SKILL.md`, `references/workflows.md`, `scripts/voc_metrics_eval.py` | Native fixture commands and synthetic text-folder cases. |
| Ground-truth/detection file schemas | Support workflow | `sub-skills/file-evaluation` | `references/file-format.md` | Invalid-line and mixed-format synthetic cases. |
| Absolute `xywh` and `xyrb` coordinate selection | Support workflow | `sub-skills/file-evaluation` | `references/file-format.md`, `references/troubleshooting.md` | Mixed-format tiny fixture. |
| YOLO-like relative center/size coordinates | Support workflow | `sub-skills/file-evaluation` for folder-level shared size; `sub-skills/python-api` for custom per-image handling | `file-evaluation/references/file-format.md`, `python-api/references/api-reference.md` | Relative-detection fixture and missing-image-size failure case. |
| Direct `BoundingBox` / `BoundingBoxes` construction | Primary workflow | `sub-skills/python-api` | `references/api-reference.md`, `scripts/api_metric_smoke.py` | API smoke with perfect and duplicate cases. |
| `Evaluator.GetPascalVOCMetrics` and return dictionary interpretation | Primary workflow | `sub-skills/python-api` | `references/api-reference.md`, `references/metric-behavior.md` | API smoke and synthetic AP method cases. |
| Every-point vs 11-point AP method choice | Support workflow | `sub-skills/python-api` | `references/metric-behavior.md`, `scripts/api_metric_smoke.py` | AP-method enum smoke. |
| IoU inclusive-area behavior and duplicate detections | Support workflow | `sub-skills/python-api`, mirrored in `file-evaluation` | `python-api/references/metric-behavior.md`, `file-evaluation/references/troubleshooting.md` | Duplicate-detection case. |
| OpenCV drawing and matplotlib plotting caveats | Minor/support workflow | `sub-skills/python-api` | `references/api-reference.md`, `references/troubleshooting.md` | Documented only; not executed because GUI/image-write behavior is optional. |
| Environment/import diagnostics | Support workflow | Root and `sub-skills/python-api` | `scripts/check_env.py`, `python-api/scripts/api_metric_smoke.py`, root `references/troubleshooting.md` | Help and source-import smoke checks. |

## Explicit non-goals

- COCO metrics and richer file formats from the successor repository.
- Video/STT-AP workflows.
- Training, inference, model export, or detector architecture guidance.
- Paper survey reproduction.
- Repository contribution, release, CI, or maintainer workflows.

## Bundled replacements for source artifacts

| Source repo artifact | Runtime need | Bundled replacement | Link owner |
|---|---|---|---|
| `pascalvoc.py` | Noninteractive file-folder VOC AP/mAP evaluation | `sub-skills/file-evaluation/scripts/voc_metrics_eval.py` | `sub-skills/file-evaluation/SKILL.md` |
| `samples/sample_2/sample_2.py` | Direct API metric smoke without plotting | `sub-skills/python-api/scripts/api_metric_smoke.py` | `sub-skills/python-api/SKILL.md` |
| `samples/sample_1/sample_1.py` | Manual `BoundingBox` construction and drawing concepts | Distilled into `sub-skills/python-api/references/api-reference.md` | `sub-skills/python-api/SKILL.md` |
| `_init_paths.py` | Source-style import path behavior | Distilled into root and `python-api` troubleshooting; no runtime wrapper needed | root and `python-api` references |

The generated skill never requires future agents to execute upstream scripts or examples. Original paths are evidence anchors only.
