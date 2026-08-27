---
name: ab3dmot
description: "Operate AB3DMOT 3D multi-object tracking workflows for KITTI and
  nuScenes data, tracking, evaluation, and visualization."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# AB3DMOT repo skill

Use this skill when a task involves AB3DMOT, 3D multi-object tracking, KITTI/nuScenes tracking inputs, the AB3DMOT tracker API, AB3DMOT result evaluation, confidence thresholding, or qualitative visualization.

AB3DMOT is a CPU-oriented Python baseline that combines 3D object detections, a 3D Kalman filter, ego-motion compensation, and Hungarian/greedy data association. It is organized as a repository script workflow rather than an installed console-entry-point package.

## Start here

1. If the task is about installation, imports, dependencies, or runtime smoke checks, read [references/install-and-dependencies.md](references/install-and-dependencies.md) and run [scripts/ab3dmot_environment_check.py](scripts/ab3dmot_environment_check.py).
2. If the task is about repository layout, public source areas, configs, result roots, or which bundled sub-skill owns a file family, read [references/repository-map.md](references/repository-map.md).
3. If the task fails before you know the owning workflow, read [references/troubleshooting.md](references/troubleshooting.md).
4. For provenance and staleness checks, read [references/repo-provenance.md](references/repo-provenance.md).

## Route by workflow

- Use [sub-skills/data-conversion/SKILL.md](sub-skills/data-conversion/SKILL.md) for KITTI/nuScenes data placement, detector-result conversion, AB3DMOT detection row validation, category-specific detection folders, and nuScenes-to-KITTI intermediate layouts.
- Use [sub-skills/tracking-pipeline/SKILL.md](sub-skills/tracking-pipeline/SKILL.md) for `main.py` tracking commands, config defaults, output naming, direct `AB3DMOT.track` API use, Box3D/matching/Kalman behavior, and one-frame smoke checks.
- Use [sub-skills/evaluation-visualization/SKILL.md](sub-skills/evaluation-visualization/SKILL.md) for KITTI 2D/3D MOT metrics, nuScenes official/quick evaluation, confidence thresholding, result export/submission packaging, and image/video visualization.

## Common task routing

| User asks for | Read |
| --- | --- |
| “Validate this AB3DMOT detection file” | `data-conversion` validator and data formats |
| “Convert nuScenes detections for AB3DMOT” | `data-conversion` nuScenes conversion reference |
| “Run KITTI PointRCNN tracking” | `tracking-pipeline` tracking workflow |
| “Use AB3DMOT.track directly” | `tracking-pipeline` API reference and synthetic smoke script |
| “Why did `main.py` use nuScenes defaults?” | `tracking-pipeline` configuration/troubleshooting |
| “Evaluate KITTI validation with 0.25/0.5/0.7 3D IoU” | `evaluation-visualization` KITTI evaluation |
| “Make KITTI 2D MOT submission files” | `evaluation-visualization` KITTI threshold/submission guidance |
| “Convert AB3DMOT nuScenes results to JSON and evaluate” | `evaluation-visualization` nuScenes evaluation |
| “Render track videos” | `evaluation-visualization` visualization troubleshooting |

## Minimal runtime expectations

AB3DMOT command workflows assume a working AB3DMOT checkout or equivalent
project tree with:

- Python runtime compatible with the repository and dependencies.
- NumPy and SciPy in addition to FilterPy, Numba, Matplotlib, Pillow, OpenCV, PyYAML, EasyDict, and the other `requirements.txt` entries.
- The external Xinshuo Python toolbox (`Xinshuo_PyToolbox`) importable via `--toolbox-root` or `PYTHONPATH`; it is not bundled or reliably pin-able as a PyPI dependency.
- Full external KITTI or nuScenes tracking data when running dataset-level tracking or metrics; detection text files alone are not sufficient for `main.py`.
- Optional nuScenes dependencies when running nuScenes conversion or official evaluation.

Safe first check from this generated skill directory, pointing it at an AB3DMOT checkout:

```bash
python scripts/ab3dmot_environment_check.py --repo-root /path/to/AB3DMOT --smoke-track
```

If the Xinshuo toolbox is not already importable, also pass `--toolbox-root <path-to-Xinshuo_PyToolbox>`.

## Important constraints

- AB3DMOT is not a detector; it consumes already-generated 3D detections.
- The README quick KITTI demo command is explicit, but `main.py` parser defaults point at nuScenes. Always pass `--dataset`, `--split`, and `--det_name` deliberately.
- KITTI `val` maps to the external KITTI `training` tree and a validation sequence list. KITTI `test` maps to the external `testing` tree.
- nuScenes tracking uses the repo's KITTI-like `data/nuScenes/nuKITTI/` intermediate tree.
- Local test-set labels are unavailable for KITTI and nuScenes; official test metrics require external benchmark servers.

## Verification status for this generated skill

This skill's lightweight repair checks cover Python syntax and CLI help only;
the synthetic tracker smoke remains dependent on an external AB3DMOT checkout,
NumPy/SciPy and the Xinshuo toolbox. Full benchmark-scale tracking/evaluation
requires external datasets and is intentionally not run here.
