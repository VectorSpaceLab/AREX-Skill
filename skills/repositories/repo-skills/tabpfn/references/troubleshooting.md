# Cross-Cutting Troubleshooting

This file collects failures that cut across multiple workflows. For details that
belong to a single sub-skill, follow the route map in the root skill.

## Common failures

| Symptom | Likely cause | Route |
| --- | --- | --- |
| `TabPFNValidationError` about shape, samples, features, labels, or classes | Input shape or label mismatch | `preprocessing-config` or `tabular-prediction` |
| CPU runtime error about large datasets | CPU sample guard triggered | `preprocessing-config` |
| `TabPFNLicenseError` or gated repo access error | Browser/token access not configured | `model-management` |
| OOM or chunking confusion on cached inference | Cache or batch-size settings too aggressive | `batched-performance` |
| `float64` rejection in batched inference | Fused batched path only supports lower precision | `batched-performance` |
| Fine-tuning/early-stopping warnings | Validation split or patience configuration | `tuning-and-advanced` |
| Save/load or checkpoint format errors | Persistence helper or file-format mismatch | `model-management` |

## Good first checks

1. Confirm the package version and settings with the root environment script.
2. Check whether the task should really be routed to a narrower sub-skill.
3. If the task is about a local checkpoint, confirm that the path exists and has
   the expected extension.
4. If the task is about first-use access, confirm that a token or browser flow
   is available.

## What not to do

- Do not assume CPU import success means GPU behavior is verified.
- Do not use batched inference on ragged shapes.
- Do not treat a missing token or browser as a silent no-op.
- Do not fit large datasets on CPU unless the user explicitly accepts that path.
