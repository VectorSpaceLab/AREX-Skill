# Model troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: torch.utils.ffi` while importing MRCNN/Retina code | Historical custom NMS/RoIAlign wrappers use an API removed from modern torch | Read [cuda-extensions](../../cuda-extensions/SKILL.md); verify a matching historical environment or stop. Do not patch the import or call CPU helpers as equivalent proof. |
| Anchor count does not match classifier/regressor output | `dim`, pyramid levels, anchor ratios/scales, or Retina scale expansion disagree | Recompute per-level shapes/counts from the config and inspect the model's expected head dimensions. |
| Empty positive samples or unstable loss | Label map/box coordinates do not overlap anchors, or sampling thresholds are too strict | Validate ROI labels, coordinate order, IoU thresholds, and a tiny target case before changing learning settings. |
| Tensor rank/channel mismatch | 2D/3D config, `n_3D_context`, `n_channels`, and loader transpose disagree | Route to [data-and-preprocessing](../../data-and-preprocessing/SKILL.md), write down each axis, and check the first batch contract. |
| Out-of-memory in proposal or mask stage | Pre/post-NMS counts, ROI chunk size, patch size, or 3D volume is too large | Reduce one bounded memory driver after recording the original config; do not interpret OOM as an operator compatibility pass/fail. |
| Segmentation output has unexpected classes | `class_specific_seg_flag`, `num_seg_classes`, and `head_classes` are inconsistent | Align config and converter label mode; binary masks and instance maps require different loader flags. |
| 3D RoIAlign signature or coordinate failure | Historical 3D wrapper/class has API drift and needs z-depth/6-coordinate handling | Use the direct 3D contract in [cuda-extensions](../../cuda-extensions/references/custom-ops.md); treat the high-level class as unverified. |
| A source model name is accepted by config but module import fails | Dispatch key and `models/<name>` implementation differ in this revision | Inspect the selected config/model pair and record the exact revision; do not silently substitute another family. |

A model claim is accepted only when geometry, targets, and dependency/backend
preconditions are recorded. Portable utility evidence cannot clear an unresolved
legacy CUDA/custom-op boundary.
