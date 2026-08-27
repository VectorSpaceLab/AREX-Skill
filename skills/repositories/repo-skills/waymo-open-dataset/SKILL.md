---
name: waymo-open-dataset
description: "Guides Waymo Open Dataset package workflows for autonomous-driving
  data schemas, perception and motion utilities, metrics, challenge submissions,
  and repository build/test tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Waymo Open Dataset Repo Skill

Use this repo skill when a task involves the Waymo Open Dataset Python package or repository: autonomous-driving Perception/Motion/End-to-End Driving data formats, `waymo_open_dataset` protos and utilities, V2 columnar components, TensorFlow metric wrappers, WOD challenge submissions, or maintaining the Bazel/PyPI build.

Before relying on this skill for a checkout or installed package, read [references/repo-provenance.md](references/repo-provenance.md) to compare the source commit, package version, and evidence paths. For package setup, read [references/installation-and-environment.md](references/installation-and-environment.md), then run [`scripts/check_wod_environment.py`](scripts/check_wod_environment.py) against the active Python environment.

## Install and import baseline

For normal package use, prefer a published WOD wheel that matches the TensorFlow line you need. This skill was verified against:

```bash
python -m pip install -f https://storage.googleapis.com/jax-releases/jax_releases.html \
  waymo-open-dataset-tf-2-12-0==1.6.7
python - <<'PY'
from importlib.metadata import version
from waymo_open_dataset import v2
print(version('waymo-open-dataset-tf-2-12-0'))
print(v2.ALL_TAGS[:3])
PY
```

If dependency resolution fails on `jaxlib==0.4.13`, use Python 3.10 and the official JAX release links shown above. GPU challenge timing and Deeplab2 camera-segmentation paths are optional; do not treat a CPU import as proof of those optional paths.

## Route map

- Use [sub-skills/v2-components/SKILL.md](sub-skills/v2-components/SKILL.md) for V2 columnar data, component dataclasses, Parquet component tags, Pandas/Dask joins, and object-asset component structures.
- Use [sub-skills/dataset-utils/SKILL.md](sub-skills/dataset-utils/SKILL.md) for v1 `Frame` protos, compressed range images, point clouds, camera projections, maps, geometry, boxes, and keypoint helper data.
- Use [sub-skills/metrics-evaluation/SKILL.md](sub-skills/metrics-evaluation/SKILL.md) for detection/tracking/motion/keypoint/segmentation metrics, TensorFlow metric ops, metric configs, and accuracy submission artifacts.
- Use [sub-skills/motion-sim-agents/SKILL.md](sub-skills/motion-sim-agents/SKILL.md) for WOMD motion scenarios, occupancy-flow metrics, sim-agents/scenario-generation submissions, and WOMD camera/LiDAR feature merging.
- Use [sub-skills/latency-submissions/SKILL.md](sub-skills/latency-submissions/SKILL.md) for real-time 2D/3D detection latency modules, pre-extracted numpy inputs, output shape validation, and Docker image source guidance.
- Use [sub-skills/camera-and-segmentation/SKILL.md](sub-skills/camera-and-segmentation/SKILL.md) for camera custom ops, camera-only detection, PVPS, 3D semantic segmentation, camera segmentation metrics, and E2E driving data/submission outlines.
- Use [sub-skills/repo-build-test/SKILL.md](sub-skills/repo-build-test/SKILL.md) for Bazel, Docker/Jupyter, wheel packaging, requirements updates, focused native tests, and contributor diagnostics.

## Shared references

- [references/package-map.md](references/package-map.md) summarizes distribution names, import modules, major source-derived capability families, and optional dependency boundaries.
- [references/installation-and-environment.md](references/installation-and-environment.md) explains CPU/GPU package selection, Python/JAX compatibility, notebook/Docker setup, and smoke checks.
- [references/troubleshooting.md](references/troubleshooting.md) covers cross-cutting install/import, TensorFlow/custom-op, dataset access, optional dependency, and routing failures.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) is structured metadata for managed `repo-skills-router` import.

## Operating rules for future agents

1. Distinguish WOD dataset access from the Python package. The package provides schemas, utilities, metrics, and challenge helpers; full datasets require Waymo access/terms and are not bundled here.
2. Prefer installed-package facts for signatures and imports; use the sub-skill references for source-derived workflows such as latency, which is source-only in the public wheel.
3. Do not claim GPU or Deeplab2 verification unless you have run a fresh backend-specific check. The verified baseline for this skill is CPU package inspection plus optional-path warnings.
4. For generated scripts in this skill, run them from any working directory and pass ordinary package-installed Python; they do not require the original repository checkout.
