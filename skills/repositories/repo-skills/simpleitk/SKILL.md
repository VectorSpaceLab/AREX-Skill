---
name: simpleitk
description: "Use SimpleITK for medical-image IO, image metadata, NumPy
  conversion, filtering, segmentation, registration, transforms, and
  source-build troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SimpleITK Repo Skill

Use this repo skill when a task names SimpleITK, `simpleitk`, `import SimpleITK as sitk`, medical-image IO, DICOM series, image spacing/origin/direction, NumPy image conversion, SimpleITK filters, segmentation, registration, transforms, resampling, or SimpleITK source builds and wrapping.

## Start Here

- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a SimpleITK checkout or whether `refresh-repo-skill` is needed.
- Read [references/source-evidence-map.md](references/source-evidence-map.md) to see which source, docs, examples, tests, scripts, and existing skills informed this self-contained skill.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import/version, optional feature, ImageIO, and workflow routing failures.
- Run [scripts/check_simpleitk_env.py](scripts/check_simpleitk_env.py) to inspect a local `SimpleITK` install, NumPy bridge, ImageIO discovery, registration availability, and optional elastix wrappers without needing source data.

## Installation and Import

For ordinary Python usage, prefer a binary install before attempting source builds:

```bash
python -m pip install --upgrade pip
python -m pip install simpleitk
python - <<'PY'
import SimpleITK as sitk
print(sitk.Version())
PY
```

Use conda-forge consistently when the project is conda-based:

```bash
conda create --name sitk python=3.11 simpleitk --channel conda-forge --override-channels
conda activate sitk
```

Import the Python package with `import SimpleITK as sitk`; the distribution name is `simpleitk`.

## Route by Task

| User task | Read this sub-skill |
| --- | --- |
| Construct `sitk.Image`, preserve spacing/origin/direction, inspect pixel IDs, convert to or from NumPy, debug shape reversal | [image-core](sub-skills/image-core/SKILL.md) |
| Read/write MHA, NRRD, NIfTI, PNG, DICOM series, metadata tags, transforms, or ImageIO backends | [io-and-data](sub-skills/io-and-data/SKILL.md) |
| Apply filters, smooth/threshold images, run morphology, connected components, segmentation, N4, or label statistics | [filtering-segmentation](sub-skills/filtering-segmentation/SKILL.md) |
| Configure transforms, resampling, registration metrics/optimizers, callbacks, reproducibility, or optional elastix/transformix workflows | [registration-transforms](sub-skills/registration-transforms/SKILL.md) |
| Install/build SimpleITK, choose PyPI vs conda vs source/SuperBuild, inspect CMake `WRAP_*`, enable optional wrappers, or run maintainer checks | [builds-and-wrapping](sub-skills/builds-and-wrapping/SKILL.md) |

## Core Rules

- Treat a SimpleITK image as a physical object: preserve `GetOrigin()`, `GetSpacing()`, and `GetDirection()` when replacing pixels or moving through NumPy.
- Remember axis order: SimpleITK indexes are `(x, y, z, ...)`; NumPy arrays from SimpleITK are reversed spatially, such as `(z, y, x)` for a 3D scalar image.
- Use `sitk.ImageFileReader().GetRegisteredImageIOs()` and `sitk.ImageFileWriter().GetRegisteredImageIOs()` for registered ImageIO discovery in Python examples.
- Use `.mha` or `.nrrd` for deterministic smoke tests; avoid lossy formats such as JPEG when pixel equality matters.
- Cast registration inputs deliberately to `sitk.sitkFloat32` or `sitk.sitkFloat64` when a metric or optimizer requires floating-point images.
- For label images, use nearest-neighbor interpolation during resampling; use linear interpolation for intensities unless a workflow says otherwise.
- Treat `ElastixImageFilter` and `TransformixImageFilter` as optional build-dependent APIs; absence in a binary install is an installation/build feature issue, not necessarily a typo.

## Source Build Guardrails

Do not start a source build for ordinary SimpleITK API usage. Source builds use native C++/CMake/SWIG tooling and can fetch/build ITK or other dependencies. Route source-build, SuperBuild, wrapping, and optional elastix requests to [builds-and-wrapping](sub-skills/builds-and-wrapping/SKILL.md), and ask before running expensive or mutating commands.

## Self-Containment

This skill distills repository docs, examples, tests, source code, and an installed-package inspection into bundled references and scripts. Runtime instructions here do not require access to the original SimpleITK checkout.
