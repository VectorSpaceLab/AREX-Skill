---
name: auxiliary-analysis
description: "Use TotalSegmentator auxiliary analysis CLIs for contrast phase,
  CT/MR modality, body statistics, and Evans index."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Auxiliary Analysis

Use this sub-skill when the task is not to run a general segmentation, but to run one of TotalSegmentator's secondary analysis commands: contrast phase prediction, CT/MR modality prediction, body-stat prediction, or Evans index calculation.

TotalSegmentator and these helper outputs are research/workflow aids, not standalone clinical decision systems. Preserve input provenance, inspect generated JSON/PNG outputs, and route license, install, and backend setup questions to the appropriate sibling skill.

## Start Here

- Build a safe command without running models: `python scripts/build_auxiliary_command.py <phase|modality|body-stats|evans-index> ...`.
- Read [`references/auxiliary-tools.md`](references/auxiliary-tools.md) for command flags, output schemas, dependency notes, and reuse limits.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for optional dependency, license, classifier resource, output path, and expensive-rerun fixes.
- Use `totalseg_get_phase` for CT contrast phase JSON with `pi_time`, phase label, confidence probability, min/max, and ensemble `stddev`.
- Use `totalseg_get_modality` for CT/MR classification JSON; add `-n` only when intensities are normalized and ROI-based prediction is needed.
- Use `totalseg_get_body_stats` for weight, size, age, sex, BMI, and BSA JSON from CT/MR images; default CNN inference is usually preferred over XGBoost.
- Use `totalseg_evans_index` for Evans index JSON plus a required preview PNG for visual validation.

## Route Elsewhere

- For selectable task/class discovery, registry APIs, or license-required task inventory, use [`../capability-discovery/SKILL.md`](../capability-discovery/SKILL.md).
- For ordinary `TotalSegmentator -i ... -o ...` segmentation runs and `python_api.totalsegmentator(...)`, use [`../segmentation-workflows/SKILL.md`](../segmentation-workflows/SKILL.md).
- For run reports, `statistics.json`, multilabel masks, probabilities, and mask combination, use [`../outputs-and-statistics/SKILL.md`](../outputs-and-statistics/SKILL.md).
- For installation, model weights, offline caches, license setup, device/backend setup, and usage-stat configuration, use `../runtime-configuration/SKILL.md` when present in this generated skill.
- For DICOM input layout, NIfTI/DICOM conversion, DICOM outputs, and `crop_to_body`, use `../dicom-and-formats/SKILL.md` when present in this generated skill.

## Safe Operating Rules

- Prefer the bundled command builder for automation because it prints shell-quoted commands and dependency cautions without importing TotalSegmentator or running inference.
- Always write JSON outputs to explicit paths; for Evans index, always request and inspect the preview PNG before trusting the numeric result.
- Treat optional dependencies as workflow-specific: XGBoost for phase/modality/XGBoost body stats, PyTorch+timm+MONAI for body-stats CNN, and antspyx+blosc for Evans index registration/serialization.
- Do not rerun expensive segmentation blindly. Reuse documented existing statistics for contrast phase when available; body-stats CLI does not expose a safe existing-statistics flag.
- Keep general segmentation planning and task/ROI selection out of this sub-skill unless the auxiliary tool itself invokes segmentation internally.
