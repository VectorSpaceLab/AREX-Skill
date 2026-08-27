---
name: runtime-configuration
description: "Install, inspect, and configure TotalSegmentator runtime
  dependencies, devices, weights, licenses, offline caches, and usage
  statistics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Runtime Configuration

Use this sub-skill when an agent needs to make TotalSegmentator importable, choose a backend device, inspect local runtime state, pre-stage model weights, configure offline/license behavior, or disable usage telemetry. It owns setup and diagnostics, not segmentation command construction.

## Start Here

- Install with `pip install TotalSegmentator`; verify with `TotalSegmentator --version`, `totalseg_info --json`, or the bundled checker.
- Run `python scripts/check_totalseg_runtime.py --task total --device cpu --json` for a safe smoke check that imports metadata/registry/config helpers, checks PyTorch visibility, and never downloads weights or runs models.
- Read [`references/install-and-backends.md`](references/install-and-backends.md) for Python/PyTorch requirements, optional dependencies, and `cpu`/`gpu`/`gpu:N`/`mps` selection.
- Read [`references/configuration.md`](references/configuration.md) for `TOTALSEG_HOME_DIR`, `TOTALSEG_WEIGHTS_PATH`, `config.json`, weights, offline staging, licenses, and usage-stat settings.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) when imports, CUDA/MPS, offline weights, licenses, preview rendering, optional dependencies, or config isolation fail.

## Routing Boundaries

- For task and class discovery, license flag lookup, or valid `--roi_subset` names, route to [`../capability-discovery/SKILL.md`](../capability-discovery/SKILL.md).
- For actual `TotalSegmentator -i ... -o ...` commands or `python_api.totalsegmentator(...)` calls, route to [`../segmentation-workflows/SKILL.md`](../segmentation-workflows/SKILL.md).
- For run reports, statistics, multilabel outputs, probabilities, or mask combination, route to [`../outputs-and-statistics/SKILL.md`](../outputs-and-statistics/SKILL.md).
- For DICOM input/output details and `crop_to_body`, route to [`../dicom-and-formats/SKILL.md`](../dicom-and-formats/SKILL.md).
- For phase, modality, body-stats, and Evans-index helper CLIs, route to [`../auxiliary-analysis/SKILL.md`](../auxiliary-analysis/SKILL.md).
- For training, dataset conversion, or research evaluation workflows, route to [`../advanced-training/SKILL.md`](../advanced-training/SKILL.md).

## Runtime Rules

- Prefer `totalseg_info` and `totalsegmentator.registry` for capability decisions; they are safe, fast, and do not load models.
- Do not log license numbers, absolute local paths, API keys, or machine-specific environment details in shared outputs.
- Treat model downloads as explicit side effects; only run `totalseg_download_weights` when the user expects network and storage use.
- Use the bundled checker for diagnostics before running expensive segmentation, especially in offline or service environments.
