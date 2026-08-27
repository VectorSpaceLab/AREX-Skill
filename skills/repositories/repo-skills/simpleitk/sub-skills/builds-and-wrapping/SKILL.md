---
name: builds-and-wrapping
description: "Install SimpleITK binaries, choose source or SuperBuild builds,
  inspect CMake wrapping options, and run safe contributor checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SimpleITK Builds and Wrapping

Use this sub-skill when a task mentions installing SimpleITK, building from source, configuring the SuperBuild, choosing CMake or `WRAP_*` options, packaging Python wheels, enabling optional elastix/transformix wrappers, or running maintainer-oriented checks.

## Start Here

- Read [references/install-build.md](references/install-build.md) to choose PyPI, conda-forge, pre-release wheels, `pip install .`, direct CMake, or SuperBuild.
- Read [references/cmake-wrapping.md](references/cmake-wrapping.md) for CMake options, `WRAP_*` language flags, Python packaging, Python limited API, SWIG-generated wrappers, and `SimpleITK_USE_ELASTIX`.
- Read [references/maintainer-checks.md](references/maintainer-checks.md) for safe docs, tests, pre-commit, and metadata checks, plus release-heavy exclusions.
- Read [references/troubleshooting.md](references/troubleshooting.md) when a wheel is not selected, conda environments mix channels, CMake/SWIG/compiler detection fails, language dependencies are missing, or elastix classes are absent.
- Run [scripts/check_build_metadata.py](scripts/check_build_metadata.py) from a SimpleITK source checkout, or pass a checkout path, to print read-only JSON about build metadata files and key flags.

## Decision Rules

- Prefer a binary install unless the user needs development-branch code, an unsupported language/platform binary, C++ integration, custom ITK modules, optional elastix wrappers, or maintainer work.
- Prefer `pip install simpleitk` for ordinary Python use; import with `import SimpleITK as sitk`, even though the distribution name is `simpleitk`.
- Prefer conda-forge in isolated conda environments; avoid mixing `defaults` with `conda-forge` for SimpleITK dependencies.
- Prefer SuperBuild for full source builds because it pins/fetches matching ITK, SWIG, GTest, and build support; use direct CMake only when supplying dependencies yourself.
- Treat `pip install .` from the source tree as a Python source build: it uses `scikit-build-core`, CMake, SWIG, and native compilation, so it can be slow and platform-sensitive.
- Treat `ElastixImageFilter` and `TransformixImageFilter` as optional build-dependent APIs. They were absent from the inspected wheel, while the source tree contains wrappers and examples.

## Route Elsewhere

- For public image construction, spatial metadata, pixel types, and NumPy array conversion, route to [../image-core/SKILL.md](../image-core/SKILL.md).
- For file formats, ImageIO discovery, DICOM series, or transform IO, route to [../io-and-data/SKILL.md](../io-and-data/SKILL.md).
- For filters, segmentation, smoothing, thresholding, statistics, or N4 bias correction, route to [../filtering-segmentation/SKILL.md](../filtering-segmentation/SKILL.md).
- For registration, transforms, resampling, or using elastix/transformix after the wrappers exist, route to [../registration-transforms/SKILL.md](../registration-transforms/SKILL.md).

## Safety Guardrails

- Mark full source builds, SuperBuilds, `pip install .`, docs builds with dependency installation, and broad `ctest` runs as expensive or environment-mutating before running them.
- Use the bundled helper only for read-only inspection; it never configures CMake, installs packages, downloads dependencies, or edits generated files.
- Do not rely on source checkout paths at runtime. Copy or write any future helper needed by this skill under this subtree and link it from the nearest `SKILL.md`.
- Do not use source release automation or download-statistics scripts for ordinary install/build answers; those are release-heavy maintainer tasks outside this sub-skill.
