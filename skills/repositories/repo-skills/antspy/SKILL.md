---
name: antspy
description: "Use ANTsPy/antspyx for medical image IO, ANTsImage metadata, image
  operations, registration, segmentation, visualization, and learning helper
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ANTsPy Repo Skill

Use this repo skill when a task involves the Python package distributed as `antspyx` and imported as `ants`: medical image IO, `ANTsImage` objects, preprocessing, registration, transforms, segmentation, labels, plotting, interoperability, or ANTsPy learning/deeplearn helper utilities.

## Start Here

1. Install the package with `pip install antspyx` or `conda install conda-forge::antspyx`.
2. Verify the public import with `python -c "import ants; print(ants.__name__)"`.
3. Run [scripts/antspy_environment_check.py](scripts/antspy_environment_check.py) for a tiny import/API smoke check.
4. Read [references/package-overview.md](references/package-overview.md) for package scope, compiled-backend caveats, and workflow boundaries.
5. Read [references/troubleshooting.md](references/troubleshooting.md) when installation, import, compiled libraries, physical-space metadata, optional dependencies, or expensive algorithms fail.
6. Check [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is stale for a newer ANTsPy checkout.

## Route by Task

| User task | Read |
| --- | --- |
| Create, read, write, clone, index, compare, or validate `ants.ANTsImage` objects and physical metadata | [image-core](sub-skills/image-core/SKILL.md) |
| Smooth, denoise, mask, crop, pad, slice, resample, threshold, run `iMath`, compute image metrics, or use morphology | [image-ops-math](sub-skills/image-ops-math/SKILL.md) |
| Register images, apply transforms to images or points, inspect transform files, build templates, run motion correction, or compute Jacobians | [registration-transforms](sub-skills/registration-transforms/SKILL.md) |
| Run Atropos, k-means, Otsu, priors, joint label fusion, label stats, overlap, geometry, label matrices, centroids, or point images | [segmentation-labels](sub-skills/segmentation-labels/SKILL.md) |
| Save plots headlessly, build overlays/grids/movies, handle RGB/vector channels, convert image lists/matrices, or interoperate with nibabel/SimpleITK | [visualization-interop](sub-skills/visualization-interop/SKILL.md) |
| Use sparse/eigen learning helpers, patch extraction/reconstruction, one-hot labels, random augmentation, simulated bias fields, or learning-oriented crop/pad helpers | [learning-deeplearn](sub-skills/learning-deeplearn/SKILL.md) |

## Cross-Cutting Rules

- Import with `import ants`; do not import `antspyx` as a module.
- ANTsPy wraps compiled ANTs/ITK code. A successful `pip install` is not enough if importing `ants` fails; run the environment check script before debugging workflow code.
- `ANTsImage` values and physical metadata are both important. Validate `shape`, `dimension`, `origin`, `spacing`, and `direction` before mixing images, masks, labels, transforms, overlays, or matrices.
- Use label-safe interpolation such as `nearestNeighbor` or `genericLabel` for labels and masks. Use linear-style interpolation for intensity images unless the workflow requires otherwise.
- Prefer small synthetic images for smoke checks and troubleshooting. Full nonlinear registration, joint label fusion, high-resolution 3-D operations, and template building can be expensive.
- Keep ANTsPyNet, neural-network model training, and application-specific medical pipelines outside this skill unless the task only uses ANTsPy helper utilities.

## Shared References and Scripts

- [Package overview](references/package-overview.md): package identity, public workflow map, data model, optional dependencies, and version caveats.
- [API index](references/api-index.md): quick map from common `ants.*` functions to the owning sub-skill and detailed reference.
- [Troubleshooting](references/troubleshooting.md): install/import failures, wheel/source-build problems, shadowed imports, physical-space errors, optional dependencies, and expensive workflow triage.
- [Repo provenance](references/repo-provenance.md): source commit, dirty-state baseline, package versions, and evidence paths used for this generated skill.
- [Routing metadata](references/repo-routing-metadata.json): structured scenario metadata consumed by the managed `repo-skills-router` during import.
- [Environment check](scripts/antspy_environment_check.py): tiny import/API smoke check for `antspyx`.
- [Smoke suite](scripts/run_antspy_smoke_suite.py): runs the bundled sub-skill smoke scripts with the current Python interpreter.
