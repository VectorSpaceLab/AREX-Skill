---
name: totalsegmentator
description: "Use TotalSegmentator as an installed package for medical-image
  segmentation, task discovery, runtime configuration, output parsing, DICOM
  handling, auxiliary analysis, and advanced training boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TotalSegmentator

Use this skill when a user asks about TotalSegmentator, the `TotalSegmentator` CLI, the `totalsegmentator` Python package, anatomical CT/MR segmentation tasks, model-weight or license setup, segmentation output parsing, DICOM/NIfTI handling, or TotalSegmentator-style nnU-Net retraining.

TotalSegmentator outputs are research/workflow artifacts unless the surrounding product has its own approved clinical validation. Preserve input provenance, verify task/class choices, and prefer machine-readable JSON outputs over scraping stdout.

## Quick Start

1. Discover capabilities first when task or class names are uncertain: `totalseg_info --json` or [capability-discovery](sub-skills/capability-discovery/SKILL.md).
2. Build segmentation commands through [segmentation-workflows](sub-skills/segmentation-workflows/SKILL.md); add `--report <path.json>` for automation.
3. Parse `run_report.json`, `statistics.json`, multilabel outputs, probabilities, and combined masks through [outputs-and-statistics](sub-skills/outputs-and-statistics/SKILL.md).
4. Use [runtime-configuration](sub-skills/runtime-configuration/SKILL.md) for install/import checks, CPU/GPU/MPS decisions, model weights, offline setup, licenses, and usage-stat settings.
5. Use [dicom-and-formats](sub-skills/dicom-and-formats/SKILL.md) before long runs when inputs are DICOM folders/zips, DICOM output is requested, or crop-to-body preprocessing is needed.

## Route by User Intent

| User intent | Read this |
| --- | --- |
| List tasks, classes, modalities, license flags, or valid `--roi_subset` names | [capability-discovery](sub-skills/capability-discovery/SKILL.md) |
| Build or run a CT/MR segmentation CLI/API workflow | [segmentation-workflows](sub-skills/segmentation-workflows/SKILL.md) |
| Validate reports, statistics, masks, multilabel headers, probabilities, or combined masks | [outputs-and-statistics](sub-skills/outputs-and-statistics/SKILL.md) |
| Fix install/import/backend issues, choose devices, pre-stage weights, configure offline or licensed tasks | [runtime-configuration](sub-skills/runtime-configuration/SKILL.md) |
| Validate NIfTI/DICOM inputs, DICOM SEG/RTSTRUCT outputs, modality detection, or crop-to-body preprocessing | [dicom-and-formats](sub-skills/dicom-and-formats/SKILL.md) |
| Use contrast phase, CT/MR modality, body stats, or Evans index helper CLIs | [auxiliary-analysis](sub-skills/auxiliary-analysis/SKILL.md) |
| Plan retraining, dataset conversion, benchmark evaluation, or model-contribution work | [advanced-training](sub-skills/advanced-training/SKILL.md) |

## Safe Install and Smoke Check

Install the public package in the user's chosen environment:

```bash
pip install TotalSegmentator
```

Then run safe checks that do not download model weights:

```bash
totalseg_info --json
python scripts/check_install.py --task total --class-name liver --json
```

The root helper verifies package metadata, importability, registry access, selected task/class names, and console-script availability. It does not run segmentation, validate licenses against the network, or download weights.

## Common Workflows

- **Automation pipeline:** discover task/classes with `totalseg_info --json`, build a `TotalSegmentator` command with `--report` and optional `--statistics`, then parse JSON files through the outputs sub-skill.
- **CPU-only run:** choose `--device cpu`, add `--fast` or a small `--roi_subset`, and use the segmentation troubleshooting reference for memory/runtime limits.
- **Offline deployment:** use runtime configuration to set a writable TotalSegmentator home, pre-stage weights, save any required license, and run read-only diagnostics before inference.
- **DICOM output:** validate the input as DICOM first, install the needed optional DICOM output dependency, and avoid requesting DICOM output from NIfTI input.
- **Advanced research:** use the training sub-skill only for explicit retraining/evaluation/contribution requests; ordinary segmentation should stay in the segmentation workflow.

## Runtime References

- Read [references/task-selection.md](references/task-selection.md) for task, class, modality, and license selection patterns.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install, data, CLI/API, optional dependency, model-weight, and license failures.
- Read [references/repo-provenance.md](references/repo-provenance.md) to decide whether this skill is aligned with the source version.
- `references/repo-routing-metadata.json` contains structured metadata for managed router import.

## Boundaries

- Do not hard-code task/class lists from memory; use `totalseg_info` or `totalsegmentator.registry`.
- Do not run heavyweight segmentation, model downloads, licensed tasks, or training by default when the user only needs planning or validation.
- Do not expose license numbers, local cache paths, or environment paths in shared reports.
- Do not treat skipped native examples or heavyweight tests as passing; record why they are skipped and use safe JSON/helper checks where possible.
